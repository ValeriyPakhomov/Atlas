"""News relevance scoring.

Not "how important is this story" — Atlas has no view on that and does not need one. It
is **how much this story bears on this owner**. An item below the floor is not surfaced,
but it stays visible in the Sources view with its discard reason: seeing why 58 of 63
items were dropped builds more trust than reading them would, and it is the surface where
the owner corrects Atlas.

Only entity resolution needs a model. The arithmetic is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

RELEVANCE_FLOOR = Decimal(30)

_ZERO = Decimal(0)
_ONE = Decimal(1)


class SourceClass(StrEnum):
    """Reliability classes from `docs/SOURCE_POLICY.md`."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


_RELIABILITY: dict[SourceClass, Decimal] = {
    SourceClass.A: Decimal("1.00"),
    SourceClass.B: Decimal("0.85"),
    SourceClass.C: Decimal("0.60"),
    SourceClass.D: Decimal("0.35"),
}


class DiscardReason(StrEnum):
    ALREADY_REPORTED = "already_reported"
    NO_EXPOSURE = "no_exposure"
    IMMATERIAL = "immaterial"
    BELOW_FLOOR = "below_floor"


@dataclass(frozen=True, slots=True)
class RelevanceInputs:
    """Everything the score needs, all of it already computed elsewhere."""

    item_id: str
    source_class: SourceClass
    novelty: Decimal
    materiality: Decimal
    exposure_match: Decimal
    duplicate_of_event: str | None = None

    def __post_init__(self) -> None:
        for name in ("novelty", "materiality", "exposure_match"):
            value = getattr(self, name)
            if not _ZERO <= value <= _ONE:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class RelevanceVerdict:
    """The score and, when it does not surface, why — never a silent drop."""

    item_id: str
    score: Decimal
    surfaced: bool
    discard_reason: DiscardReason | None = None
    duplicate_of_event: str | None = None

    @property
    def explanation(self) -> str:
        if self.surfaced:
            return f"relevance {self.score}"
        match self.discard_reason:
            case DiscardReason.ALREADY_REPORTED:
                return f"duplicate of event {self.duplicate_of_event} — no new evidence"
            case DiscardReason.NO_EXPOSURE:
                return "no exposure to the entities named"
            case DiscardReason.IMMATERIAL:
                return "produces no material change"
            case _:
                return f"relevance {self.score}, below the floor of {RELEVANCE_FLOOR}"


def score_relevance(
    inputs: RelevanceInputs,
    *,
    floor: Decimal = RELEVANCE_FLOOR,
) -> RelevanceVerdict:
    """Score one item's bearing on the owner, and decide whether it surfaces.

    Each factor can independently zero the result, which is the intended behaviour: an
    item about something the owner has no exposure to is irrelevant however reliable its
    source, and a fifth report of a known event is irrelevant however material the event.
    """
    if inputs.duplicate_of_event is not None and inputs.novelty == _ZERO:
        return RelevanceVerdict(
            item_id=inputs.item_id,
            score=_ZERO,
            surfaced=False,
            discard_reason=DiscardReason.ALREADY_REPORTED,
            duplicate_of_event=inputs.duplicate_of_event,
        )

    score = (
        Decimal(100)
        * _RELIABILITY[inputs.source_class]
        * inputs.novelty
        * inputs.materiality
        * inputs.exposure_match
    ).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)

    if inputs.exposure_match == _ZERO:
        reason = DiscardReason.NO_EXPOSURE
    elif inputs.materiality == _ZERO:
        reason = DiscardReason.IMMATERIAL
    elif score < floor:
        reason = DiscardReason.BELOW_FLOOR
    else:
        return RelevanceVerdict(item_id=inputs.item_id, score=score, surfaced=True)

    return RelevanceVerdict(
        item_id=inputs.item_id, score=score, surfaced=False, discard_reason=reason
    )
