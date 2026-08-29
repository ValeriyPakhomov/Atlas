"""Stage 0 of the funnel: deterministic identity (ADR-0007).

Three layers decide whether an item is new, and none of them involves a model:

1. exact ``(source, external_id)``;
2. canonical URL;
3. normalised content hash.

Every layer is a pure function of the item plus a **version string that is stored with
the result**. That is the whole point of ADR-0007: when the canonicalisation rules change,
old rows keep the version that produced them, so a replay of March reconstructs March's
graph rather than today's opinion of it. Semantic similarity may later *propose* a merge;
it never participates here.

Two scoping decisions are load-bearing and easy to get wrong:

* **External ids are scoped to their source.** Provider ids are only meaningful inside the
  provider's namespace; two feeds both numbering their items ``1`` are not the same item.
* **URL and content hash are global.** The same article reached through two aggregators is
  one artifact, and the identical wire copy run by six outlets is one artifact six times.
  Treating that as six independent reports would let syndication masquerade as
  corroboration and inflate the credibility of a single claim — the failure mode this
  layer exists to prevent. Corroboration means two *different* artifacts.

A dropped duplicate is still answerable: the verdict names the layer that matched and the
item it matched, so the Reading Room can show "already seen, via Reuters, 40 minutes ago"
rather than simply not showing anything.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from atlas.ingestion.contracts import AdapterDescriptor, FetchedItem

URL_CANONICALISATION_VERSION = "url-canon-v1"
TEXT_NORMALISATION_VERSION = "text-norm-v1"
HASH_VERSION = "sha256-v1"

_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
_HOST_PATTERN = re.compile(r"^[^\s@:/?#]+$")
_DEFAULT_PORTS = {"http": "80", "https": "443"}
_ALLOWED_SCHEMES = frozenset({"http", "https"})

#: Parameters that identify a *referral*, never the artifact. Dropping them is what makes
#: the same story shared by mail, by a newsletter and by a feed reader collapse into one.
_TRACKING_PARAMS = frozenset(
    {
        "cmpid",
        "ext",
        "fbclid",
        "gclid",
        "igshid",
        "mc_cid",
        "mc_eid",
        "msclkid",
        "ref",
        "referrer",
        "s_kwcid",
        "spm",
        "twclid",
        "vero_id",
        "yclid",
    }
)
_TRACKING_PREFIXES = ("utm_", "at_", "__cf", "_hs", "pk_")

_PUNCTUATION_MAP = {
    # Typographic variants that carry no meaning of their own.
    0x2018: "'",  # left single quotation mark
    0x2019: "'",  # right single quotation mark
    0x201A: "'",  # single low-9 quotation mark
    0x201C: '"',  # left double quotation mark
    0x201D: '"',  # right double quotation mark
    0x2013: "-",  # en dash
    0x2014: "-",  # em dash
    0x2212: "-",  # minus sign
    0x00A0: " ",  # no-break space
    # Invisible characters, which some publishers inject into every paragraph.
    0x200B: None,  # zero-width space
    0x200C: None,  # zero-width non-joiner
    0x200D: None,  # zero-width joiner
    0xFEFF: None,  # byte-order mark
}

_FIELD_SEPARATOR = "\x1f"


def _is_tracking(key: str) -> bool:
    lowered = key.lower()
    return lowered in _TRACKING_PARAMS or lowered.startswith(_TRACKING_PREFIXES)


def canonical_url(raw: str | None) -> str | None:
    """Reduce a URL to the artifact it points at, or ``None`` if it points at nothing.

    Deliberately conservative. Every rule here is one that cannot change *which document*
    is addressed: case in the scheme and host, a default port, a ``www.`` prefix, referral
    parameters, a fragment, a trailing slash. Rules that merely usually work — stripping
    ``/amp``, dropping pagination, following redirects — are not applied, because a
    wrong merge silently deletes a real item and no later stage can recover it.
    """
    if raw is None:
        return None
    candidate = raw.strip()
    if not candidate:
        return None
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    elif _SCHEME_PATTERN.match(candidate) is None:
        # A bare ``example.com/x`` is a URL a human wrote; ``mailto:`` is not a document.
        candidate = f"https://{candidate}"

    parts = urlsplit(candidate)
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES or not parts.hostname:
        return None

    host = parts.hostname.lower().rstrip(".")
    labels = host.split(".")
    if (
        _HOST_PATTERN.match(host) is None
        or not all(labels)
        or (len(labels) == 1 and host != "localhost")
    ):
        # Free text that happens to be in a URL field is not a URL. Better no URL key
        # than a fabricated one that could collide with a real address.
        return None
    if host.startswith("www.") and host.count(".") > 1:
        host = host[4:]
    netloc = host
    port = parts.port
    if port is not None and str(port) != _DEFAULT_PORTS.get(scheme):
        netloc = f"{host}:{port}"

    path = parts.path or "/"
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1:
        path = path.rstrip("/") or "/"

    kept = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking(key)
    )
    return urlunsplit((scheme, netloc, path, urlencode(kept), ""))


def normalise_text(value: str | None) -> str:
    """Fold away everything that is presentation rather than content."""
    if not value:
        return ""
    folded = unicodedata.normalize("NFKC", value).translate(_PUNCTUATION_MAP)
    return " ".join(folded.split()).casefold()


def content_hash(*parts: str | None) -> str | None:
    """Hash the normalised content, or return ``None`` when there is no content.

    An item with no text is not "the empty item" — it has no content identity at all, and
    hashing emptiness would collapse every such item into one. Better to fall back to the
    other two layers than to invent a match.
    """
    normalised = [normalise_text(part) for part in parts]
    if not any(normalised):
        return None
    digest = hashlib.sha256(_FIELD_SEPARATOR.join(normalised).encode("utf-8")).hexdigest()
    return f"{HASH_VERSION}:{digest}"


class DedupeLayer(StrEnum):
    """Ordered cheapest-first; the first layer that matches decides."""

    EXTERNAL_ID = "external_id"
    CANONICAL_URL = "canonical_url"
    CONTENT_HASH = "content_hash"


class DedupeStatus(StrEnum):
    NEW = "new"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class ItemIdentity:
    """An item's deterministic identity, with the versions that computed it."""

    source_name: str
    external_key: str | None
    url_key: str | None
    content_key: str | None
    parse_version: str
    canonicalisation_version: str = URL_CANONICALISATION_VERSION
    normalisation_version: str = TEXT_NORMALISATION_VERSION
    hash_version: str = HASH_VERSION

    def __post_init__(self) -> None:
        if not self.layers():
            raise ValueError(
                "an item with no external id, no resolvable URL and no content has no "
                "identity and cannot be deduplicated"
            )

    def layers(self) -> tuple[tuple[DedupeLayer, str], ...]:
        pairs = (
            (DedupeLayer.EXTERNAL_ID, self.external_key),
            (DedupeLayer.CANONICAL_URL, self.url_key),
            (DedupeLayer.CONTENT_HASH, self.content_key),
        )
        return tuple((layer, key) for layer, key in pairs if key is not None)

    @property
    def primary_key(self) -> str:
        return self.layers()[0][1]

    @property
    def storage_hash(self) -> str:
        """The hash persisted on the ``RawItem`` row.

        Normally the content hash. When an item has no text at all — a price tick, a
        filing stub — it is a digest of the identity instead, prefixed so that it can
        never be mistaken for a hash of content that was never there.
        """
        if self.content_key is not None:
            return self.content_key
        digest = hashlib.sha256(self.primary_key.encode("utf-8")).hexdigest()
        return f"ident-v1:{digest}"


def identify(item: FetchedItem, descriptor: AdapterDescriptor) -> ItemIdentity:
    """Compute an item's identity. Pure, offline, and stable across runs."""
    external_id = (item.external_id or "").strip()
    url = canonical_url(item.url)
    return ItemIdentity(
        source_name=descriptor.name,
        external_key=f"ext:{descriptor.name}:{external_id}" if external_id else None,
        url_key=f"url:{url}" if url else None,
        content_key=content_hash(item.title, item.body),
        parse_version=descriptor.parse_version,
    )


@dataclass(frozen=True, slots=True)
class DedupeVerdict:
    """New, or a duplicate that can say exactly what it duplicates and why."""

    status: DedupeStatus
    layer: DedupeLayer | None = None
    matched_key: str | None = None
    matched_ref: str | None = None

    @property
    def is_new(self) -> bool:
        return self.status is DedupeStatus.NEW

    @property
    def explanation(self) -> str:
        if self.is_new:
            return "not seen before"
        match self.layer:
            case DedupeLayer.EXTERNAL_ID:
                return f"already ingested as {self.matched_ref} (same source id)"
            case DedupeLayer.CANONICAL_URL:
                return f"already ingested as {self.matched_ref} (same URL)"
            case _:
                return f"already ingested as {self.matched_ref} (identical text)"


class SeenLedger(Protocol):
    """Where identity keys are remembered.

    A Protocol so that the in-memory ledger used by tests and replay and the
    PostgreSQL-backed one used in production are the same contract. Persistence lands
    with Queue 03; nothing here knows about a database.
    """

    def lookup(self, key: str) -> str | None: ...

    def record(self, key: str, ref: str) -> None: ...


@dataclass(slots=True)
class InMemoryLedger:
    """First writer wins, so re-recording never rewrites an item's original reference."""

    seen: dict[str, str] = field(default_factory=dict)

    def lookup(self, key: str) -> str | None:
        return self.seen.get(key)

    def record(self, key: str, ref: str) -> None:
        self.seen.setdefault(key, ref)

    def bulk_record(self, entries: Iterable[tuple[str, str]]) -> None:
        for key, ref in entries:
            self.record(key, ref)


class Deduplicator:
    """Stage 0. Free, deterministic, and the largest single reduction in the funnel."""

    def __init__(self, ledger: SeenLedger) -> None:
        self._ledger = ledger

    def classify(self, identity: ItemIdentity) -> DedupeVerdict:
        for layer, key in identity.layers():
            existing = self._ledger.lookup(key)
            if existing is not None:
                return DedupeVerdict(
                    status=DedupeStatus.DUPLICATE,
                    layer=layer,
                    matched_key=key,
                    matched_ref=existing,
                )
        return DedupeVerdict(status=DedupeStatus.NEW)

    def admit(self, identity: ItemIdentity, ref: str) -> None:
        """Remember an accepted item under every layer it can be recognised by."""
        for _, key in identity.layers():
            self._ledger.record(key, ref)

    def register(self, identity: ItemIdentity, ref: str) -> DedupeVerdict:
        """Classify and, when new, admit — the operation ingestion actually performs."""
        verdict = self.classify(identity)
        if verdict.is_new:
            self.admit(identity, ref)
        return verdict
