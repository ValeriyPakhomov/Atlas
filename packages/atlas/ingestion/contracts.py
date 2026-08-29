"""The Source adapter contract (Queue 02).

An adapter has exactly one job: **turn a provider into raw, uninterpreted items**. It
does not score, summarise, deduplicate, classify or decide. Everything it returns is an
Artifact in the blueprint's sense — the thing that was actually published — and the
interpretation layers downstream are forbidden from reaching back through it.

Three constitutional rules are encoded here as types rather than left to discipline:

* **A09 — read-only.** ``AdapterDescriptor.write_capable`` is ``Literal[False]``. There is
  no value an adapter author can assign that would let one act on the world.
* **A02 — time is first-class.** An adapter never reads the wall clock. Both the fetch
  window and every ``observed_at`` come from an injected :class:`~atlas.domain.clock.Clock`,
  so a live cycle and a replay of 2026-03-11 differ only in which clock and provider stub
  are passed in.
* **A06 — partial is not zero.** A fetch that returned some of the window says so
  (:class:`~atlas.domain.measurement.Completeness`) and names the gap. A source that was
  down does not quietly look like a quiet day.

The last rule is why :func:`collect` distinguishes two kinds of failure. A typed
:class:`AdapterError` is *data missing* — the batch degrades, the cycle continues, the gap
travels downstream and is rendered. Any other exception is *a bug in Atlas* and is allowed
to escape: swallowing it would convert a defect into a silent hole in the record.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Literal, Protocol, runtime_checkable

from atlas.domain.clock import Clock
from atlas.domain.measurement import Completeness, MissingInput, MissingReason
from atlas.domain.sensitivity import SensitivityTier
from atlas.scoring.relevance import SourceClass

CURSOR_VERSION = "cursor-v1"


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def _require_non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


# ── typed failures ──────────────────────────────────────────────────────────────


class AdapterFailure(StrEnum):
    """Why a source did not deliver. Recorded on the run, never discarded."""

    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION = "authentication"
    NOT_PERMITTED = "not_permitted"
    CONTRACT_VIOLATION = "contract_violation"
    MALFORMED_PAYLOAD = "malformed_payload"


class AdapterError(RuntimeError):
    """Base class for every failure an adapter is allowed to report.

    Anything an adapter raises that is *not* one of these is treated as an Atlas defect
    and propagates. That boundary is deliberate: a provider outage and a broken parser
    must not look the same in the record.
    """

    failure: AdapterFailure = AdapterFailure.UNAVAILABLE
    retryable: bool = True

    def __init__(
        self,
        source_name: str,
        detail: str,
        *,
        retry_after: timedelta | None = None,
    ) -> None:
        super().__init__(f"{source_name}: {detail}")
        self.source_name = source_name
        self.detail = detail
        self.retry_after = retry_after

    def as_gap(self) -> MissingInput:
        """Render the failure as the gap it creates in the day's observation."""
        return MissingInput(
            subject=self.source_name,
            reason=MissingReason.MISSING,
            detail=f"{self.failure}: {self.detail}",
        )


class SourceUnavailable(AdapterError):
    """The provider could not be reached, or answered with a server-side error."""


class SourceTimeout(AdapterError):
    failure = AdapterFailure.TIMEOUT


class SourceRateLimited(AdapterError):
    failure = AdapterFailure.RATE_LIMITED


class SourceAuthenticationError(AdapterError):
    """Credentials are missing, expired or rejected. Retrying will not help."""

    failure = AdapterFailure.AUTHENTICATION
    retryable = False


class SourceNotPermitted(AdapterError):
    """The provider's terms or Atlas's own policy forbid this fetch."""

    failure = AdapterFailure.NOT_PERMITTED
    retryable = False


class SourceContractViolation(AdapterError):
    """The provider answered, but broke the shape the adapter is written against.

    Not retryable: the same request will break the same way until someone reads it.
    """

    failure = AdapterFailure.CONTRACT_VIOLATION
    retryable = False


class MalformedItem(AdapterError):
    """A single item could not be parsed into a :class:`FetchedItem`."""

    failure = AdapterFailure.MALFORMED_PAYLOAD
    retryable = False


class CursorRegression(RuntimeError):
    """A cursor was asked to move backwards.

    This is not a data problem, it is a correctness problem: a rewinding high-water mark
    silently re-reads a window Atlas has already accounted for, or skips one it has not.
    """


# ── cursors and windows ─────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class SourceCursor:
    """Where a source was read up to. Opaque to Atlas, monotonic by construction."""

    source_name: str
    position: str | None = None
    high_water_mark: datetime | None = None
    fetched_through: datetime | None = None
    version: str = CURSOR_VERSION

    def __post_init__(self) -> None:
        _require_non_empty(self.source_name, "source_name")
        for name in ("high_water_mark", "fetched_through"):
            instant: datetime | None = getattr(self, name)
            if instant is not None:
                _require_aware(instant, name)

    def advanced_to(
        self,
        *,
        position: str | None = None,
        high_water_mark: datetime | None = None,
        fetched_through: datetime | None = None,
    ) -> SourceCursor:
        """Return the next cursor, refusing to move either clock backwards."""
        for name, current, proposed in (
            ("high_water_mark", self.high_water_mark, high_water_mark),
            ("fetched_through", self.fetched_through, fetched_through),
        ):
            if proposed is not None:
                _require_aware(proposed, name)
                if current is not None and proposed < current:
                    raise CursorRegression(
                        f"{self.source_name}: {name} would move backwards "
                        f"from {current.isoformat()} to {proposed.isoformat()}"
                    )
        return SourceCursor(
            source_name=self.source_name,
            position=position if position is not None else self.position,
            high_water_mark=high_water_mark or self.high_water_mark,
            fetched_through=fetched_through or self.fetched_through,
            version=self.version,
        )


@dataclass(frozen=True, slots=True)
class FetchWindow:
    """The slice of time a fetch is responsible for.

    ``until`` is always supplied by the caller's clock, never by ``now()`` inside the
    adapter, which is what makes a replay of a past window reproducible.
    """

    until: datetime
    since: datetime | None = None
    max_items: int = 200

    def __post_init__(self) -> None:
        _require_aware(self.until, "until")
        if self.since is not None:
            _require_aware(self.since, "since")
            if self.since >= self.until:
                raise ValueError("fetch window 'since' must precede 'until'")
        if self.max_items <= 0:
            raise ValueError("max_items must be positive")

    def covers(self, instant: datetime | None) -> bool:
        """Whether an item timestamped ``instant`` belongs in this window.

        An item with no timestamp is included: withholding it would be a silent drop,
        and the deterministic dedupe layers handle it correctly anyway.
        """
        if instant is None:
            return True
        if instant > self.until:
            return False
        return self.since is None or instant >= self.since

    @classmethod
    def ending_now(
        cls, clock: Clock, *, lookback: timedelta | None = None, max_items: int = 200
    ) -> FetchWindow:
        now = clock.now()
        return cls(until=now, since=now - lookback if lookback else None, max_items=max_items)


# ── what an adapter returns ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class FetchedItem:
    """One artifact, exactly as the provider published it.

    ``payload`` keeps the provider's own representation verbatim so that a later parser
    version can re-derive fields without re-fetching — the raw artifact survives every
    change to its interpretation.
    """

    observed_at: datetime
    external_id: str | None = None
    url: str | None = None
    title: str | None = None
    body: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    declared_tier: SensitivityTier = SensitivityTier.L3

    def __post_init__(self) -> None:
        _require_aware(self.observed_at, "observed_at")
        if self.published_at is not None:
            _require_aware(self.published_at, "published_at")
        if not self.has_identity:
            raise ValueError(
                "a fetched item needs at least one of external_id, url, title or body; "
                "an item with no identifying content cannot be deduplicated"
            )

    @property
    def has_identity(self) -> bool:
        return any(
            (value or "").strip() for value in (self.external_id, self.url, self.title, self.body)
        )

    @property
    def effective_at(self) -> datetime:
        """Publication time when the provider gave one, otherwise the observation."""
        return self.published_at or self.observed_at


@dataclass(frozen=True, slots=True)
class FetchBatch:
    """The result of one fetch, including what it failed to see.

    The completeness invariants mirror :class:`~atlas.domain.measurement.Measured`
    deliberately: a batch is a measurement of a source over a window, and it obeys the
    same rule — an incomplete result must say what is missing, and an unavailable one
    carries no items rather than an empty list that reads as "nothing happened".
    """

    source_name: str
    fetched_at: datetime
    window: FetchWindow
    cursor: SourceCursor
    items: tuple[FetchedItem, ...] = ()
    completeness: Completeness = Completeness.COMPLETE
    gaps: tuple[MissingInput, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.source_name, "source_name")
        _require_aware(self.fetched_at, "fetched_at")
        if self.completeness is Completeness.COMPLETE and self.gaps:
            raise ValueError("a complete fetch cannot name gaps")
        if self.completeness is not Completeness.COMPLETE and not self.gaps:
            raise ValueError("an incomplete fetch must say what it missed")
        if self.completeness is Completeness.UNAVAILABLE and self.items:
            raise ValueError("an unavailable fetch cannot carry items")
        if self.cursor.source_name != self.source_name:
            raise ValueError("cursor belongs to a different source")

    @property
    def observed_everything(self) -> bool:
        return self.completeness is Completeness.COMPLETE

    @classmethod
    def unavailable(
        cls,
        *,
        source_name: str,
        fetched_at: datetime,
        window: FetchWindow,
        cursor: SourceCursor,
        gaps: tuple[MissingInput, ...],
    ) -> FetchBatch:
        return cls(
            source_name=source_name,
            fetched_at=fetched_at,
            window=window,
            cursor=cursor,
            items=(),
            completeness=Completeness.UNAVAILABLE,
            gaps=gaps,
        )


# ── the adapter itself ──────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """Everything Atlas needs to know about a source without invoking it."""

    name: str
    source_type: str
    source_class: SourceClass
    parse_version: str = "1"
    default_tier: SensitivityTier = SensitivityTier.L1
    supports_incremental: bool = True
    requires_network: bool = True
    owner_authored: bool = False
    terms_notes: str | None = None
    write_capable: Literal[False] = False

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.source_type, "source_type")
        _require_non_empty(self.parse_version, "parse_version")
        if self.owner_authored and self.default_tier is not SensitivityTier.L3:
            raise ValueError("owner-authored sources are L3 until explicitly projected")


@runtime_checkable
class SourceAdapter(Protocol):
    """A provider, reduced to the only two things Atlas asks of it.

    Implementations must be **pure with respect to Atlas state**: the same window, cursor
    and provider response must always produce the same batch. No adapter writes to the
    database, calls a model, or reads the clock.
    """

    @property
    def descriptor(self) -> AdapterDescriptor: ...

    def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch: ...


def collect(
    adapter: SourceAdapter,
    window: FetchWindow,
    *,
    clock: Clock,
    cursor: SourceCursor | None = None,
) -> FetchBatch:
    """Fetch one source, converting a *typed* failure into a measured gap.

    A failing source degrades this cycle's observation; it does not end the cycle, and it
    does not vanish. Unexpected exceptions are re-raised untouched — see the module
    docstring for why that line is drawn where it is.
    """
    name = adapter.descriptor.name
    resume = cursor or SourceCursor(source_name=name)
    try:
        batch = adapter.fetch(window, resume)
    except AdapterError as error:
        return FetchBatch.unavailable(
            source_name=name,
            fetched_at=clock.now(),
            window=window,
            cursor=resume,
            gaps=(error.as_gap(),),
        )
    if batch.source_name != name:
        raise SourceContractViolation(name, f"adapter returned a batch for {batch.source_name!r}")
    return batch
