"""Queue 02 acceptance — ingesting the same fixture twice produces no duplicates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from atlas.domain.clock import FixedClock
from atlas.domain.measurement import Completeness
from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.adapters import FixtureAdapter, ManualSubmissionAdapter, OwnerSubmission
from atlas.ingestion.contracts import (
    FetchedItem,
    FetchWindow,
    SourceAdapter,
    SourceCursor,
    SourceUnavailable,
    collect,
)
from atlas.ingestion.idempotency import Deduplicator, InMemoryLedger
from atlas.ingestion.pipeline import (
    IngestionReport,
    ingest,
    raw_item_id,
    run_counts,
    run_gaps,
)
from atlas.ingestion.triage import (
    ExposureGate,
    ExposureKind,
    ExposureProfile,
    ExposureTerm,
    TriageStage,
)

NOW = datetime(2026, 8, 29, 9, 0, tzinfo=UTC)
CLOCK = FixedClock(NOW)
SOURCE_ID = UUID("11111111-1111-4111-8111-111111111111")

NVIDIA = ExposureTerm(
    key="entity:nvidia", label="Nvidia", kind=ExposureKind.ENTITY, weight=Decimal("0.9")
)
GEORGIA = ExposureTerm(
    key="country:GE",
    label="Georgia",
    kind=ExposureKind.COUNTRY,
    weight=Decimal("0.8"),
    aliases=("Tbilisi",),
)

FIXTURE_ITEMS = (
    FetchedItem(
        observed_at=NOW - timedelta(hours=2),
        external_id="wire-1",
        url="https://example.com/nvidia-guidance",
        title="Nvidia raises guidance",
        body="The company lifted its outlook for the quarter.",
        published_at=NOW - timedelta(hours=2),
    ),
    FetchedItem(
        observed_at=NOW - timedelta(hours=1),
        external_id="wire-2",
        url="https://example.com/tbilisi-rules",
        title="Tbilisi tightens residency rules",
        body="New documentation requirements take effect next month.",
        published_at=NOW - timedelta(hours=1),
    ),
    FetchedItem(
        observed_at=NOW - timedelta(minutes=30),
        external_id="wire-3",
        url="https://example.com/patagonia-rain",
        title="Record rainfall in Patagonia",
        body="Meteorologists reported the wettest month on record.",
        published_at=NOW - timedelta(minutes=30),
    ),
)


def gate() -> ExposureGate:
    return ExposureGate(ExposureProfile((NVIDIA, GEORGIA)))


def run_cycle(
    adapter: SourceAdapter,
    deduplicator: Deduplicator,
    *,
    window: FetchWindow | None = None,
    cursor: SourceCursor | None = None,
) -> IngestionReport:
    window = window or FetchWindow(until=NOW, since=NOW - timedelta(days=1))
    batch = collect(adapter, window, clock=CLOCK, cursor=cursor)
    return ingest(
        batch,
        adapter.descriptor,
        deduplicator=deduplicator,
        gate=gate(),
        source_id=SOURCE_ID,
        clock=CLOCK,
    )


# ── the acceptance criterion ────────────────────────────────────────────────


def test_the_same_fixture_ingested_twice_produces_no_duplicates():
    adapter = FixtureAdapter(items=FIXTURE_ITEMS)
    deduplicator = Deduplicator(InMemoryLedger())

    first = run_cycle(adapter, deduplicator)
    second = run_cycle(adapter, deduplicator)

    assert [a.raw_item.title for a in first.admitted] == [
        "Nvidia raises guidance",
        "Tbilisi tightens residency rules",
    ]
    assert second.admitted == ()
    assert second.fetched == 3
    assert len(second.dropped_at(TriageStage.IDEMPOTENCY)) == 3
    assert all("already ingested" in d.explanation for d in second.dropped)


def test_ids_are_derived_from_identity_so_a_replay_writes_the_same_rows():
    first = run_cycle(FixtureAdapter(items=FIXTURE_ITEMS), Deduplicator(InMemoryLedger()))
    replay = run_cycle(FixtureAdapter(items=FIXTURE_ITEMS), Deduplicator(InMemoryLedger()))

    assert [a.raw_item.id for a in first.admitted] == [a.raw_item.id for a in replay.admitted]
    assert [a.raw_item for a in first.admitted] == [a.raw_item for a in replay.admitted]


def test_raw_item_id_is_a_pure_function_of_the_identity():
    identity = (
        run_cycle(FixtureAdapter(items=FIXTURE_ITEMS), Deduplicator(InMemoryLedger()))
        .admitted[0]
        .identity
    )
    assert raw_item_id(identity) == raw_item_id(identity)


# ── what the gate does to the ledger ────────────────────────────────────────


def test_a_gated_item_is_answered_once_not_re_judged_every_cycle():
    """Stage 1 costs nothing, but re-explaining the same rejection daily is noise."""
    adapter = FixtureAdapter(items=FIXTURE_ITEMS)
    deduplicator = Deduplicator(InMemoryLedger())

    first = run_cycle(adapter, deduplicator)
    assert [d.stage for d in first.dropped] == [TriageStage.EXPOSURE]
    assert first.dropped[0].title == "Record rainfall in Patagonia"

    second = run_cycle(adapter, deduplicator)
    assert {d.stage for d in second.dropped} == {TriageStage.IDEMPOTENCY}


# ── the record a cycle leaves ───────────────────────────────────────────────


def test_the_report_counts_the_whole_funnel():
    report = run_cycle(FixtureAdapter(items=FIXTURE_ITEMS), Deduplicator(InMemoryLedger()))
    assert report.counts == {
        "fetched": 3,
        "admitted": 2,
        "dropped": 1,
        "dropped_stage_1_exposure": 1,
    }
    assert report.survival == Decimal("0.67")
    assert report.summary == "fixture: 2 of 3 items admitted"


def test_a_broken_source_does_not_look_like_a_quiet_day():
    adapter = FixtureAdapter(
        items=FIXTURE_ITEMS, failure=SourceUnavailable("fixture", "connection refused")
    )
    report = run_cycle(adapter, Deduplicator(InMemoryLedger()))

    assert report.admitted == ()
    assert report.fetched == 0
    assert report.observed_everything is False
    assert report.completeness is Completeness.UNAVAILABLE
    assert "connection refused" in report.summary


def test_a_quiet_day_is_complete_and_says_so():
    report = run_cycle(FixtureAdapter(items=()), Deduplicator(InMemoryLedger()))
    assert report.admitted == ()
    assert report.observed_everything is True
    assert report.survival == Decimal(0)


def test_run_counts_and_gaps_aggregate_a_whole_cycle():
    working = run_cycle(FixtureAdapter(items=FIXTURE_ITEMS), Deduplicator(InMemoryLedger()))
    broken = run_cycle(
        FixtureAdapter(name="down", failure=SourceUnavailable("down", "502")),
        Deduplicator(InMemoryLedger()),
    )

    totals = run_counts([working, broken])
    assert totals["fetched"] == 3
    assert totals["admitted"] == 2
    assert totals["sources"] == 2
    assert totals["sources_degraded"] == 1

    gaps = run_gaps([working, broken])
    assert len(gaps) == 1
    assert gaps[0].subject == "down"


# ── the raw record itself ───────────────────────────────────────────────────


def test_the_raw_item_preserves_the_artifact_and_fails_high_on_tier():
    item = FetchedItem(
        observed_at=NOW,
        external_id="wire-9",
        url="https://example.com/story?utm_source=x",
        title="Nvidia news",
        body="Body text.",
        payload={"provider": "fixture", "rank": 3},
        declared_tier=SensitivityTier.L2,
    )
    report = run_cycle(FixtureAdapter(items=(item,)), Deduplicator(InMemoryLedger()))
    raw = report.admitted[0].raw_item

    assert raw.canonical_url == "https://example.com/story"
    assert raw.raw_payload == {"provider": "fixture", "rank": 3}
    assert raw.raw_text == "Body text."
    assert raw.ingested_at == NOW
    assert raw.content_hash.startswith("sha256-v1:")
    assert raw.effective_tier is SensitivityTier.L2  # higher of source L1 and item L2


# ── the owner as a source ───────────────────────────────────────────────────


def test_an_owner_submission_bypasses_the_gate_and_stays_l3():
    adapter = ManualSubmissionAdapter()
    adapter.submit(
        OwnerSubmission(
            submitted_at=NOW - timedelta(minutes=5),
            text="Landlord mentioned the lease renews in November",
            note="check this against the residency rules",
        )
    )
    report = run_cycle(adapter, Deduplicator(InMemoryLedger()))

    assert len(report.admitted) == 1
    admitted = report.admitted[0]
    assert admitted.raw_item.effective_tier is SensitivityTier.L3
    assert admitted.why == "you submitted this"
    assert "[owner note] check this" in (admitted.raw_item.raw_text or "")


def test_forwarding_the_same_link_twice_is_one_item():
    adapter = ManualSubmissionAdapter()
    deduplicator = Deduplicator(InMemoryLedger())
    submission = OwnerSubmission(submitted_at=NOW - timedelta(minutes=5), url="https://a.example/x")
    adapter.submit(submission)

    first = run_cycle(adapter, deduplicator)
    adapter.submit(OwnerSubmission(submitted_at=NOW - timedelta(minutes=1), url=submission.url))
    second = run_cycle(adapter, deduplicator)

    assert len(first.admitted) == 1
    assert second.admitted == ()
    assert second.dropped[0].stage is TriageStage.IDEMPOTENCY


def test_a_submission_beyond_the_batch_limit_is_held_not_lost():
    adapter = ManualSubmissionAdapter()
    for minute in range(3):
        adapter.submit(
            OwnerSubmission(submitted_at=NOW - timedelta(minutes=minute + 1), text=f"note {minute}")
        )

    window = FetchWindow(until=NOW, since=NOW - timedelta(days=1), max_items=2)
    report = run_cycle(adapter, Deduplicator(InMemoryLedger()), window=window)

    assert len(report.admitted) == 2
    assert report.completeness is Completeness.PARTIAL
    assert "read next cycle" in report.gaps[0].detail
