"""Deterministic event scores.

Three numbers travel with every Event, and all three are computed by rule. No model
produces them, because a score a model produced cannot be replayed and cannot be argued
with.

The distinction that matters most here is between two things both called "novelty":

* **Item novelty** (`atlas.scoring.relevance`) asks whether *this report* adds anything —
  the fifth retelling of a known event scores zero and is not surfaced.
* **Event novelty** (here) asks whether *the event* is new to Atlas. It decays with age
  and nothing else. Being widely reported does not make an event older or newer.

Collapsing them is how systems end up ranking obscure stories above important ones:
"few sources covered it" is not the same as "this is new".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID

from atlas.scoring.relevance import SourceClass, reliability_of

_ZERO = Decimal(0)
_ONE = Decimal(1)
_PLACES = Decimal("0.0001")


def _quantize(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, value)).quantize(_PLACES, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True, slots=True, order=True)
class Report:
    """One source saying the event happened, once."""

    reported_at: datetime
    source_key: str
    source_class: SourceClass
    evidence_id: UUID

    def __post_init__(self) -> None:
        if self.reported_at.tzinfo is None:
            raise ValueError("reported_at must be timezone-aware")
        if not self.source_key.strip():
            raise ValueError("a report must name its source")

    @property
    def reliability(self) -> Decimal:
        return reliability_of(self.source_class)


#: The most credible any event can become on a given class of evidence alone. This is the
#: anti-hype rule from `docs/SOURCE_POLICY.md` expressed as arithmetic: no quantity of
#: class-D agreement reaches the standing of one filing. Volume is not verification.
DEFAULT_CLASS_CEILING: Mapping[SourceClass, Decimal] = {
    SourceClass.A: Decimal("1.00"),
    SourceClass.B: Decimal("0.90"),
    SourceClass.C: Decimal("0.75"),
    SourceClass.D: Decimal("0.55"),
}


@dataclass(frozen=True, slots=True)
class EventScoringPolicy:
    """Versioned constants (ADR-0014), so a past score stays explicable."""

    corroboration_gain: Decimal = Decimal("0.55")
    novelty_window: timedelta = timedelta(hours=48)
    urgency_window: timedelta = timedelta(hours=24)
    default_urgency: Decimal = Decimal("0.5")
    urgency_by_type: Mapping[str, Decimal] = field(default_factory=dict)
    class_ceiling: Mapping[SourceClass, Decimal] = field(
        default_factory=lambda: dict(DEFAULT_CLASS_CEILING)
    )
    version: str = "event-scoring-v1"

    def __post_init__(self) -> None:
        if not _ZERO < self.corroboration_gain <= _ONE:
            raise ValueError("corroboration_gain must be in (0, 1]")
        for window in (self.novelty_window, self.urgency_window):
            if window <= timedelta(0):
                raise ValueError("scoring windows must be positive")
        missing = set(SourceClass) - set(self.class_ceiling)
        if missing:
            raise ValueError(f"class_ceiling is missing {sorted(missing)}")


DEFAULT_SCORING = EventScoringPolicy()


def distinct_sources(reports: Iterable[Report]) -> tuple[Report, ...]:
    """The earliest report from each source.

    Deduplicating by source is what makes corroboration mean *independent* confirmation.
    A source repeating itself — a live blog updating, a feed re-publishing — is one voice
    however many times it speaks.
    """
    earliest: dict[str, Report] = {}
    for report in reports:
        current = earliest.get(report.source_key)
        if current is None or report.reported_at < current.reported_at:
            earliest[report.source_key] = report
    return tuple(sorted(earliest.values()))


def credibility(
    reports: Sequence[Report], *, policy: EventScoringPolicy = DEFAULT_SCORING
) -> Decimal:
    """How much Atlas believes the event happened.

    The strongest source sets the floor; each additional *independent* source closes part
    of the remaining doubt, weighted by its own reliability. Diminishing by construction:
    the fourth outlet agreeing adds far less than the first, and no amount of class-D
    agreement reaches the certainty of a filing.

    A ceiling per class caps the result, so agreement among weak sources cannot
    accumulate into false certainty however many of them speak.

    Order-independent — sources are folded strongest-first — so the same evidence always
    produces the same number, whatever order it arrived in.
    """
    independent = distinct_sources(reports)
    if not independent:
        return _ZERO
    by_strength = sorted(independent, key=lambda report: (-report.reliability, report.source_key))
    score = by_strength[0].reliability
    for report in by_strength[1:]:
        score += (_ONE - score) * policy.corroboration_gain * report.reliability
    ceiling = max(policy.class_ceiling[report.source_class] for report in independent)
    return _quantize(min(score, ceiling))


def novelty(
    first_reported_at: datetime,
    *,
    as_of: datetime,
    policy: EventScoringPolicy = DEFAULT_SCORING,
) -> Decimal:
    """How new the event is to Atlas. Decays with age, and with nothing else."""
    age = as_of - first_reported_at
    if age <= timedelta(0):
        return _ONE
    return _quantize(_ONE - Decimal(age / policy.novelty_window))


def urgency(
    event_type: str,
    occurred_at: datetime,
    *,
    as_of: datetime,
    policy: EventScoringPolicy = DEFAULT_SCORING,
) -> Decimal:
    """How much the event asks for attention now.

    A scheduled event that has not happened yet carries its type's full weight — a rate
    decision tomorrow is urgent precisely because it is still ahead. Once it has happened,
    urgency decays: the same news is worth less attention on Thursday than it was on
    Tuesday, even though its credibility is unchanged.
    """
    weight = policy.urgency_by_type.get(event_type, policy.default_urgency)
    if not _ZERO <= weight <= _ONE:
        raise ValueError(f"urgency weight for {event_type!r} must be between 0 and 1")
    age = as_of - occurred_at
    if age <= timedelta(0):
        return _quantize(weight)
    return _quantize(weight * (_ONE - Decimal(age / policy.urgency_window)))
