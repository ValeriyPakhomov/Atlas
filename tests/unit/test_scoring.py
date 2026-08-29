"""The Atlas Score is derived, never judged — and refuses to exist when inputs are stale."""

from __future__ import annotations

from decimal import Decimal

import pytest

from atlas.domain.measurement import Completeness, MissingReason
from atlas.scoring import (
    RELEVANCE_FLOOR,
    ContributionKind,
    DimensionExposure,
    DomainScoreInputs,
    ImpactContribution,
    PolicyOutcome,
    RelevanceInputs,
    SourceClass,
    overall_score,
    score_domain,
    score_relevance,
)
from atlas.scoring.relevance import DiscardReason


def dim(key: str, score: str, exposure: str = "1") -> DimensionExposure:
    return DimensionExposure(key=key, score=Decimal(score), exposure=Decimal(exposure))


# ── domain score ────────────────────────────────────────────────────────────
def test_a_neutral_world_with_no_penalties_scores_the_midpoint() -> None:
    result = score_domain(
        DomainScoreInputs(domain="capital", dimensions=[dim("macro.liquidity", "0")])
    )
    assert result.require().score == Decimal("50.0")


def test_the_scale_maps_its_endpoints_to_zero_and_one_hundred() -> None:
    worst = score_domain(DomainScoreInputs(domain="d", dimensions=[dim("k", "-3")])).require()
    best = score_domain(DomainScoreInputs(domain="d", dimensions=[dim("k", "3")])).require()
    assert (worst.score, best.score) == (Decimal("0.0"), Decimal("100.0"))


def test_dimensions_are_weighted_by_owner_exposure_not_equally() -> None:
    result = score_domain(
        DomainScoreInputs(
            domain="capital",
            dimensions=[dim("heavy", "3", "0.9"), dim("light", "-3", "0.1")],
        )
    ).require()
    assert result.score == Decimal("90.0")


def test_a_breach_costs_more_than_a_warning() -> None:
    base = DomainScoreInputs(domain="d", dimensions=[dim("k", "0")])
    warn = score_domain(
        DomainScoreInputs(
            domain="d", dimensions=base.dimensions, policies=[("p", PolicyOutcome.WARN)]
        )
    ).require()
    breach = score_domain(
        DomainScoreInputs(
            domain="d", dimensions=base.dimensions, policies=[("p", PolicyOutcome.BREACH)]
        )
    ).require()
    assert warn.score == Decimal("42.0")
    assert breach.score == Decimal("22.0")
    assert breach.score < warn.score


def test_an_unevaluable_policy_is_reported_not_scored_as_a_pass() -> None:
    result = score_domain(
        DomainScoreInputs(
            domain="d",
            dimensions=[dim("k", "0")],
            policies=[("single-country", PolicyOutcome.UNKNOWN_DATA)],
        )
    )
    assert result.completeness is Completeness.PARTIAL
    assert result.missing[0].subject == "single-country"


def test_adverse_impacts_weigh_more_than_favourable_ones_of_equal_priority() -> None:
    adverse = score_domain(
        DomainScoreInputs(
            domain="d",
            dimensions=[dim("k", "0")],
            impacts=[ImpactContribution("i1", "bad", Decimal("1"), favourable=False)],
        )
    ).require()
    favourable = score_domain(
        DomainScoreInputs(
            domain="d",
            dimensions=[dim("k", "0")],
            impacts=[ImpactContribution("i2", "good", Decimal("1"), favourable=True)],
        )
    ).require()
    assert Decimal(50) - adverse.score > favourable.score - Decimal(50)


def test_every_point_is_carried_by_a_contribution_row() -> None:
    result = score_domain(
        DomainScoreInputs(
            domain="mobility",
            dimensions=[dim("migration.eu", "-1")],
            policies=[("residency deadline", PolicyOutcome.BREACH)],
            impacts=[
                ImpactContribution("i1", "permit deadline", Decimal("0.79"), favourable=False)
            ],
        )
    ).require()
    kinds = {c.kind for c in result.contributions}
    assert kinds == {ContributionKind.WORLD, ContributionKind.POLICY, ContributionKind.IMPACT_DRAG}
    assert result.contributions[0].points < 0  # sorted worst-first
    assert any(c.ref == "i1" for c in result.contributions)


def test_the_score_is_clamped_rather_than_going_negative() -> None:
    result = score_domain(
        DomainScoreInputs(
            domain="d",
            dimensions=[dim("k", "-3")],
            policies=[("a", PolicyOutcome.BREACH)],
        )
    ).require()
    assert result.score == Decimal("0.0")


def test_a_stale_input_produces_no_score_at_all() -> None:
    result = score_domain(
        DomainScoreInputs(
            domain="markets", dimensions=[dim("k", "1")], stale_subjects=["portfolio feed"]
        )
    )
    assert result.completeness is Completeness.UNAVAILABLE
    assert result.value is None
    assert result.missing[0].reason is MissingReason.STALE


def test_a_domain_with_no_exposure_is_not_scored() -> None:
    result = score_domain(DomainScoreInputs(domain="d", dimensions=[dim("k", "1", "0")]))
    assert result.completeness is Completeness.UNAVAILABLE


def test_the_weights_version_travels_with_the_score() -> None:
    result = score_domain(DomainScoreInputs(domain="d", dimensions=[dim("k", "0")])).require()
    assert result.weights_version == "score-weights-v1"


@pytest.mark.parametrize("score", ["-4", "4"])
def test_a_dimension_outside_its_scale_is_rejected(score: str) -> None:
    with pytest.raises(ValueError, match="outside its scale"):
        dim("k", score)


# ── overall ─────────────────────────────────────────────────────────────────
def test_overall_weights_domains_by_objective_priority() -> None:
    a = score_domain(DomainScoreInputs(domain="a", dimensions=[dim("k", "3")]))
    b = score_domain(DomainScoreInputs(domain="b", dimensions=[dim("k", "-3")]))
    result = overall_score([a, b], {"a": Decimal(3), "b": Decimal(1)})
    assert result.require() == Decimal("75.0")


def test_an_unavailable_domain_is_excluded_with_its_reason_carried_forward() -> None:
    good = score_domain(DomainScoreInputs(domain="a", dimensions=[dim("k", "3")]))
    stale = score_domain(
        DomainScoreInputs(domain="b", dimensions=[dim("k", "0")], stale_subjects=["feed"])
    )
    result = overall_score([good, stale], {"a": Decimal(1), "b": Decimal(1)})
    assert result.value == Decimal("100.0")
    assert result.completeness is Completeness.PARTIAL
    assert result.missing[0].subject == "feed"


def test_a_domain_with_no_objective_is_excluded_rather_than_averaged_in() -> None:
    a = score_domain(DomainScoreInputs(domain="a", dimensions=[dim("k", "3")]))
    b = score_domain(DomainScoreInputs(domain="b", dimensions=[dim("k", "-3")]))
    assert overall_score([a, b], {"a": Decimal(1)}).require() == Decimal("100.0")


def test_no_scorable_domain_yields_no_overall_score() -> None:
    stale = score_domain(
        DomainScoreInputs(domain="b", dimensions=[dim("k", "0")], stale_subjects=["feed"])
    )
    assert overall_score([stale], {"b": Decimal(1)}).completeness is Completeness.UNAVAILABLE


# ── relevance ───────────────────────────────────────────────────────────────
def test_a_reliable_material_item_the_owner_is_exposed_to_surfaces() -> None:
    verdict = score_relevance(
        RelevanceInputs("i1", SourceClass.A, Decimal(1), Decimal("0.95"), Decimal("0.96"))
    )
    assert verdict.surfaced
    assert verdict.score == Decimal(91)


def test_source_class_scales_the_same_story_down() -> None:
    args = (Decimal(1), Decimal("0.95"), Decimal("0.96"))
    a = score_relevance(RelevanceInputs("i", SourceClass.A, *args)).score
    d = score_relevance(RelevanceInputs("i", SourceClass.D, *args)).score
    assert d < a


def test_no_exposure_makes_a_reliable_story_irrelevant() -> None:
    verdict = score_relevance(
        RelevanceInputs("i", SourceClass.A, Decimal(1), Decimal(1), Decimal(0))
    )
    assert not verdict.surfaced
    assert verdict.discard_reason is DiscardReason.NO_EXPOSURE
    assert "no exposure" in verdict.explanation


def test_a_repeat_of_a_known_event_is_discarded_with_the_event_named() -> None:
    verdict = score_relevance(
        RelevanceInputs(
            "i", SourceClass.B, Decimal(0), Decimal("0.9"), Decimal("0.9"), duplicate_of_event="e42"
        )
    )
    assert verdict.discard_reason is DiscardReason.ALREADY_REPORTED
    assert "e42" in verdict.explanation


def test_an_immaterial_price_move_does_not_surface() -> None:
    verdict = score_relevance(
        RelevanceInputs("btc-daily", SourceClass.C, Decimal(1), Decimal(0), Decimal("0.9"))
    )
    assert verdict.discard_reason is DiscardReason.IMMATERIAL


def test_a_discarded_item_keeps_its_score_and_reason_rather_than_vanishing() -> None:
    verdict = score_relevance(
        RelevanceInputs("i", SourceClass.C, Decimal("0.4"), Decimal("0.4"), Decimal("0.4"))
    )
    assert not verdict.surfaced
    assert verdict.score < RELEVANCE_FLOOR
    assert verdict.discard_reason is DiscardReason.BELOW_FLOOR
    assert verdict.explanation


@pytest.mark.parametrize("bad", ["-0.1", "1.1"])
def test_relevance_factors_must_be_fractions(bad: str) -> None:
    with pytest.raises(ValueError):
        RelevanceInputs("i", SourceClass.A, Decimal(bad), Decimal(1), Decimal(1))
