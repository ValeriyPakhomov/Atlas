"""The Atlas Score.

A score that hides its inputs is astrology with a progress ring. The rule that makes
this one safe is that it is **derived, never judged**: no model produces it, and every
point is carried by a `Contribution` row that the interface renders directly. The domain
screen is a rendering of those rows, not a second computation.

Specification: `docs/product/ATLAS_SCORE.md`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from atlas.domain.measurement import Measured, MeasurementContext, MissingReason

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)


class ContributionKind(StrEnum):
    WORLD = "world"
    POLICY = "policy"
    IMPACT_DRAG = "impact_drag"
    IMPACT_LIFT = "impact_lift"


class PolicyOutcome(StrEnum):
    PASS = "pass"
    WARN = "warn"
    BREACH = "breach"
    UNKNOWN_DATA = "unknown_data"


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Tunable constants, versioned as an artefact (ADR-0014) so history stays explicable.

    `impact_drag` outweighs `impact_lift` deliberately: a favourable change rarely
    compensates for an adverse one of equal magnitude when the adverse one is harder to
    undo.
    """

    warn_penalty: Decimal = Decimal(8)
    breach_penalty: Decimal = Decimal(28)
    impact_drag: Decimal = Decimal(22)
    impact_lift: Decimal = Decimal(14)
    version: str = "score-weights-v1"


DEFAULT_WEIGHTS = ScoreWeights()


@dataclass(frozen=True, slots=True)
class DimensionExposure:
    """One world dimension and how much of it the owner actually carries.

    `score` is the dimension's own -3..+3 ordinal. `exposure` is the owner's weight on it,
    derived from position and geography — never a judgement.
    """

    key: str
    score: Decimal
    exposure: Decimal
    scale_min: Decimal = Decimal(-3)
    scale_max: Decimal = Decimal(3)

    def __post_init__(self) -> None:
        if not self.scale_min < self.scale_max:
            raise ValueError("scale_min must be below scale_max")
        if not self.scale_min <= self.score <= self.scale_max:
            raise ValueError(f"{self.key} score {self.score} is outside its scale")
        if not _ZERO <= self.exposure <= Decimal(1):
            raise ValueError("exposure must be between 0 and 1")

    @property
    def normalised(self) -> Decimal:
        """Map the ordinal onto 0…100 without asserting more precision than it has."""
        span = self.scale_max - self.scale_min
        return (self.score - self.scale_min) / span * _HUNDRED


@dataclass(frozen=True, slots=True)
class ImpactContribution:
    """A standing impact's pull on the domain score."""

    impact_id: str
    label: str
    priority: Decimal
    favourable: bool

    def __post_init__(self) -> None:
        if not _ZERO <= self.priority <= Decimal(2):
            raise ValueError("priority must be within the 0…2 band ADR-0008 defines")


@dataclass(frozen=True, slots=True)
class Contribution:
    """One line of the explanation. Persisted, and rendered verbatim by the UI."""

    label: str
    points: Decimal
    kind: ContributionKind
    ref: str | None = None


@dataclass(frozen=True, slots=True)
class DomainScoreInputs:
    domain: str
    dimensions: Sequence[DimensionExposure] = ()
    policies: Sequence[tuple[str, PolicyOutcome]] = ()
    impacts: Sequence[ImpactContribution] = ()
    stale_subjects: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class DomainScore:
    domain: str
    score: Decimal
    contributions: tuple[Contribution, ...]
    weights_version: str


def score_domain(
    inputs: DomainScoreInputs,
    *,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
) -> Measured[DomainScore]:
    """Compute one domain score, or refuse to.

    The staleness gate is the rule that keeps the number honest: if any input is past its
    freshness SLA the domain reports no score at all. A score is the easiest thing in the
    product to fake, because nobody can see that it is wrong.
    """
    ctx = MeasurementContext()

    for subject in inputs.stale_subjects:
        ctx.note(subject, MissingReason.STALE, f"blocks the {inputs.domain} score")
    if inputs.stale_subjects:
        return ctx.abandon()

    if not inputs.dimensions:
        ctx.note(inputs.domain, MissingReason.UNKNOWN, "no world dimension is mapped")
        return ctx.abandon()

    rows: list[Contribution] = []

    total_exposure = sum((d.exposure for d in inputs.dimensions), start=_ZERO)
    if total_exposure == _ZERO:
        ctx.note(inputs.domain, MissingReason.UNKNOWN, "owner has no exposure to this domain")
        return ctx.abandon()

    world = _ZERO
    for dimension in inputs.dimensions:
        share = dimension.exposure / total_exposure
        points = dimension.normalised * share
        world += points
        rows.append(
            Contribution(
                label=dimension.key,
                points=_round(points),
                kind=ContributionKind.WORLD,
                ref=dimension.key,
            )
        )

    running = world

    for name, outcome in inputs.policies:
        if outcome is PolicyOutcome.UNKNOWN_DATA:
            ctx.note(name, MissingReason.UNKNOWN, "policy could not be evaluated")
            continue
        penalty = {
            PolicyOutcome.PASS: _ZERO,
            PolicyOutcome.WARN: weights.warn_penalty,
            PolicyOutcome.BREACH: weights.breach_penalty,
        }[outcome]
        if penalty:
            running -= penalty
            rows.append(
                Contribution(label=name, points=_round(-penalty), kind=ContributionKind.POLICY)
            )

    for impact in inputs.impacts:
        factor = weights.impact_lift if impact.favourable else weights.impact_drag
        signed = impact.priority * factor * (Decimal(1) if impact.favourable else Decimal(-1))
        running += signed
        kind = ContributionKind.IMPACT_LIFT if impact.favourable else ContributionKind.IMPACT_DRAG
        rows.append(
            Contribution(
                label=impact.label,
                points=_round(signed),
                kind=kind,
                ref=impact.impact_id,
            )
        )

    score = _clamp(running)
    result = DomainScore(
        domain=inputs.domain,
        score=_round(score),
        contributions=tuple(sorted(rows, key=lambda r: r.points)),
        weights_version=weights.version,
    )
    return ctx.settle(result)


def overall_score(
    domains: Iterable[Measured[DomainScore]],
    objective_priority: Mapping[str, Decimal],
) -> Measured[Decimal]:
    """Objective-weighted mean of the domain scores.

    A domain the owner holds no active objective in is excluded rather than averaged in
    at a neutral value, and an unavailable domain is excluded with its reason carried
    forward — never imputed.
    """
    ctx = MeasurementContext()
    weighted = _ZERO
    total_weight = _ZERO

    for measured in domains:
        ctx.absorb(measured)
        if measured.value is None:
            continue
        weight = objective_priority.get(measured.value.domain, _ZERO)
        if weight <= _ZERO:
            continue
        weighted += measured.value.score * weight
        total_weight += weight

    if total_weight == _ZERO:
        ctx.note("atlas score", MissingReason.UNKNOWN, "no scorable domain carries an objective")
        return ctx.abandon()
    return ctx.settle(_round(weighted / total_weight))


def _clamp(value: Decimal) -> Decimal:
    return max(_ZERO, min(_HUNDRED, value))


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN)
