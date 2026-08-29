"""A06 as a type: you cannot get a value out without acknowledging its gaps."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from atlas.domain.measurement import (
    Completeness,
    IncompleteResultError,
    Measured,
    MeasurementContext,
    MissingInput,
    MissingReason,
)

EARLY = datetime(2026, 8, 20, tzinfo=UTC)
LATE = datetime(2026, 8, 28, tzinfo=UTC)


def test_an_unavailable_result_cannot_carry_a_value() -> None:
    with pytest.raises(ValueError):
        Measured(42, Completeness.UNAVAILABLE, (MissingInput("x", MissingReason.UNKNOWN),))


def test_an_incomplete_result_must_say_what_is_missing() -> None:
    with pytest.raises(ValueError):
        Measured(42, Completeness.PARTIAL, ())


def test_a_complete_result_cannot_name_missing_inputs() -> None:
    with pytest.raises(ValueError):
        Measured(42, Completeness.COMPLETE, (MissingInput("x", MissingReason.STALE),))


def test_require_refuses_a_partial_answer_and_names_the_gap() -> None:
    ctx = MeasurementContext()
    ctx.note("portfolio feed", MissingReason.STALE, "9d")
    result = ctx.settle(42)
    with pytest.raises(IncompleteResultError, match="portfolio feed"):
        result.require()


def test_freshness_is_the_oldest_input_not_the_newest() -> None:
    ctx = MeasurementContext()
    ctx.observed(LATE)
    ctx.observed(EARLY)
    assert ctx.settle(1).oldest_input_at == EARLY


def test_map_carries_gaps_and_freshness_through() -> None:
    ctx = MeasurementContext()
    ctx.observed(EARLY)
    ctx.note("rate", MissingReason.MISSING)
    doubled = ctx.settle(21).map(lambda v: v * 2)
    assert doubled.value == 42
    assert doubled.completeness is Completeness.PARTIAL
    assert doubled.oldest_input_at == EARLY
    assert doubled.missing[0].subject == "rate"


def test_mapping_an_unavailable_result_stays_unavailable() -> None:
    unavailable = Measured[int].unavailable([MissingInput("x", MissingReason.UNKNOWN)])
    assert unavailable.map(lambda v: v * 2).completeness is Completeness.UNAVAILABLE


def test_degraded_by_downgrades_a_complete_result() -> None:
    complete = Measured.complete(10)
    degraded = complete.degraded_by([MissingInput("fx", MissingReason.MISSING)])
    assert degraded.completeness is Completeness.PARTIAL
    assert degraded.value == 10


def test_degrading_by_nothing_is_a_no_op() -> None:
    complete = Measured.complete(10)
    assert complete.degraded_by([]) is complete


def test_gaps_are_deduplicated_by_subject_and_reason() -> None:
    ctx = MeasurementContext()
    ctx.note("feed", MissingReason.STALE, "9d")
    ctx.note("feed", MissingReason.STALE, "9d again")
    assert len(ctx.settle(1).missing) == 1


def test_abandoning_without_a_reason_is_itself_an_error() -> None:
    with pytest.raises(ValueError):
        MeasurementContext().abandon()


def test_or_else_is_an_explicit_visible_fallback() -> None:
    unavailable = Measured[int].unavailable([MissingInput("x", MissingReason.UNKNOWN)])
    assert unavailable.or_else(0) == 0
    assert unavailable.is_usable is False
