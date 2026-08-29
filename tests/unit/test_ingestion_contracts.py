"""Queue 02 — the source adapter contract."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from atlas.domain.clock import FixedClock
from atlas.domain.measurement import Completeness, MissingInput, MissingReason
from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.adapters import FixtureAdapter
from atlas.ingestion.contracts import (
    AdapterDescriptor,
    AdapterFailure,
    CursorRegression,
    FetchBatch,
    FetchedItem,
    FetchWindow,
    SourceAdapter,
    SourceAuthenticationError,
    SourceContractViolation,
    SourceCursor,
    SourceRateLimited,
    SourceUnavailable,
    collect,
)
from atlas.scoring.relevance import SourceClass

NOW = datetime(2026, 8, 29, 9, 0, tzinfo=UTC)
CLOCK = FixedClock(NOW)


def item(**overrides: Any) -> FetchedItem:
    fields: dict[str, Any] = {
        "observed_at": NOW,
        "external_id": "a1",
        "title": "Something happened",
    }
    fields.update(overrides)
    return FetchedItem(**fields)


# ── windows ─────────────────────────────────────────────────────────────────


def test_window_rejects_naive_and_inverted_bounds():
    with pytest.raises(ValueError, match="timezone-aware"):
        FetchWindow(until=datetime(2026, 8, 29, 9, 0))
    with pytest.raises(ValueError, match="must precede"):
        FetchWindow(until=NOW, since=NOW)
    with pytest.raises(ValueError, match="max_items"):
        FetchWindow(until=NOW, max_items=0)


def test_window_includes_undated_items():
    """An item without a timestamp is admitted, not silently dropped."""
    window = FetchWindow(until=NOW, since=NOW - timedelta(days=1))
    assert window.covers(None) is True
    assert window.covers(NOW - timedelta(hours=1)) is True
    assert window.covers(NOW - timedelta(days=2)) is False
    assert window.covers(NOW + timedelta(minutes=1)) is False


def test_window_ending_now_reads_the_injected_clock():
    window = FetchWindow.ending_now(CLOCK, lookback=timedelta(hours=6))
    assert window.until == NOW
    assert window.since == NOW - timedelta(hours=6)


# ── cursors ─────────────────────────────────────────────────────────────────


def test_cursor_refuses_to_move_backwards():
    start = SourceCursor(source_name="fixture", high_water_mark=NOW)
    with pytest.raises(CursorRegression, match="backwards"):
        start.advanced_to(high_water_mark=NOW - timedelta(minutes=1))


def test_cursor_advance_keeps_unspecified_fields():
    start = SourceCursor(source_name="fixture", position="page-2", high_water_mark=NOW)
    moved = start.advanced_to(fetched_through=NOW)
    assert moved.position == "page-2"
    assert moved.high_water_mark == NOW
    assert moved.fetched_through == NOW


# ── items and batches ───────────────────────────────────────────────────────


def test_item_without_any_identifying_content_is_refused():
    with pytest.raises(ValueError, match="cannot be deduplicated"):
        FetchedItem(observed_at=NOW)


def test_item_effective_time_prefers_publication():
    published = NOW - timedelta(hours=3)
    assert item(published_at=published).effective_at == published
    assert item().effective_at == NOW


def test_batch_completeness_invariants_mirror_measured():
    window = FetchWindow(until=NOW)
    cursor = SourceCursor(source_name="fixture")
    gap = MissingInput(subject="fixture", reason=MissingReason.MISSING, detail="down")

    with pytest.raises(ValueError, match="complete fetch cannot name gaps"):
        FetchBatch("fixture", NOW, window, cursor, (item(),), Completeness.COMPLETE, (gap,))
    with pytest.raises(ValueError, match="must say what it missed"):
        FetchBatch("fixture", NOW, window, cursor, (item(),), Completeness.PARTIAL, ())
    with pytest.raises(ValueError, match="unavailable fetch cannot carry items"):
        FetchBatch("fixture", NOW, window, cursor, (item(),), Completeness.UNAVAILABLE, (gap,))


def test_batch_rejects_a_cursor_from_another_source():
    with pytest.raises(ValueError, match="different source"):
        FetchBatch(
            source_name="fixture",
            fetched_at=NOW,
            window=FetchWindow(until=NOW),
            cursor=SourceCursor(source_name="other"),
        )


# ── descriptors ─────────────────────────────────────────────────────────────


def test_descriptor_cannot_declare_write_capability():
    descriptor = AdapterDescriptor(name="x", source_type="rss", source_class=SourceClass.B)
    assert descriptor.write_capable is False


def test_owner_authored_sources_must_be_l3():
    with pytest.raises(ValueError, match="L3"):
        AdapterDescriptor(
            name="owner",
            source_type="manual",
            source_class=SourceClass.A,
            default_tier=SensitivityTier.L1,
            owner_authored=True,
        )


def test_fixture_adapter_satisfies_the_protocol():
    assert isinstance(FixtureAdapter(), SourceAdapter)


# ── failure handling ────────────────────────────────────────────────────────


def test_a_failing_source_becomes_a_measured_gap_not_a_quiet_day():
    adapter = FixtureAdapter(
        items=(item(),), failure=SourceUnavailable("fixture", "connection refused")
    )
    batch = collect(adapter, FetchWindow(until=NOW), clock=CLOCK)

    assert batch.completeness is Completeness.UNAVAILABLE
    assert batch.items == ()
    assert batch.observed_everything is False
    assert "connection refused" in batch.gaps[0].detail
    assert batch.gaps[0].subject == "fixture"


def test_failure_taxonomy_carries_retryability():
    assert SourceRateLimited("x", "429").retryable is True
    assert SourceRateLimited("x", "429").failure is AdapterFailure.RATE_LIMITED
    auth = SourceAuthenticationError("x", "expired key")
    assert auth.retryable is False
    assert auth.as_gap().reason is MissingReason.MISSING


def test_an_atlas_defect_is_not_disguised_as_missing_data():
    """A bug must escape. Only typed adapter failures degrade a batch."""

    class BrokenAdapter:
        @property
        def descriptor(self) -> AdapterDescriptor:
            return AdapterDescriptor(name="broken", source_type="rss", source_class=SourceClass.C)

        def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch:
            raise KeyError("published_at")

    with pytest.raises(KeyError):
        collect(BrokenAdapter(), FetchWindow(until=NOW), clock=CLOCK)


def test_collect_rejects_a_batch_belonging_to_another_source():
    class LyingAdapter:
        @property
        def descriptor(self) -> AdapterDescriptor:
            return AdapterDescriptor(name="honest", source_type="rss", source_class=SourceClass.C)

        def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch:
            return FetchBatch(
                source_name="somewhere-else",
                fetched_at=NOW,
                window=window,
                cursor=SourceCursor(source_name="somewhere-else"),
            )

    with pytest.raises(SourceContractViolation):
        collect(LyingAdapter(), FetchWindow(until=NOW), clock=CLOCK)


# ── fixture adapter behaviour ───────────────────────────────────────────────


def test_fixture_adapter_truncates_loudly():
    items = tuple(
        item(external_id=f"i{n}", observed_at=NOW - timedelta(minutes=n)) for n in range(5)
    )
    batch = FixtureAdapter(items=items).fetch(FetchWindow(until=NOW, max_items=2))

    assert len(batch.items) == 2
    assert batch.completeness is Completeness.PARTIAL
    assert "3 item(s) past the batch limit" in batch.gaps[0].detail
    assert batch.cursor.fetched_through is None  # the window was not finished


def test_fixture_adapter_is_incremental_on_its_cursor():
    items = tuple(item(external_id=f"i{n}", observed_at=NOW - timedelta(hours=n)) for n in range(3))
    adapter = FixtureAdapter(items=items)
    window = FetchWindow(until=NOW)

    first = adapter.fetch(window)
    assert len(first.items) == 3

    second = adapter.fetch(window, first.cursor)
    assert second.items == ()
    assert second.completeness is Completeness.COMPLETE  # quiet, not broken
