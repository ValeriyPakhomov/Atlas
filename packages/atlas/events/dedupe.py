"""Event-level deduplication: a deterministic spine and an advisory layer (ADR-0007).

Two candidates with the same exact key are the same event, always, with no judgement
involved. Everything looser — an entity set that overlaps but does not match, an
occurrence that straddles midnight, a wording that reads like the same story — produces an
:class:`EventMergeProposal`, never a silent merge.

The property this buys is the one that matters for a system meant to be trusted over
years: **replay reads stored decisions rather than recomputing them.** Every evaluated
pair leaves a decision behind, so when the similarity method changes — a better rule, a
different embedding model, the local-model migration in `PROGRAM.md` §8 — history keeps
its shape. The new method only affects pairs judged after the change. Without that,
upgrading an embedding model would silently rewrite what happened last March, and no
audit of a past decision would mean anything.

A rejected pair is remembered too, so the same near-miss is not re-proposed every night.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from atlas.domain.clock import Clock
from atlas.domain.entities import Event
from atlas.events.normalization import EventCandidate, build_event
from atlas.events.scoring import DEFAULT_SCORING, EventScoringPolicy

_ZERO = Decimal(0)
_ONE = Decimal(1)


class MergeMethod(StrEnum):
    EXACT_KEY = "exact_key"
    ENTITY_TIME_TOPIC = "entity_time_topic"
    SEMANTIC_SIMILARITY = "semantic_similarity"


class MergeDecision(StrEnum):
    AUTO_ACCEPTED = "auto_accepted"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DecidedBy(StrEnum):
    SYSTEM = "system"
    OWNER = "owner"


class MergeOutcome(StrEnum):
    CREATED = "created"
    MERGED_EXACT = "merged_exact"
    MERGED_BY_PROPOSAL = "merged_by_proposal"
    CREATED_WITH_PROPOSAL = "created_with_proposal"


PairKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class EventMergeProposal:
    """A suggested merge, with everything needed to re-explain it years later."""

    source_key: str
    target_key: str
    method: MergeMethod
    score: Decimal
    threshold_applied: Decimal
    decision: MergeDecision
    decided_at: datetime
    decided_by: DecidedBy = DecidedBy.SYSTEM
    model_name: str | None = None
    model_version: str | None = None
    embedding_dim: int | None = None
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")
        if self.source_key == self.target_key:
            raise ValueError("a proposal must relate two different events")
        rule_based = self.method is not MergeMethod.SEMANTIC_SIMILARITY
        if rule_based and any((self.model_name, self.model_version, self.embedding_dim)):
            raise ValueError("a rule-based proposal has no model to record")
        if not rule_based and not (self.model_name and self.model_version):
            raise ValueError(
                "a similarity proposal must record the model that produced it, or a later "
                "model change cannot be told apart from a change of fact"
            )

    @property
    def pair(self) -> PairKey:
        return (self.source_key, self.target_key)


@dataclass(frozen=True, slots=True)
class MergePolicy:
    """Thresholds, versioned so a past decision stays explicable."""

    auto_accept: Decimal = Decimal("0.85")
    propose_floor: Decimal = Decimal("0.60")
    window: timedelta = timedelta(hours=36)
    entity_weight: Decimal = Decimal("0.7")
    time_weight: Decimal = Decimal("0.3")
    version: str = "merge-rules-v1"

    def __post_init__(self) -> None:
        if not _ZERO < self.propose_floor <= self.auto_accept <= _ONE:
            raise ValueError("thresholds must satisfy 0 < propose_floor <= auto_accept <= 1")
        if self.entity_weight + self.time_weight != _ONE:
            raise ValueError("entity and time weights must sum to 1")
        if self.window <= timedelta(0):
            raise ValueError("the comparison window must be positive")


DEFAULT_MERGE_POLICY = MergePolicy()


@dataclass(frozen=True, slots=True)
class EventRecord:
    """An event and every account Atlas holds of it."""

    dedupe_key: str
    event: Event
    candidates: tuple[EventCandidate, ...]
    merged_keys: tuple[str, ...] = ()

    @property
    def keys(self) -> tuple[str, ...]:
        return (self.dedupe_key, *self.merged_keys)


@dataclass(frozen=True, slots=True)
class MergeResult:
    """What happened to one candidate, and why."""

    outcome: MergeOutcome
    record: EventRecord
    proposal: EventMergeProposal | None = None
    score: Decimal = _ZERO

    @property
    def merged(self) -> bool:
        return self.outcome in {MergeOutcome.MERGED_EXACT, MergeOutcome.MERGED_BY_PROPOSAL}

    @property
    def explanation(self) -> str:
        match self.outcome:
            case MergeOutcome.MERGED_EXACT:
                return f"same event as {self.record.event.canonical_title!r}"
            case MergeOutcome.MERGED_BY_PROPOSAL:
                return f"merged into {self.record.event.canonical_title!r} on a {self.score} match"
            case MergeOutcome.CREATED_WITH_PROPOSAL:
                return f"new event; possible duplicate flagged at {self.score}"
            case _:
                return "new event"


def jaccard(left: Sequence[str], right: Sequence[str]) -> Decimal:
    """Overlap of two term sets, 0..1."""
    a, b = set(left), set(right)
    if not a and not b:
        return _ZERO
    union = a | b
    return (Decimal(len(a & b)) / Decimal(len(union))).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
    )


def entity_time_topic_score(
    candidate: EventCandidate, record: EventRecord, policy: MergePolicy
) -> Decimal:
    """Blueprint layer 5, as a rule rather than a model.

    Event type is a hard gate, not a weighted term: a rate decision and a resignation
    involving the same actor on the same day are two events, and no amount of entity
    overlap should merge them.
    """
    reference = record.candidates[0]
    if candidate.event_type != reference.event_type:
        return _ZERO
    gap = abs(candidate.occurred_at - reference.occurred_at)
    if gap > policy.window:
        return _ZERO
    proximity = _ONE - (Decimal(gap / policy.window))
    overlap = jaccard(candidate.primary_entities, reference.primary_entities)
    score = policy.entity_weight * overlap + policy.time_weight * proximity
    return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)


Scorer = Callable[[EventCandidate, EventRecord, MergePolicy], Decimal]


@dataclass(slots=True)
class DecisionLog:
    """Every pair Atlas has judged, and what it concluded.

    The authority for replay. Proposals are the *reviewable* subset — pairs close enough
    to be worth a human glance — while pairs scored below the floor are recorded here as
    rejected without generating a row to review. Only pairs inside the comparison window
    are ever evaluated, which is what bounds this.
    """

    decisions: dict[PairKey, MergeDecision] = field(default_factory=dict)

    def get(self, source_key: str, target_key: str) -> MergeDecision | None:
        return self.decisions.get((source_key, target_key))

    def record(self, source_key: str, target_key: str, decision: MergeDecision) -> None:
        self.decisions[(source_key, target_key)] = decision

    def override(self, source_key: str, target_key: str, decision: MergeDecision) -> None:
        """The owner correcting Atlas. Overrides never erase evidence, only the merge."""
        self.decisions[(source_key, target_key)] = decision

    def snapshot(self) -> dict[PairKey, MergeDecision]:
        return dict(self.decisions)


class EventGraph:
    """Candidates in, canonical events out.

    Order-independent by construction: every merge rebuilds its event from the full
    candidate set rather than patching fields, so the same accounts always produce the same
    event whatever sequence they arrive in.
    """

    __slots__ = (
        "_by_key",
        "_clock",
        "_log",
        "_policy",
        "_proposals",
        "_records",
        "_scorer",
        "_scoring",
    )

    def __init__(
        self,
        *,
        clock: Clock,
        policy: MergePolicy = DEFAULT_MERGE_POLICY,
        scoring: EventScoringPolicy = DEFAULT_SCORING,
        decisions: Mapping[PairKey, MergeDecision] | None = None,
        scorer: Scorer = entity_time_topic_score,
    ) -> None:
        self._clock = clock
        self._policy = policy
        self._scoring = scoring
        self._scorer = scorer
        self._log = DecisionLog(dict(decisions or {}))
        self._records: dict[str, EventRecord] = {}
        self._by_key: dict[str, str] = {}
        self._proposals: list[EventMergeProposal] = []

    # ── reading ─────────────────────────────────────────────────────────────
    @property
    def records(self) -> tuple[EventRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda record: record.dedupe_key))

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(record.event for record in self.records)

    @property
    def proposals(self) -> tuple[EventMergeProposal, ...]:
        return tuple(self._proposals)

    @property
    def decisions(self) -> dict[PairKey, MergeDecision]:
        return self._log.snapshot()

    def record_for(self, key: str) -> EventRecord | None:
        canonical = self._by_key.get(key)
        return self._records.get(canonical) if canonical else None

    # ── writing ─────────────────────────────────────────────────────────────
    def absorb(self, candidate: EventCandidate, *, as_of: datetime | None = None) -> MergeResult:
        """Fold one account into the graph."""
        now = as_of or self._clock.now()
        key = candidate.dedupe_key

        existing = self.record_for(key)
        if existing is not None:
            return MergeResult(
                outcome=MergeOutcome.MERGED_EXACT,
                record=self._attach(existing, candidate, as_of=now),
                score=_ONE,
            )

        target, score, decision = self._best_target(candidate, now)
        if target is not None and decision in {MergeDecision.AUTO_ACCEPTED, MergeDecision.ACCEPTED}:
            proposal = self._propose(key, target, score, decision, now)
            merged = self._attach(target, candidate, as_of=now)
            return MergeResult(
                outcome=MergeOutcome.MERGED_BY_PROPOSAL,
                record=merged,
                proposal=proposal,
                score=score,
            )

        created = self._create(candidate, as_of=now)
        if target is not None and decision is MergeDecision.PENDING:
            proposal = self._propose(key, target, score, MergeDecision.PENDING, now)
            return MergeResult(
                outcome=MergeOutcome.CREATED_WITH_PROPOSAL,
                record=created,
                proposal=proposal,
                score=score,
            )
        return MergeResult(outcome=MergeOutcome.CREATED, record=created, score=score)

    def absorb_all(self, candidates: Iterable[EventCandidate]) -> tuple[MergeResult, ...]:
        return tuple(self.absorb(candidate) for candidate in candidates)

    # ── internals ───────────────────────────────────────────────────────────
    def _best_target(
        self, candidate: EventCandidate, now: datetime
    ) -> tuple[EventRecord | None, Decimal, MergeDecision | None]:
        """Pick the best merge target, reading stored decisions before scoring anything."""
        best: EventRecord | None = None
        best_score = _ZERO
        best_decision: MergeDecision | None = None
        key = candidate.dedupe_key

        for record in self.records:
            stored = self._log.get(key, record.dedupe_key)
            if stored is MergeDecision.REJECTED:
                continue
            standing = {
                MergeDecision.AUTO_ACCEPTED,
                MergeDecision.ACCEPTED,
                MergeDecision.PENDING,
            }
            if stored in standing:
                # Replay path: the decision stands, whatever today's scorer would say.
                return record, _ONE, stored

            score = self._scorer(candidate, record, self._policy)
            if score < self._policy.propose_floor:
                self._log.record(key, record.dedupe_key, MergeDecision.REJECTED)
                continue
            if score > best_score:
                best, best_score = record, score
                best_decision = (
                    MergeDecision.AUTO_ACCEPTED
                    if score >= self._policy.auto_accept
                    else MergeDecision.PENDING
                )
        return best, best_score, best_decision

    def _propose(
        self,
        source_key: str,
        target: EventRecord,
        score: Decimal,
        decision: MergeDecision,
        now: datetime,
    ) -> EventMergeProposal:
        proposal = EventMergeProposal(
            source_key=source_key,
            target_key=target.dedupe_key,
            method=MergeMethod.ENTITY_TIME_TOPIC,
            score=score,
            threshold_applied=self._policy.auto_accept,
            decision=decision,
            decided_at=now,
            rationale=f"{self._policy.version}: entity and time match against "
            f"{target.event.canonical_title!r}",
        )
        self._log.record(source_key, target.dedupe_key, decision)
        self._proposals.append(proposal)
        return proposal

    def _create(self, candidate: EventCandidate, *, as_of: datetime) -> EventRecord:
        key = candidate.dedupe_key
        record = EventRecord(
            dedupe_key=key,
            event=build_event([candidate], dedupe_key=key, as_of=as_of, policy=self._scoring),
            candidates=(candidate,),
        )
        self._records[key] = record
        self._by_key[key] = key
        return record

    def _attach(
        self, record: EventRecord, candidate: EventCandidate, *, as_of: datetime
    ) -> EventRecord:
        """Rebuild the event from every account, including the new one.

        Candidates are keyed by evidence id, so re-absorbing the same account changes
        nothing — re-ingestion must not inflate corroboration (A08).

        When a merge brings together accounts with different keys, the surviving key is
        the most authoritative account's, not whichever arrived first. Without that rule
        the same reports in a different order would produce a differently-identified
        event, and a replay would not reproduce the graph it is replaying.
        """
        by_evidence = {existing.report.evidence_id: existing for existing in record.candidates}
        by_evidence[candidate.report.evidence_id] = candidate
        candidates = tuple(
            sorted(by_evidence.values(), key=lambda item: (item.report.reported_at, item.title))
        )
        canonical = min(candidates, key=lambda item: item.authority).dedupe_key
        aliases = {record.dedupe_key, *record.merged_keys, candidate.dedupe_key} - {canonical}

        updated = EventRecord(
            dedupe_key=canonical,
            event=build_event(candidates, dedupe_key=canonical, as_of=as_of, policy=self._scoring),
            candidates=candidates,
            merged_keys=tuple(sorted(aliases)),
        )
        if canonical != record.dedupe_key:
            self._records.pop(record.dedupe_key, None)
        self._records[canonical] = updated
        for key in updated.keys:
            self._by_key[key] = canonical
        return updated
