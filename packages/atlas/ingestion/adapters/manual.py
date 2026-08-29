"""The owner as a source.

Capture is the primary input action, not an afterthought: a link forwarded at 07:40 must
enter the same pipeline as a wire feed, keep the same provenance, and be answerable in the
same way. What it does *not* do is pass through the exposure gate — the owner sending
something is the strongest possible statement that it is relevant, and a system that
second-guesses that is one the owner stops using.

Everything here is L3 by construction. Owner text may name an employer, a lawyer, a
diagnosis or an account, and Atlas cannot tell in advance. Classification fails high and
is lowered only by an explicit, receipted projection (ADR-0010).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from atlas.domain.measurement import Completeness, MissingInput, MissingReason
from atlas.domain.sensitivity import SensitivityTier
from atlas.ingestion.contracts import (
    AdapterDescriptor,
    FetchBatch,
    FetchedItem,
    FetchWindow,
    SourceCursor,
)
from atlas.scoring.relevance import SourceClass

MANUAL_SOURCE_NAME = "owner"


@dataclass(frozen=True, slots=True)
class OwnerSubmission:
    """Something the owner handed to Atlas, with the time they handed it over."""

    submitted_at: datetime
    text: str = ""
    url: str | None = None
    title: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at must be timezone-aware")
        if not self.text.strip() and not (self.url or "").strip():
            raise ValueError("a submission needs text or a link")

    @property
    def external_id(self) -> str:
        """Stable across resubmission, so forwarding the same link twice is one item."""
        material = f"{(self.url or '').strip()}\x1f{self.text.strip()}"
        return f"manual:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:16]}"

    def to_item(self) -> FetchedItem:
        body = self.text.strip() or None
        if self.note:
            body = f"{body}\n\n[owner note] {self.note}" if body else f"[owner note] {self.note}"
        return FetchedItem(
            observed_at=self.submitted_at,
            external_id=self.external_id,
            url=(self.url or None),
            title=self.title,
            body=body,
            published_at=None,
            payload={"submitted_at": self.submitted_at.isoformat(), "note": self.note or ""},
            declared_tier=SensitivityTier.L3,
        )


@dataclass(slots=True)
class ManualSubmissionAdapter:
    """An in-process queue of owner submissions, drained by the cycle.

    Deliberately not a network client: the API layer accepts a submission and appends it
    here, so capture works offline and the adapter stays a pure function of its contents.
    """

    submissions: list[OwnerSubmission] = field(default_factory=list)

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=MANUAL_SOURCE_NAME,
            source_type="manual",
            source_class=SourceClass.A,
            parse_version="1",
            default_tier=SensitivityTier.L3,
            supports_incremental=True,
            requires_network=False,
            owner_authored=True,
            terms_notes="Owner-authored content. Never leaves the L3 perimeter unprojected.",
        )

    def submit(self, submission: OwnerSubmission) -> None:
        self.submissions.append(submission)

    def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch:
        resume = cursor or SourceCursor(source_name=MANUAL_SOURCE_NAME)
        watermark = resume.high_water_mark
        pending = sorted(
            (
                submission
                for submission in self.submissions
                if window.covers(submission.submitted_at)
                and (watermark is None or submission.submitted_at > watermark)
            ),
            key=lambda submission: (submission.submitted_at, submission.external_id),
        )

        selected = pending[: window.max_items]
        held_back = len(pending) - len(selected)
        items = tuple(submission.to_item() for submission in selected)
        newest = max((s.submitted_at for s in selected), default=None)

        gaps: tuple[MissingInput, ...] = ()
        completeness = Completeness.COMPLETE
        if held_back:
            completeness = Completeness.PARTIAL
            gaps = (
                MissingInput(
                    subject=MANUAL_SOURCE_NAME,
                    reason=MissingReason.MISSING,
                    detail=f"{held_back} submission(s) beyond the batch limit, read next cycle",
                ),
            )

        return FetchBatch(
            source_name=MANUAL_SOURCE_NAME,
            fetched_at=window.until,
            window=window,
            cursor=resume.advanced_to(
                high_water_mark=newest,
                fetched_through=None if held_back else window.until,
            ),
            items=items,
            completeness=completeness,
            gaps=gaps,
        )
