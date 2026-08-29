"""One source, one window, one auditable pass through stages 0 and 1.

The pipeline is where the funnel becomes a record. It fetches, computes identity, drops
what has already been seen, gates what the owner has no exposure to, and turns the
survivors into :class:`~atlas.domain.entities.RawItem` rows — while keeping, for every
item it removed, the sentence explaining why.

Two properties are worth stating outright because the rest of the system leans on them:

**Ingesting the same batch twice changes nothing.** Item ids are ``uuid5`` of the
deterministic identity key, so a re-run produces the *same* primary keys rather than new
rows that later have to be reconciled. Replay, backfill and a retried cycle are all the
same operation.

**A quiet day and a broken day look different.** The report carries the fetch's
completeness and gaps, so "nothing happened" and "the source was down" never collapse into
the same empty list (A06).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid5

from atlas.domain.clock import Clock
from atlas.domain.entities import RawItem
from atlas.domain.measurement import Completeness, MissingInput
from atlas.domain.sensitivity import maximum_tier
from atlas.ingestion.contracts import (
    AdapterDescriptor,
    FetchBatch,
    FetchedItem,
    FetchWindow,
    SourceCursor,
)
from atlas.ingestion.idempotency import Deduplicator, ItemIdentity, canonical_url, identify
from atlas.ingestion.triage import ExposureGate, TriageDecision, TriageStage

#: Fixed namespace for deterministic raw-item ids. Changing it would re-key history, so
#: it is a constant, not configuration.
ATLAS_ITEM_NAMESPACE = UUID("6f1d4d1a-2f77-5c4e-9a1b-0f3f8a2c7e11")


def raw_item_id(identity: ItemIdentity) -> UUID:
    """A stable id for an item, derived from its identity rather than from chance."""
    return uuid5(ATLAS_ITEM_NAMESPACE, identity.primary_key)


def to_raw_item(
    item: FetchedItem,
    identity: ItemIdentity,
    descriptor: AdapterDescriptor,
    *,
    source_id: UUID,
    ingested_at: datetime,
) -> RawItem:
    """Map an adapter's artifact onto the persisted raw record, verbatim.

    Nothing is interpreted here. The sensitivity tier is the *higher* of what the source
    declares and what the item declares: classification fails high, always (ADR-0010).
    """
    return RawItem(
        id=raw_item_id(identity),
        source_id=source_id,
        observed_at=item.observed_at,
        ingested_at=ingested_at,
        content_hash=identity.storage_hash,
        external_id=item.external_id,
        canonical_url=canonical_url(item.url),
        published_at=item.published_at,
        title=item.title,
        raw_text=item.body,
        raw_payload=dict(item.payload),
        language=item.language,
        parse_version=identity.parse_version,
        effective_tier=maximum_tier(descriptor.default_tier, item.declared_tier),
    )


@dataclass(frozen=True, slots=True)
class AdmittedItem:
    """An item that survived the funnel, with the reason it did."""

    raw_item: RawItem
    identity: ItemIdentity
    decision: TriageDecision

    @property
    def why(self) -> str:
        return self.decision.explanation


@dataclass(frozen=True, slots=True)
class DroppedItem:
    """An item that did not survive — kept, because the reason is the product."""

    ref: str
    stage: TriageStage
    explanation: str
    title: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """What one source contributed to one cycle, and what it cost nothing to reject."""

    source_name: str
    window: FetchWindow
    cursor: SourceCursor
    fetched: int
    admitted: tuple[AdmittedItem, ...] = ()
    dropped: tuple[DroppedItem, ...] = ()
    completeness: Completeness = Completeness.COMPLETE
    gaps: tuple[MissingInput, ...] = ()

    @property
    def observed_everything(self) -> bool:
        return self.completeness is Completeness.COMPLETE

    def dropped_at(self, stage: TriageStage) -> tuple[DroppedItem, ...]:
        return tuple(item for item in self.dropped if item.stage is stage)

    @property
    def counts(self) -> dict[str, int]:
        """Funnel counts, shaped for ``RunRecord.counts``."""
        counts = {
            "fetched": self.fetched,
            "admitted": len(self.admitted),
            "dropped": len(self.dropped),
        }
        for stage in TriageStage:
            dropped = len(self.dropped_at(stage))
            if dropped:
                counts[f"dropped_{stage}"] = dropped
        return counts

    @property
    def survival(self) -> Decimal:
        """Share of fetched items that reached extraction, to two places."""
        if self.fetched == 0:
            return Decimal(0)
        return (Decimal(len(self.admitted)) / Decimal(self.fetched)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )

    @property
    def summary(self) -> str:
        head = f"{self.source_name}: {len(self.admitted)} of {self.fetched} items admitted"
        if self.observed_everything:
            return head
        return f"{head} — incomplete: " + "; ".join(str(gap) for gap in self.gaps)


def ingest(
    batch: FetchBatch,
    descriptor: AdapterDescriptor,
    *,
    deduplicator: Deduplicator,
    gate: ExposureGate,
    source_id: UUID,
    clock: Clock,
) -> IngestionReport:
    """Run stages 0 and 1 over a fetched batch.

    Order matters and is not an implementation detail: identity is checked before the
    exposure gate because it is cheaper and because a duplicate must be reported as a
    duplicate. If the gate ran first, an item already ingested last night would be
    re-explained as "no exposure" every time it reappeared, which is both wrong and
    confusing in the Reading Room.
    """
    ingested_at = clock.now()
    admitted: list[AdmittedItem] = []
    dropped: list[DroppedItem] = []

    for item in batch.items:
        identity = identify(item, descriptor)
        ref = str(raw_item_id(identity))
        verdict = deduplicator.classify(identity)
        if not verdict.is_new:
            dropped.append(
                DroppedItem(
                    ref=ref,
                    stage=TriageStage.IDEMPOTENCY,
                    explanation=verdict.explanation,
                    title=item.title,
                )
            )
            continue

        decision = gate.evaluate(item, descriptor, item_ref=ref)
        if not decision.admitted:
            # Still admitted to the ledger: a gated item is *seen*, and re-evaluating it
            # every cycle would pay stage 1 forever for an item already answered.
            deduplicator.admit(identity, ref)
            dropped.append(
                DroppedItem(
                    ref=ref,
                    stage=decision.stopped_at or TriageStage.EXPOSURE,
                    explanation=decision.explanation,
                    title=item.title,
                )
            )
            continue

        deduplicator.admit(identity, ref)
        admitted.append(
            AdmittedItem(
                raw_item=to_raw_item(
                    item,
                    identity,
                    descriptor,
                    source_id=source_id,
                    ingested_at=ingested_at,
                ),
                identity=identity,
                decision=decision,
            )
        )

    return IngestionReport(
        source_name=batch.source_name,
        window=batch.window,
        cursor=batch.cursor,
        fetched=len(batch.items),
        admitted=tuple(admitted),
        dropped=tuple(dropped),
        completeness=batch.completeness,
        gaps=batch.gaps,
    )


def run_counts(reports: Sequence[IngestionReport]) -> dict[str, int]:
    """Aggregate funnel counts across a cycle, for ``RunRecord.counts``."""
    totals: dict[str, int] = {}
    for report in reports:
        for key, value in report.counts.items():
            totals[key] = totals.get(key, 0) + value
    totals["sources"] = len(reports)
    totals["sources_degraded"] = sum(1 for report in reports if not report.observed_everything)
    return totals


def run_gaps(reports: Iterable[IngestionReport]) -> tuple[MissingInput, ...]:
    """Every gap a cycle observed, deduplicated and ordered for the brief."""
    seen: dict[tuple[str, str, str], MissingInput] = {}
    for report in reports:
        for gap in report.gaps:
            seen.setdefault((gap.subject, gap.reason, gap.detail), gap)
    return tuple(sorted(seen.values()))
