"""Stage 1 of the funnel: the exposure gate.

This is the cheapest important thing Atlas does. Before any model sees an item, a trie
match asks one question: **does this name something the owner is actually exposed to?**
An article about semiconductor export controls is world news to everyone and *information*
only to someone holding semiconductors, working in the sector, or living somewhere the
policy binds.

The gate is free, deterministic and offline. It is also the largest reduction in the
funnel after idempotency — see `docs/COST_MODEL.md` §2 — but cost is the smaller half of
the argument. The same filter that keeps the bill in cents is the one that keeps the daily
brief readable, so the cheap path and the good path are the same path. A system that had
unlimited money should still have this gate.

Two rules keep it honest:

* **Nothing is dropped silently.** Every rejected item leaves a :class:`TriageDecision`
  carrying the profile version it was judged against and what it failed to match. The
  Reading Room renders those reasons, and correcting one is how the owner teaches Atlas
  what it is exposed to. Seeing *why* 58 of 63 items were dropped builds more trust than
  reading them would.
* **The owner is never gated.** Something the owner submitted is relevant by construction.
  A gate that argues with its owner about what matters is a gate that gets turned off.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from atlas.ingestion.contracts import AdapterDescriptor, FetchedItem
from atlas.ingestion.idempotency import normalise_text
from atlas.scoring.relevance import DiscardReason

EXPOSURE_PROFILE_VERSION = "exposure-v1"

#: Words, plus the joiners that appear inside real identifiers: ``BRK.B``, ``S&P``,
#: ``e-commerce``, ``d'Ivoire``.
_TOKEN_PATTERN = re.compile(r"[^\W_]+(?:[.\-'&][^\W_]+)*", re.UNICODE)

_ZERO = Decimal(0)
_ONE = Decimal(1)


class ExposureKind(StrEnum):
    """What kind of stake the owner has. Carried through so the brief can say why."""

    INSTRUMENT = "instrument"
    CURRENCY = "currency"
    COUNTRY = "country"
    SECTOR = "sector"
    ENTITY = "entity"
    OBJECTIVE = "objective"
    OBLIGATION = "obligation"


class MatchMode(StrEnum):
    """How a phrase is compared against text.

    ``TEXT`` folds case. ``SYMBOL`` does not, because tickers collide catastrophically
    with ordinary words: ``IT``, ``ALL``, ``ON``, ``ARE`` and ``A`` are all real symbols.
    """

    TEXT = "text"
    SYMBOL = "symbol"


class TriageStage(StrEnum):
    """The funnel from `docs/COST_MODEL.md` §2. Stages 2-4 land with their queue items."""

    IDEMPOTENCY = "stage_0_idempotency"
    EXPOSURE = "stage_1_exposure"
    SIMILARITY = "stage_2_similarity"
    EXTRACTION = "stage_3_extraction"
    REASONING = "stage_4_reasoning"


class TriageOutcome(StrEnum):
    ADMITTED = "admitted"
    DROPPED = "dropped"


@dataclass(frozen=True, slots=True)
class ExposureTerm:
    """One thing the owner is exposed to, with every name it goes by."""

    key: str
    label: str
    kind: ExposureKind
    weight: Decimal = Decimal("0.5")
    aliases: tuple[str, ...] = ()
    match_mode: MatchMode = MatchMode.TEXT

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.label.strip():
            raise ValueError("an exposure term needs a key and a label")
        if not _ZERO < self.weight <= _ONE:
            raise ValueError("exposure weight must be greater than 0 and at most 1")
        for phrase in self.phrases:
            if not phrase.strip():
                raise ValueError(f"{self.key}: empty phrase")
            if self.match_mode is MatchMode.SYMBOL and phrase != phrase.upper():
                raise ValueError(
                    f"{self.key}: symbol phrases are matched case-sensitively and must "
                    f"be written as they appear, e.g. 'NVDA' not {phrase!r}"
                )

    @property
    def phrases(self) -> tuple[str, ...]:
        return (self.label, *self.aliases)

    def fingerprint(self) -> str:
        return "|".join(
            (self.key, self.kind, self.match_mode, str(self.weight), *sorted(self.phrases))
        )


@dataclass(frozen=True, slots=True)
class ExposureMatch:
    """A term found in an item, and where."""

    term_key: str
    kind: ExposureKind
    weight: Decimal
    matched_text: str
    position: int

    def __str__(self) -> str:
        return f"{self.matched_text} ({self.kind})"


@dataclass(slots=True)
class _TrieNode:
    children: dict[str, _TrieNode] = field(default_factory=dict)
    terminals: tuple[str, ...] = ()


def _tokenise(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text)


def _shouty(tokens: Sequence[str]) -> bool:
    """Whether the text is set in capitals, which makes symbol matching meaningless.

    ``US FED HOLDS RATES`` would otherwise match the ticker ``US``. Long all-caps runs
    are common in headlines and wire copy, so this is a real false-positive source rather
    than a hypothetical one.
    """
    alpha = [token for token in tokens if token.isalpha() and len(token) > 1]
    if len(alpha) < 5:
        return False
    upper = sum(1 for token in alpha if token.isupper())
    return upper * 5 >= len(alpha) * 3


class ExposureProfile:
    """The owner's exposure set, compiled once into a token trie and reused all cycle.

    The profile is deliberately a value: its :attr:`version` is a hash of its terms, so a
    decision can always be re-explained against the exact profile that produced it, and
    the identical serialised profile can be sent as a cached prompt prefix on every
    extraction call in a run (`docs/COST_MODEL.md` §5).

    Building the profile from holdings, objectives and residency is Queue 07's job. This
    module only matches against whatever it is given.
    """

    __slots__ = ("_symbol_root", "_terms", "_text_root", "_version")

    def __init__(self, terms: Iterable[ExposureTerm]) -> None:
        by_key: dict[str, ExposureTerm] = {}
        for term in terms:
            if term.key in by_key:
                raise ValueError(f"duplicate exposure term {term.key!r}")
            by_key[term.key] = term
        self._terms = tuple(sorted(by_key.values(), key=lambda term: term.key))
        self._text_root = _TrieNode()
        self._symbol_root = _TrieNode()
        for term in self._terms:
            root = self._symbol_root if term.match_mode is MatchMode.SYMBOL else self._text_root
            for phrase in term.phrases:
                tokens = _tokenise(phrase)
                if term.match_mode is MatchMode.TEXT:
                    tokens = [normalise_text(token) for token in tokens]
                if not tokens:
                    raise ValueError(f"{term.key}: phrase {phrase!r} contains no tokens")
                self._insert(root, tokens, term.key)
        self._version = self._compute_version()

    @staticmethod
    def _insert(root: _TrieNode, tokens: Sequence[str], term_key: str) -> None:
        node = root
        for token in tokens:
            node = node.children.setdefault(token, _TrieNode())
        if term_key not in node.terminals:
            node.terminals = (*node.terminals, term_key)

    def _compute_version(self) -> str:
        payload = "\n".join(term.fingerprint() for term in self._terms)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"{EXPOSURE_PROFILE_VERSION}:{digest}"

    @property
    def terms(self) -> tuple[ExposureTerm, ...]:
        return self._terms

    @property
    def version(self) -> str:
        return self._version

    @property
    def is_empty(self) -> bool:
        return not self._terms

    def term(self, key: str) -> ExposureTerm:
        for candidate in self._terms:
            if candidate.key == key:
                return candidate
        raise KeyError(key)

    def matches(self, *texts: str | None) -> tuple[ExposureMatch, ...]:
        """Every distinct exposure named anywhere in the given texts.

        One match per term — the first occurrence. Repetition is not evidence of
        anything: an article that says ``NVDA`` nine times is one article about NVDA.
        """
        joined = " . ".join(text for text in texts if text)
        raw_tokens = _tokenise(joined)
        if not raw_tokens:
            return ()
        folded = [normalise_text(token) for token in raw_tokens]
        symbols_meaningful = not _shouty(raw_tokens)

        found: dict[str, ExposureMatch] = {}
        for start in range(len(raw_tokens)):
            self._walk(self._text_root, folded, start, raw_tokens, found)
            if symbols_meaningful:
                self._walk(self._symbol_root, raw_tokens, start, raw_tokens, found)
        return tuple(sorted(found.values(), key=lambda match: (match.position, match.term_key)))

    def _walk(
        self,
        root: _TrieNode,
        haystack: Sequence[str],
        start: int,
        raw_tokens: Sequence[str],
        found: dict[str, ExposureMatch],
    ) -> None:
        node = root
        for offset in range(start, len(haystack)):
            child = node.children.get(haystack[offset])
            if child is None:
                return
            node = child
            for term_key in node.terminals:
                if term_key in found:
                    continue
                term = self.term(term_key)
                found[term_key] = ExposureMatch(
                    term_key=term_key,
                    kind=term.kind,
                    weight=term.weight,
                    matched_text=" ".join(raw_tokens[start : offset + 1]),
                    position=start,
                )


def exposure_score(matches: Sequence[ExposureMatch]) -> Decimal:
    """The strongest exposure the item touches.

    Not a sum. Summing would let a dozen incidental mentions outrank the one holding that
    is a third of the portfolio, which inverts exactly the judgement this gate exists to
    make. Breadth is still available to later stages as the match count.
    """
    return max((match.weight for match in matches), default=_ZERO)


@dataclass(frozen=True, slots=True)
class GatePolicy:
    """The only tuning surface. Deliberately small."""

    minimum_weight: Decimal = Decimal("0.20")
    admit_owner_authored: bool = True
    always_admit_sources: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not _ZERO <= self.minimum_weight <= _ONE:
            raise ValueError("minimum_weight must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class TriageDecision:
    """Why one item did or did not reach a model. User-facing text, not a log line."""

    item_ref: str
    outcome: TriageOutcome
    reached: TriageStage
    profile_version: str
    stopped_at: TriageStage | None = None
    reason: DiscardReason | None = None
    matches: tuple[ExposureMatch, ...] = ()
    score: Decimal = _ZERO
    detail: str = ""

    def __post_init__(self) -> None:
        if self.outcome is TriageOutcome.DROPPED and self.stopped_at is None:
            raise ValueError("a dropped item must record the stage that dropped it")
        if self.outcome is TriageOutcome.ADMITTED and self.reason is not None:
            raise ValueError("an admitted item has no discard reason")

    @property
    def admitted(self) -> bool:
        return self.outcome is TriageOutcome.ADMITTED

    @property
    def explanation(self) -> str:
        if self.admitted:
            if self.matches:
                named = ", ".join(str(match) for match in self.matches[:3])
                return f"relates to {named}"
            return self.detail or "admitted"
        if self.detail:
            return self.detail
        if self.reason is DiscardReason.NO_EXPOSURE:
            return "names nothing you are exposed to"
        return f"dropped at {self.stopped_at}"


class ExposureGate:
    """Stage 1. Free, offline, and answerable for every item it turns away."""

    def __init__(self, profile: ExposureProfile, policy: GatePolicy | None = None) -> None:
        self._profile = profile
        self._policy = policy or GatePolicy()

    @property
    def profile(self) -> ExposureProfile:
        return self._profile

    def evaluate(
        self,
        item: FetchedItem,
        descriptor: AdapterDescriptor,
        *,
        item_ref: str,
        extra_text: Sequence[str] = (),
    ) -> TriageDecision:
        """Decide whether an item may proceed to extraction."""
        if descriptor.owner_authored and self._policy.admit_owner_authored:
            return self._admit(item_ref, (), _ONE, "you submitted this")
        if descriptor.name in self._policy.always_admit_sources:
            return self._admit(item_ref, (), _ONE, f"{descriptor.name} is always read")
        if self._profile.is_empty:
            # An empty profile means Atlas does not yet know the owner. Gating on it
            # would silently discard everything and look like a quiet world.
            return self._admit(item_ref, (), _ZERO, "no exposure profile configured yet")

        matches = self._profile.matches(item.title, item.body, *extra_text)
        score = exposure_score(matches)
        if not matches:
            return self._drop(item_ref, DiscardReason.NO_EXPOSURE, (), _ZERO)
        if score < self._policy.minimum_weight:
            named = ", ".join(str(match) for match in matches[:3])
            return self._drop(
                item_ref,
                DiscardReason.IMMATERIAL,
                matches,
                score,
                detail=f"only marginal exposure ({named})",
            )
        return TriageDecision(
            item_ref=item_ref,
            outcome=TriageOutcome.ADMITTED,
            reached=TriageStage.EXTRACTION,
            profile_version=self._profile.version,
            matches=matches,
            score=score,
        )

    def _admit(
        self, item_ref: str, matches: tuple[ExposureMatch, ...], score: Decimal, detail: str
    ) -> TriageDecision:
        return TriageDecision(
            item_ref=item_ref,
            outcome=TriageOutcome.ADMITTED,
            reached=TriageStage.EXTRACTION,
            profile_version=self._profile.version,
            matches=matches,
            score=score,
            detail=detail,
        )

    def _drop(
        self,
        item_ref: str,
        reason: DiscardReason,
        matches: tuple[ExposureMatch, ...],
        score: Decimal,
        *,
        detail: str = "",
    ) -> TriageDecision:
        return TriageDecision(
            item_ref=item_ref,
            outcome=TriageOutcome.DROPPED,
            reached=TriageStage.EXPOSURE,
            stopped_at=TriageStage.EXPOSURE,
            profile_version=self._profile.version,
            reason=reason,
            matches=matches,
            score=score,
            detail=detail,
        )
