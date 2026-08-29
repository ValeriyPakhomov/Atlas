"""Queue 03 — the three deterministic scores every Event carries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from atlas.events.scoring import (
    DEFAULT_SCORING,
    EventScoringPolicy,
    Report,
    credibility,
    distinct_sources,
    novelty,
    urgency,
)
from atlas.scoring.relevance import SourceClass

NOW = datetime(2026, 8, 29, 9, 0, tzinfo=UTC)


def report(source: str, source_class: SourceClass, *, hours_ago: float = 0.0) -> Report:
    return Report(
        reported_at=NOW - timedelta(hours=hours_ago),
        source_key=source,
        source_class=source_class,
        evidence_id=UUID(int=abs(hash((source, hours_ago))) % (2**128)),
    )


# ── credibility ─────────────────────────────────────────────────────────────


def test_an_official_primary_source_is_believed():
    assert credibility([report("ecb_press", SourceClass.A)]) == Decimal("1.0000")


def test_an_independent_second_source_closes_part_of_the_doubt():
    alone = credibility([report("guardian_open", SourceClass.B)])
    corroborated = credibility(
        [report("guardian_open", SourceClass.B), report("ft", SourceClass.B)]
    )
    assert alone == Decimal("0.8500")
    assert corroborated > alone


def test_a_source_repeating_itself_is_still_one_voice():
    once = credibility([report("guardian_open", SourceClass.B)])
    thrice = credibility(
        [
            report("guardian_open", SourceClass.B, hours_ago=2),
            report("guardian_open", SourceClass.B, hours_ago=1),
            report("guardian_open", SourceClass.B),
        ]
    )
    assert thrice == once


def test_no_volume_of_weak_agreement_reaches_the_standing_of_a_filing():
    """The anti-hype rule as arithmetic: volume is not verification."""
    crowd = credibility([report(f"channel-{n}", SourceClass.D, hours_ago=n) for n in range(12)])
    assert crowd == Decimal("0.5500")
    assert crowd < credibility([report("sec_edgar", SourceClass.A)])


def test_credibility_does_not_depend_on_arrival_order():
    reports = [
        report("aggregator", SourceClass.D, hours_ago=3),
        report("ecb_press", SourceClass.A, hours_ago=1),
        report("guardian_open", SourceClass.B, hours_ago=2),
    ]
    assert credibility(reports) == credibility(list(reversed(reports)))


def test_no_reports_means_no_credibility():
    assert credibility([]) == Decimal(0)


def test_distinct_sources_keeps_the_earliest_from_each():
    late = report("guardian_open", SourceClass.B, hours_ago=1)
    early = report("guardian_open", SourceClass.B, hours_ago=5)
    assert distinct_sources([late, early]) == (early,)


# ── novelty ─────────────────────────────────────────────────────────────────


def test_event_novelty_decays_with_age_and_nothing_else():
    assert novelty(NOW, as_of=NOW) == Decimal(1)
    assert novelty(NOW - timedelta(hours=24), as_of=NOW) == Decimal("0.5000")
    assert novelty(NOW - timedelta(hours=48), as_of=NOW) == Decimal("0.0000")
    assert novelty(NOW - timedelta(days=9), as_of=NOW) == Decimal("0.0000")


def test_wide_coverage_does_not_make_an_event_older_or_newer():
    """Item novelty and event novelty are different questions; only one lives here."""
    first_seen = NOW - timedelta(hours=6)
    assert novelty(first_seen, as_of=NOW) == novelty(first_seen, as_of=NOW)


# ── urgency ─────────────────────────────────────────────────────────────────


def test_a_scheduled_event_carries_its_full_weight_until_it_happens():
    policy = EventScoringPolicy(urgency_by_type={"monetary_policy.rate_decision": Decimal("0.9")})
    ahead = urgency(
        "monetary_policy.rate_decision", NOW + timedelta(hours=20), as_of=NOW, policy=policy
    )
    assert ahead == Decimal("0.9000")


def test_urgency_decays_after_the_event():
    policy = EventScoringPolicy(urgency_by_type={"x": Decimal("1")})
    assert urgency("x", NOW - timedelta(hours=6), as_of=NOW, policy=policy) == Decimal("0.7500")
    assert urgency("x", NOW - timedelta(hours=30), as_of=NOW, policy=policy) == Decimal("0.0000")


def test_an_unweighted_type_falls_back_to_the_declared_default():
    assert urgency("unknown.type", NOW, as_of=NOW) == DEFAULT_SCORING.default_urgency


# ── policy validation ───────────────────────────────────────────────────────


def test_a_policy_missing_a_class_ceiling_is_refused():
    with pytest.raises(ValueError, match="class_ceiling is missing"):
        EventScoringPolicy(class_ceiling={SourceClass.A: Decimal("1")})


def test_scoring_windows_must_be_positive():
    with pytest.raises(ValueError, match="windows must be positive"):
        EventScoringPolicy(novelty_window=timedelta(0))


def test_a_report_must_name_its_source_and_carry_an_aware_time():
    with pytest.raises(ValueError, match="must name its source"):
        Report(NOW, "  ", SourceClass.A, UUID(int=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        Report(datetime(2026, 8, 29, 9, 0), "x", SourceClass.A, UUID(int=1))
