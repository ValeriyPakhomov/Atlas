"""Queue 03 — many accounts become one canonical event."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

import pytest

from atlas.events.normalization import (
    ATLAS_EVENT_NAMESPACE,
    EventCandidate,
    build_event,
    event_dedupe_key,
    normalise_event_type,
    normalise_terms,
)
from atlas.events.scoring import Report
from atlas.scoring.relevance import SourceClass

NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
OCCURRED = NOW - timedelta(hours=4)


def candidate(**overrides: Any) -> EventCandidate:
    fields: dict[str, Any] = {
        "event_type": "monetary_policy.rate_decision",
        "title": "ECB keeps key rates unchanged",
        "occurred_at": OCCURRED,
        "primary_entities": ("ECB",),
        "report": Report(OCCURRED + timedelta(minutes=2), "ecb_press", SourceClass.A, UUID(int=1)),
    }
    fields.update(overrides)
    return EventCandidate(**fields)


# ── normalisation ───────────────────────────────────────────────────────────


def test_event_types_fold_to_one_canonical_form():
    assert normalise_event_type(" Monetary Policy/Rate Decision ") == (
        "monetary_policy_rate_decision"
    )
    assert normalise_event_type("markets.earnings") == "markets.earnings"


def test_a_type_that_cannot_be_canonicalised_is_refused():
    for bad in ("", "  ", "policy!", "policy..rate"):
        with pytest.raises(ValueError, match="not canonical"):
            normalise_event_type(bad)


def test_term_sets_are_folded_deduplicated_and_sorted():
    assert normalise_terms(["Nvidia", " nvidia ", "ECB", ""]) == ("ecb", "nvidia")


def test_a_candidate_normalises_itself_on_construction():
    item = candidate(
        event_type="Markets/Earnings",
        title="  Chipmaker   reports  ",
        primary_entities=("Nvidia", "nvidia"),
        geography=("US", "us"),
    )
    assert item.event_type == "markets_earnings"
    assert item.title == "Chipmaker reports"
    assert item.primary_entities == ("nvidia",)
    assert item.geography == ("us",)


def test_an_event_with_no_actor_is_refused():
    with pytest.raises(ValueError, match="primary actor"):
        candidate(primary_entities=())


# ── the dedupe key ──────────────────────────────────────────────────────────


def test_the_key_ignores_the_order_entities_were_extracted_in():
    left = event_dedupe_key("x", ("ecb", "fed"), OCCURRED)
    right = event_dedupe_key("x", ("ecb", "fed"), OCCURRED)
    assert left == right


def test_the_day_bucket_is_taken_in_utc():
    """Two accounts of one instant must not land on different days."""
    tokyo = OCCURRED.astimezone(timezone(timedelta(hours=9)))
    assert event_dedupe_key("x", ("ecb",), OCCURRED) == event_dedupe_key("x", ("ecb",), tokyo)


def test_timestamps_that_differ_by_minutes_still_key_the_same_event():
    early = candidate(occurred_at=OCCURRED)
    late = candidate(occurred_at=OCCURRED + timedelta(minutes=7))
    assert early.dedupe_key == late.dedupe_key


def test_a_different_action_by_the_same_actor_keys_differently():
    assert candidate().dedupe_key != candidate(event_type="governance.appointment").dedupe_key


def test_the_key_is_versioned_so_a_rule_change_is_visible():
    assert candidate().dedupe_key.startswith("event-key-v1:")


# ── assembly ────────────────────────────────────────────────────────────────


def test_the_most_reliable_account_supplies_the_canonical_wording():
    official = candidate(
        title="ECB keeps key rates unchanged",
        report=Report(OCCURRED + timedelta(minutes=2), "ecb_press", SourceClass.A, UUID(int=1)),
    )
    paraphrase = candidate(
        title="Euro rates left alone again",
        report=Report(OCCURRED + timedelta(seconds=30), "aggregator", SourceClass.D, UUID(int=2)),
    )
    event = build_event([paraphrase, official], dedupe_key="k", as_of=NOW)
    assert event.canonical_title == "ECB keeps key rates unchanged"
    assert event.first_reported_at == paraphrase.report.reported_at
    assert event.last_updated_at == official.report.reported_at


def test_assembly_does_not_depend_on_order():
    a = candidate(report=Report(OCCURRED, "ecb_press", SourceClass.A, UUID(int=1)))
    b = candidate(
        title="Rates held",
        entities=("Lagarde",),
        report=Report(OCCURRED + timedelta(minutes=9), "guardian_open", SourceClass.B, UUID(int=2)),
    )
    assert build_event([a, b], dedupe_key="k", as_of=NOW) == build_event(
        [b, a], dedupe_key="k", as_of=NOW
    )


def test_the_event_id_is_derived_from_the_key_so_a_replay_writes_the_same_row():
    event = build_event([candidate()], dedupe_key="k", as_of=NOW)
    assert event.id == uuid5(ATLAS_EVENT_NAMESPACE, "k")


def test_every_account_contributes_its_entities():
    a = candidate(entities=("Lagarde",), sectors=("banks",))
    b = candidate(
        entities=("Governing Council",),
        assets=("EUR",),
        report=Report(OCCURRED, "guardian_open", SourceClass.B, UUID(int=2)),
    )
    event = build_event([a, b], dedupe_key="k", as_of=NOW)
    assert event.entities == ("ecb", "governing council", "lagarde")
    assert event.sectors == ("banks",)
    assert event.assets == ("eur",)


def test_the_first_non_empty_summary_by_authority_is_kept():
    silent = candidate(report=Report(OCCURRED, "ecb_press", SourceClass.A, UUID(int=1)))
    talkative = candidate(
        summary="The Governing Council left all three rates unchanged.",
        report=Report(OCCURRED, "guardian_open", SourceClass.B, UUID(int=2)),
    )
    event = build_event([silent, talkative], dedupe_key="k", as_of=NOW)
    assert event.summary.startswith("The Governing Council")


def test_scores_land_on_the_event():
    event = build_event([candidate()], dedupe_key="k", as_of=NOW)
    assert event.credibility_score == Decimal("1.0000")
    assert Decimal(0) <= event.novelty_score <= Decimal(1)
    assert Decimal(0) <= event.urgency_score <= Decimal(1)
    assert event.status == "active"


def test_an_event_needs_at_least_one_account():
    with pytest.raises(ValueError, match="at least one candidate"):
        build_event([], dedupe_key="k", as_of=NOW)
