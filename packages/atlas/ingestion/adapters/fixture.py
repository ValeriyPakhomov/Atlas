"""A source made of fixed items.

Not only a test double. A07 requires that replay and live share one engine, which is only
enforceable if a historical window can be re-read exactly as it was first read. This
adapter is the mechanism: give it the items a provider returned on 2026-03-11, hand the
cycle a :class:`~atlas.domain.clock.FixedClock`, and the run is reproducible to the byte.

It also models the two behaviours real providers have that break naive pipelines — a
batch limit that truncates a window, and a typed failure — so those paths are exercised
before a network adapter meets them in production.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.domain.measurement import Completeness, MissingInput, MissingReason
from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.contracts import (
    AdapterDescriptor,
    AdapterError,
    FetchBatch,
    FetchedItem,
    FetchWindow,
    SourceCursor,
)
from atlas.scoring.relevance import SourceClass


@dataclass(slots=True)
class FixtureAdapter:
    """Replays a fixed item set, honouring the window, the cursor and the batch limit."""

    name: str = "fixture"
    items: tuple[FetchedItem, ...] = ()
    source_class: SourceClass = SourceClass.B
    source_type: str = "fixture"
    parse_version: str = "1"
    default_tier: SensitivityTier = SensitivityTier.L1
    failure: AdapterError | None = None
    calls: int = field(default=0, init=False)

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.name,
            source_type=self.source_type,
            source_class=self.source_class,
            parse_version=self.parse_version,
            default_tier=self.default_tier,
            supports_incremental=True,
            requires_network=False,
        )

    def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch:
        self.calls += 1
        if self.failure is not None:
            raise self.failure

        resume = cursor or SourceCursor(source_name=self.name)
        watermark = resume.high_water_mark
        eligible = sorted(
            (
                item
                for item in self.items
                if window.covers(item.effective_at)
                and (watermark is None or item.effective_at > watermark)
            ),
            key=lambda item: (item.effective_at, item.external_id or "", item.title or ""),
        )

        selected = tuple(eligible[: window.max_items])
        truncated = len(eligible) - len(selected)
        newest = max((item.effective_at for item in selected), default=None)

        gaps: tuple[MissingInput, ...] = ()
        completeness = Completeness.COMPLETE
        if truncated:
            completeness = Completeness.PARTIAL
            gaps = (
                MissingInput(
                    subject=self.name,
                    reason=MissingReason.MISSING,
                    detail=f"{truncated} item(s) past the batch limit of {window.max_items}",
                ),
            )

        return FetchBatch(
            source_name=self.name,
            fetched_at=window.until,
            window=window,
            cursor=resume.advanced_to(
                position=selected[-1].external_id if selected else None,
                high_water_mark=newest,
                fetched_through=None if truncated else window.until,
            ),
            items=selected,
            completeness=completeness,
            gaps=gaps,
        )
