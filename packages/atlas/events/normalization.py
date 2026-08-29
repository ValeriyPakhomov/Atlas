"""Turning many reports into one canonical Event.

An Event is not a news item. It is the thing that happened, of which news items are
accounts. Six outlets covering one rate decision produce six Evidence rows and **one**
Event, and the Event's fields are chosen by rule from those accounts rather than by
picking whichever arrived first.

The dedupe key is deliberately narrow: event type, the primary actors, and the calendar
day the thing happened. It is an *exact* key — either two candidates agree on all three or
they do not — because the deterministic spine must never depend on a judgement call
(ADR-0007). Everything looser than that (an entity set that overlaps but does not match,
a timestamp that straddles midnight) is handled by the advisory layer in
:mod:`atlas.events.dedupe`, which proposes rather than decides.

**Which report wins.** When accounts disagree — a different headline, a slightly different
occurrence time — the most reliable source's version is taken, ties broken by whoever
reported first. So a central bank's own wording beats an aggregator's paraphrase of it,
which is the correct default and also the one the owner can check.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from atlas.domain.entities import Event
from atlas.domain.sensitivity import SensitivityTier
from atlas.events.scoring import (
    DEFAULT_SCORING,
    EventScoringPolicy,
    Report,
    credibility,
    novelty,
    urgency,
)

EVENT_KEY_VERSION = "event-key-v1"

#: Fixed namespace for deterministic event ids. Changing it would re-key history.
ATLAS_EVENT_NAMESPACE = UUID("3c2b9d64-9f0a-5e8b-b6d2-4a7c1e5f9033")

ACTIVE = "active"

_TYPE_ALLOWED = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_TYPE_SEPARATORS = re.compile(r"[\s/]+")


def normalise_event_type(value: str) -> str:
    """Fold an event type to its canonical dotted form."""
    folded = _TYPE_SEPARATORS.sub("_", value.strip().casefold())
    if not _TYPE_ALLOWED.match(folded):
        raise ValueError(
            f"event type {value!r} is not canonical; use dotted lowercase segments such as "
            "'monetary_policy.rate_decision'"
        )
    return folded


def normalise_terms(values: Iterable[str]) -> tuple[str, ...]:
    """Canonicalise a term set: folded, deduplicated, sorted.

    Sorting is what makes the key stable — two extractions that named the same actors in a
    different order must produce the same event, not two.
    """
    folded = {" ".join(value.split()).casefold() for value in values}
    return tuple(sorted(term for term in folded if term))


def event_dedupe_key(
    event_type: str, primary_entities: Sequence[str], occurred_at: datetime
) -> str:
    """The exact identity of an event: what kind, to whom, on what day.

    The day bucket is taken in UTC — converting first, rather than reading the date off
    whatever offset the source happened to use, so two accounts of the same instant cannot
    land on different days. It is coarse on purpose. Finer resolution would split one decision
    into several events whenever sources round a timestamp differently; coarser would merge
    two genuinely separate actions by the same actor. Events that straddle midnight are the
    known cost, and are exactly what the advisory layer exists to catch.
    """
    material = "\x1f".join(
        (
            EVENT_KEY_VERSION,
            event_type,
            ",".join(primary_entities),
            occurred_at.astimezone(UTC).date().isoformat(),
        )
    )
    return f"{EVENT_KEY_VERSION}:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


@dataclass(frozen=True, slots=True)
class EventCandidate:
    """One account of something that happened, already extracted and canonical.

    Canonical by construction: the constructor folds the type and every term set, so an
    un-normalised candidate cannot exist and no caller can forget to normalise one.
    """

    event_type: str
    title: str
    occurred_at: datetime
    report: Report
    summary: str = ""
    primary_entities: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    geography: tuple[str, ...] = ()
    sectors: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if not self.title.strip():
            raise ValueError("an event candidate needs a title")
        object.__setattr__(self, "event_type", normalise_event_type(self.event_type))
        object.__setattr__(self, "title", " ".join(self.title.split()))
        object.__setattr__(self, "summary", " ".join(self.summary.split()))
        for field_name in ("primary_entities", "entities", "geography", "sectors", "assets"):
            object.__setattr__(self, field_name, normalise_terms(getattr(self, field_name)))
        if not self.primary_entities:
            raise ValueError(
                "an event candidate must name at least one primary actor; an event with no "
                "actor can be neither deduplicated nor explained"
            )

    @property
    def dedupe_key(self) -> str:
        return event_dedupe_key(self.event_type, self.primary_entities, self.occurred_at)

    @property
    def all_entities(self) -> tuple[str, ...]:
        return normalise_terms((*self.primary_entities, *self.entities))

    @property
    def authority(self) -> tuple[float, datetime, str]:
        """Sort key placing the most reliable, then earliest, account first."""
        return (-float(self.report.reliability), self.report.reported_at, self.report.source_key)


def _union(candidates: Sequence[EventCandidate], attribute: str) -> tuple[str, ...]:
    merged: set[str] = set()
    for candidate in candidates:
        merged.update(getattr(candidate, attribute))
    return tuple(sorted(merged))


def build_event(
    candidates: Sequence[EventCandidate],
    *,
    dedupe_key: str,
    as_of: datetime,
    policy: EventScoringPolicy = DEFAULT_SCORING,
    effective_tier: SensitivityTier = SensitivityTier.L1,
) -> Event:
    """Assemble the canonical Event from every account of it.

    Rebuilt from the full candidate set on every merge rather than patched in place, so the
    result depends only on *which* accounts exist and never on the order they arrived. That
    is what makes a replay reproduce the event graph exactly (A07).
    """
    if not candidates:
        raise ValueError("an event needs at least one candidate")
    ordered = sorted(candidates, key=lambda candidate: candidate.authority)
    authoritative = ordered[0]
    reports = [candidate.report for candidate in ordered]
    by_time = sorted(reports)

    summary = next((candidate.summary for candidate in ordered if candidate.summary), "")
    return Event(
        id=uuid5(ATLAS_EVENT_NAMESPACE, dedupe_key),
        event_type=authoritative.event_type,
        canonical_title=authoritative.title,
        summary=summary,
        occurred_at=authoritative.occurred_at,
        first_reported_at=by_time[0].reported_at,
        last_updated_at=by_time[-1].reported_at,
        credibility_score=credibility(reports, policy=policy),
        novelty_score=novelty(by_time[0].reported_at, as_of=as_of, policy=policy),
        urgency_score=urgency(
            authoritative.event_type, authoritative.occurred_at, as_of=as_of, policy=policy
        ),
        status=ACTIVE,
        dedupe_key=dedupe_key,
        evidence_ids=tuple(report.evidence_id for report in by_time),
        geography=_union(ordered, "geography"),
        entities=_union(ordered, "all_entities"),
        sectors=_union(ordered, "sectors"),
        assets=_union(ordered, "assets"),
        effective_tier=effective_tier,
    )
