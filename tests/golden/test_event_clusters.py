"""Queue 03 acceptance — golden fixtures merge duplicate reporting into a single event."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from tests.conftest import REPO_ROOT

from atlas.domain.clock import FixedClock
from atlas.events import (
    EventCandidate,
    EventGraph,
    MergeOutcome,
    Report,
    distinct_sources,
)
from atlas.scoring.relevance import SourceClass

FIXTURE = REPO_ROOT / "fixtures" / "golden" / "events" / "duplicate_reporting.json"

pytestmark = pytest.mark.golden


def load() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data


def to_candidate(payload: dict[str, Any]) -> EventCandidate:
    report = payload["report"]
    return EventCandidate(
        event_type=payload["event_type"],
        title=payload["title"],
        summary=payload.get("summary", ""),
        occurred_at=datetime.fromisoformat(payload["occurred_at"]),
        report=Report(
            reported_at=datetime.fromisoformat(report["reported_at"]),
            source_key=report["source_key"],
            source_class=SourceClass(report["source_class"]),
            evidence_id=UUID(report["evidence_id"]),
        ),
        primary_entities=tuple(payload.get("primary_entities", ())),
        entities=tuple(payload.get("entities", ())),
        geography=tuple(payload.get("geography", ())),
        sectors=tuple(payload.get("sectors", ())),
        assets=tuple(payload.get("assets", ())),
    )


CLUSTERS = load()["clusters"]
AS_OF = datetime.fromisoformat(load()["as_of"])


@pytest.mark.parametrize("cluster", CLUSTERS, ids=[c["id"] for c in CLUSTERS])
def test_golden_cluster_resolves_as_expected(cluster: dict[str, Any]) -> None:
    graph = EventGraph(clock=FixedClock(AS_OF))
    results = graph.absorb_all(to_candidate(payload) for payload in cluster["candidates"])
    expected = cluster["expected"]

    assert len(graph.events) == expected["events"], cluster["why"]

    merged_by_proposal = sum(
        1 for result in results if result.outcome is MergeOutcome.MERGED_BY_PROPOSAL
    )
    assert merged_by_proposal == expected["merged_by_proposal"]

    if expected["events"] != 1:
        return

    record = graph.records[0]
    event = record.event
    if "canonical_title" in expected:
        assert event.canonical_title == expected["canonical_title"]
    if "credibility" in expected:
        assert event.credibility_score == Decimal(expected["credibility"])
    if "evidence" in expected:
        assert len(event.evidence_ids) == expected["evidence"]
    if "distinct_sources" in expected:
        reports = [candidate.report for candidate in record.candidates]
        assert len(distinct_sources(reports)) == expected["distinct_sources"]


def test_reordering_the_reports_changes_nothing() -> None:
    """Order-independence is what makes a replay reproduce the graph (A07)."""
    for cluster in CLUSTERS:
        candidates = [to_candidate(payload) for payload in cluster["candidates"]]
        forward = EventGraph(clock=FixedClock(AS_OF))
        forward.absorb_all(candidates)
        backward = EventGraph(clock=FixedClock(AS_OF))
        backward.absorb_all(reversed(candidates))
        assert forward.events == backward.events, cluster["id"]


def test_ingesting_the_whole_fixture_twice_creates_nothing_new() -> None:
    """A08 at the event layer: re-ingestion must not double events or inflate evidence."""
    for cluster in CLUSTERS:
        candidates = [to_candidate(payload) for payload in cluster["candidates"]]
        graph = EventGraph(clock=FixedClock(AS_OF))
        graph.absorb_all(candidates)
        first = graph.events

        graph.absorb_all(candidates)
        assert graph.events == first, cluster["id"]


def test_the_fixture_carries_no_personal_state() -> None:
    """`fixtures/README.md`: synthetic only — no balances, accounts, addresses or PII."""
    raw = FIXTURE.read_text(encoding="utf-8").casefold()
    for forbidden in ("iban", "passport", "balance", "account_number", "@gmail", "wallet"):
        assert forbidden not in raw
