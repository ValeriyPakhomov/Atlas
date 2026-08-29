"""Queue 03 — the deterministic spine and the advisory layer (ADR-0007)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest

from atlas.domain.clock import FixedClock
from atlas.events.dedupe import (
    DecidedBy,
    EventGraph,
    EventMergeProposal,
    EventRecord,
    MergeDecision,
    MergeMethod,
    MergeOutcome,
    MergePolicy,
    entity_time_topic_score,
    jaccard,
)
from atlas.events.normalization import EventCandidate
from atlas.events.scoring import Report
from atlas.scoring.relevance import SourceClass

NOW = datetime(2026, 8, 30, 9, 0, tzinfo=UTC)
CLOCK = FixedClock(NOW)
LATE = datetime(2026, 8, 28, 23, 50, tzinfo=UTC)
JUST_AFTER = datetime(2026, 8, 29, 0, 10, tzinfo=UTC)

_counter = iter(range(1, 10_000))


def candidate(**overrides: Any) -> EventCandidate:
    fields: dict[str, Any] = {
        "event_type": "regulation.enforcement",
        "title": "SEC opens enforcement action",
        "occurred_at": LATE,
        "primary_entities": ("SEC",),
    }
    fields.update(overrides)
    fields.setdefault(
        "report",
        Report(
            fields["occurred_at"] + timedelta(minutes=5),
            fields.pop("source_key", "sec_edgar"),
            fields.pop("source_class", SourceClass.A),
            UUID(int=next(_counter)),
        ),
    )
    fields.pop("source_key", None)
    fields.pop("source_class", None)
    return EventCandidate(**fields)


def graph(**kwargs: Any) -> EventGraph:
    return EventGraph(clock=CLOCK, **kwargs)


# ── the deterministic spine ─────────────────────────────────────────────────


def test_the_same_key_is_the_same_event_with_no_judgement_involved():
    g = graph()
    first = g.absorb(candidate())
    second = g.absorb(
        candidate(title="US regulator acts", source_key="guardian_open", source_class=SourceClass.B)
    )
    assert first.outcome is MergeOutcome.CREATED
    assert second.outcome is MergeOutcome.MERGED_EXACT
    assert len(g.events) == 1
    assert g.proposals == ()


def test_re_absorbing_the_same_account_changes_nothing():
    """A08 at the event layer: re-ingestion must not inflate corroboration."""
    g = graph()
    item = candidate()
    g.absorb(item)
    before = g.events
    g.absorb(item)
    assert g.events == before
    assert len(g.events[0].evidence_ids) == 1


def test_a_different_action_by_the_same_actor_stays_a_separate_event():
    """Entity overlap must never outvote the event type."""
    g = graph()
    g.absorb(candidate())
    result = g.absorb(candidate(event_type="governance.appointment", title="SEC names counsel"))
    assert result.outcome is MergeOutcome.CREATED
    assert len(g.events) == 2


# ── the advisory layer ──────────────────────────────────────────────────────


def test_an_event_straddling_midnight_is_put_back_together_and_leaves_a_proposal():
    g = graph()
    g.absorb(candidate(occurred_at=LATE))
    result = g.absorb(
        candidate(
            occurred_at=JUST_AFTER,
            title="US regulator opens action",
            source_key="guardian_open",
            source_class=SourceClass.B,
        )
    )
    assert result.outcome is MergeOutcome.MERGED_BY_PROPOSAL
    assert len(g.events) == 1
    assert result.proposal is not None
    assert result.proposal.decision is MergeDecision.AUTO_ACCEPTED
    assert result.proposal.method is MergeMethod.ENTITY_TIME_TOPIC
    assert "merged into" in result.explanation


def test_a_partial_match_creates_the_event_and_flags_it_rather_than_merging():
    g = graph(policy=MergePolicy(auto_accept=Decimal("0.95"), propose_floor=Decimal("0.30")))
    g.absorb(candidate(primary_entities=("SEC",)))
    result = g.absorb(
        candidate(
            primary_entities=("SEC", "CFTC"),
            occurred_at=JUST_AFTER,
            title="Two regulators act",
            source_key="guardian_open",
            source_class=SourceClass.B,
        )
    )
    assert result.outcome is MergeOutcome.CREATED_WITH_PROPOSAL
    assert len(g.events) == 2
    assert result.proposal is not None
    assert result.proposal.decision is MergeDecision.PENDING


def test_a_pair_below_the_floor_is_remembered_as_rejected_not_re_proposed_nightly():
    g = graph()
    g.absorb(candidate())
    g.absorb(candidate(event_type="governance.appointment", title="SEC names counsel"))
    assert MergeDecision.REJECTED in g.decisions.values()
    assert g.proposals == ()


def test_the_merged_event_keeps_the_most_authoritative_account_s_identity():
    """Otherwise the same reports in a different order identify the event differently."""
    official = candidate(occurred_at=LATE)
    paraphrase = candidate(
        occurred_at=JUST_AFTER,
        title="US regulator opens action",
        source_key="guardian_open",
        source_class=SourceClass.B,
    )
    forward = graph()
    forward.absorb_all([official, paraphrase])
    backward = graph()
    backward.absorb_all([paraphrase, official])

    assert forward.events == backward.events
    assert forward.records[0].dedupe_key == official.dedupe_key
    assert paraphrase.dedupe_key in forward.records[0].merged_keys


def test_a_later_report_of_a_merged_key_lands_on_the_merged_event():
    g = graph()
    g.absorb(candidate(occurred_at=LATE))
    g.absorb(
        candidate(occurred_at=JUST_AFTER, source_key="guardian_open", source_class=SourceClass.B)
    )
    third = g.absorb(
        candidate(occurred_at=JUST_AFTER, source_key="gdelt", source_class=SourceClass.C)
    )
    assert third.outcome is MergeOutcome.MERGED_EXACT
    assert len(g.events) == 1
    assert len(g.events[0].evidence_ids) == 3


# ── replay reads decisions rather than recomputing them ─────────────────────


def exploding_scorer(*_: Any) -> Decimal:
    raise AssertionError("a replay must not recompute similarity")


def test_replay_reproduces_the_graph_from_stored_decisions_alone():
    """ADR-0007: changing the similarity method must not rewrite what already happened."""
    candidates = [
        candidate(occurred_at=LATE),
        candidate(
            occurred_at=JUST_AFTER,
            title="US regulator opens action",
            source_key="guardian_open",
            source_class=SourceClass.B,
        ),
    ]
    live = graph()
    live.absorb_all(candidates)

    replay = EventGraph(clock=CLOCK, decisions=live.decisions, scorer=exploding_scorer)
    replay.absorb_all(candidates)
    assert replay.events == live.events


def test_an_owner_rejection_holds_against_any_later_scoring():
    candidates = [
        candidate(occurred_at=LATE),
        candidate(
            occurred_at=JUST_AFTER,
            title="US regulator opens action",
            source_key="guardian_open",
            source_class=SourceClass.B,
        ),
    ]
    overridden = {(candidates[1].dedupe_key, candidates[0].dedupe_key): MergeDecision.REJECTED}
    g = EventGraph(clock=CLOCK, decisions=overridden)
    g.absorb_all(candidates)
    assert len(g.events) == 2


# ── the scoring rule ────────────────────────────────────────────────────────


def test_jaccard_measures_overlap():
    assert jaccard(("a", "b"), ("a", "b")) == Decimal("1.0000")
    assert jaccard(("a",), ("a", "b")) == Decimal("0.5000")
    assert jaccard(("a",), ("b",)) == Decimal("0.0000")
    assert jaccard((), ()) == Decimal("0.0000")


def test_the_score_is_zero_outside_the_comparison_window():
    g = graph()
    g.absorb(candidate(occurred_at=LATE))
    record: EventRecord = g.records[0]
    far = candidate(occurred_at=LATE + timedelta(days=9))
    assert entity_time_topic_score(far, record, MergePolicy()) == Decimal(0)


# ── proposal invariants ─────────────────────────────────────────────────────


def test_a_rule_based_proposal_cannot_claim_a_model():
    with pytest.raises(ValueError, match="no model to record"):
        EventMergeProposal(
            source_key="a",
            target_key="b",
            method=MergeMethod.ENTITY_TIME_TOPIC,
            score=Decimal("0.9"),
            threshold_applied=Decimal("0.85"),
            decision=MergeDecision.AUTO_ACCEPTED,
            decided_at=NOW,
            model_name="embed-1",
        )


def test_a_similarity_proposal_must_record_the_model_that_produced_it():
    with pytest.raises(ValueError, match="must record the model"):
        EventMergeProposal(
            source_key="a",
            target_key="b",
            method=MergeMethod.SEMANTIC_SIMILARITY,
            score=Decimal("0.9"),
            threshold_applied=Decimal("0.85"),
            decision=MergeDecision.PENDING,
            decided_at=NOW,
        )


def test_a_proposal_relates_two_different_events():
    with pytest.raises(ValueError, match="two different events"):
        EventMergeProposal(
            source_key="a",
            target_key="a",
            method=MergeMethod.ENTITY_TIME_TOPIC,
            score=Decimal("0.9"),
            threshold_applied=Decimal("0.85"),
            decision=MergeDecision.PENDING,
            decided_at=NOW,
        )


def test_proposals_record_who_decided():
    g = graph()
    g.absorb(candidate(occurred_at=LATE))
    g.absorb(
        candidate(occurred_at=JUST_AFTER, source_key="guardian_open", source_class=SourceClass.B)
    )
    assert g.proposals[0].decided_by is DecidedBy.SYSTEM
    assert g.proposals[0].decided_at == NOW


def test_merge_thresholds_must_be_ordered():
    with pytest.raises(ValueError, match="thresholds must satisfy"):
        MergePolicy(auto_accept=Decimal("0.4"), propose_floor=Decimal("0.6"))
    with pytest.raises(ValueError, match="sum to 1"):
        MergePolicy(entity_weight=Decimal("0.5"), time_weight=Decimal("0.2"))
