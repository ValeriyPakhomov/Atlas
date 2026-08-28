"""Queue 01 domain entities.

Only standard-library dataclasses live here. Persistence and validation frameworks stay at
the repository/API boundaries (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from atlas.domain.sensitivity import SensitivityTier


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_interval(valid_from: datetime, valid_to: datetime | None) -> None:
    _require_aware(valid_from, "valid_from")
    if valid_to is not None:
        _require_aware(valid_to, "valid_to")
        if valid_to <= valid_from:
            raise ValueError("valid_to must be later than valid_from")


class AuthoredBy(StrEnum):
    OWNER = "owner"
    ATLAS_PROPOSED = "atlas_proposed"


class ObjectiveDirection(StrEnum):
    ATTAIN = "attain"
    AVOID = "avoid"
    MAINTAIN = "maintain"


class ObjectiveHorizon(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ObjectiveStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"


class PreferenceStrength(StrEnum):
    WEAK = "weak"
    STRONG = "strong"


class PreferenceStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"


class ForecastQuestionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ForecasterType(StrEnum):
    OWNER = "owner"
    ATLAS = "atlas"


@dataclass(frozen=True, slots=True)
class Source:
    id: UUID
    name: str
    source_type: str
    created_at: datetime
    canonical_url: str | None = None
    jurisdiction: str | None = None
    default_reliability: Decimal = Decimal("0.5")
    latency_class: str = "standard"
    terms_notes: str | None = None
    enabled: bool = True
    effective_tier: SensitivityTier = SensitivityTier.L0

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.source_type, "source_type")
        _require_aware(self.created_at, "created_at")
        if not Decimal("0") <= self.default_reliability <= Decimal("1"):
            raise ValueError("default_reliability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class RawItem:
    id: UUID
    source_id: UUID
    observed_at: datetime
    ingested_at: datetime
    content_hash: str
    external_id: str | None = None
    canonical_url: str | None = None
    published_at: datetime | None = None
    title: str | None = None
    raw_text: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    language: str | None = None
    parse_version: str = "1"
    effective_tier: SensitivityTier = SensitivityTier.L3

    def __post_init__(self) -> None:
        _require_aware(self.observed_at, "observed_at")
        _require_aware(self.ingested_at, "ingested_at")
        if self.published_at is not None:
            _require_aware(self.published_at, "published_at")
        _require_non_empty(self.content_hash, "content_hash")
        _require_non_empty(self.parse_version, "parse_version")


@dataclass(frozen=True, slots=True)
class Evidence:
    id: UUID
    raw_item_id: UUID
    proposition: str
    evidence_type: str
    effective_at: datetime
    source_reliability: Decimal
    extraction_confidence: Decimal
    verification_status: str
    entities: tuple[str, ...] = ()
    expires_at: datetime | None = None
    structured_payload: dict[str, Any] = field(default_factory=dict)
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_non_empty(self.proposition, "proposition")
        _require_aware(self.effective_at, "effective_at")
        if self.expires_at is not None:
            _require_aware(self.expires_at, "expires_at")
        for name, value in (
            ("source_reliability", self.source_reliability),
            ("extraction_confidence", self.extraction_confidence),
        ):
            if not Decimal("0") <= value <= Decimal("1"):
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Event:
    id: UUID
    event_type: str
    canonical_title: str
    summary: str
    occurred_at: datetime
    first_reported_at: datetime
    last_updated_at: datetime
    credibility_score: Decimal
    novelty_score: Decimal
    urgency_score: Decimal
    status: str
    dedupe_key: str
    evidence_ids: tuple[UUID, ...] = ()
    geography: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    sectors: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_non_empty(self.canonical_title, "canonical_title")
        for name, instant in (
            ("occurred_at", self.occurred_at),
            ("first_reported_at", self.first_reported_at),
            ("last_updated_at", self.last_updated_at),
        ):
            _require_aware(instant, name)
        for name, score in (
            ("credibility_score", self.credibility_score),
            ("novelty_score", self.novelty_score),
            ("urgency_score", self.urgency_score),
        ):
            if not Decimal("0") <= score <= Decimal("1"):
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Narrative:
    id: UUID
    slug: str
    title: str
    description: str
    category: str
    status: str
    direction: str
    strength: Decimal
    confidence: Decimal
    first_seen_at: datetime
    last_changed_at: datetime
    last_confirmed_at: datetime
    event_ids: tuple[UUID, ...] = ()
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_non_empty(self.slug, "slug")
        _require_non_empty(self.title, "title")
        for name, instant in (
            ("first_seen_at", self.first_seen_at),
            ("last_changed_at", self.last_changed_at),
            ("last_confirmed_at", self.last_confirmed_at),
        ):
            _require_aware(instant, name)
        for name, score in (("strength", self.strength), ("confidence", self.confidence)):
            if not Decimal("0") <= score <= Decimal("1"):
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: UUID
    as_of: datetime
    source_results: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    model_calls: tuple[dict[str, Any], ...] = ()
    cost: Decimal = Decimal("0")
    latency_ms: int = 0
    deltas_created: int = 0
    alerts_emitted: int = 0
    missing_critical_data: tuple[str, ...] = ()
    errors: tuple[dict[str, Any], ...] = ()
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_aware(self.as_of, "as_of")
        if self.cost < 0 or self.latency_ms < 0:
            raise ValueError("run cost and latency cannot be negative")


@dataclass(frozen=True, slots=True)
class Objective:
    id: UUID
    owner_id: UUID
    title: str
    description: str
    category_key: str
    direction: ObjectiveDirection
    horizon: ObjectiveHorizon
    priority: int
    status: ObjectiveStatus
    authored_by: AuthoredBy
    valid_from: datetime
    target_date: date | None = None
    target_value: Decimal | None = None
    target_currency: str | None = None
    accepted_at: datetime | None = None
    valid_to: datetime | None = None
    effective_tier: SensitivityTier = SensitivityTier.L2

    def __post_init__(self) -> None:
        _require_non_empty(self.title, "title")
        _require_non_empty(self.category_key, "category_key")
        _validate_interval(self.valid_from, self.valid_to)
        if self.accepted_at is not None:
            _require_aware(self.accepted_at, "accepted_at")
        if self.status is ObjectiveStatus.ACTIVE and self.accepted_at is None:
            raise ValueError("an active objective must be accepted by the owner")
        if self.target_currency is not None and (
            len(self.target_currency) != 3 or not self.target_currency.isalpha()
        ):
            raise ValueError("target_currency must be a 3-letter code")


@dataclass(frozen=True, slots=True)
class Preference:
    id: UUID
    owner_id: UUID
    higher_objective_id: UUID
    lower_objective_id: UUID
    strength: PreferenceStrength
    rationale: str
    authored_by: AuthoredBy
    status: PreferenceStatus
    valid_from: datetime
    accepted_at: datetime | None = None
    valid_to: datetime | None = None
    effective_tier: SensitivityTier = SensitivityTier.L2

    def __post_init__(self) -> None:
        if self.higher_objective_id == self.lower_objective_id:
            raise ValueError("a preference cannot rank an objective against itself")
        _validate_interval(self.valid_from, self.valid_to)
        if self.accepted_at is not None:
            _require_aware(self.accepted_at, "accepted_at")
        if self.status is PreferenceStatus.ACTIVE and self.accepted_at is None:
            raise ValueError("an active preference must be accepted by the owner")


@dataclass(frozen=True, slots=True)
class ForecastQuestion:
    id: UUID
    question: str
    domain_key: str
    resolution_criteria: str
    resolve_by: datetime
    created_at: datetime
    status: ForecastQuestionStatus = ForecastQuestionStatus.OPEN
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_non_empty(self.question, "question")
        _require_non_empty(self.domain_key, "domain_key")
        _require_non_empty(self.resolution_criteria, "resolution_criteria")
        _require_aware(self.resolve_by, "resolve_by")
        _require_aware(self.created_at, "created_at")
        if self.resolve_by <= self.created_at:
            raise ValueError("resolve_by must be later than created_at")


@dataclass(frozen=True, slots=True)
class ForecastPrediction:
    id: UUID
    question_id: UUID
    forecaster_type: ForecasterType
    probability: Decimal
    made_at: datetime
    model_ref: str | None = None
    prompt_or_artifact_version_refs: tuple[str, ...] = ()
    evidence_refs: tuple[UUID, ...] = ()
    note: str | None = None
    supersedes_prediction_id: UUID | None = None
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_aware(self.made_at, "made_at")
        if not Decimal("0") <= self.probability <= Decimal("1"):
            raise ValueError("forecast probability must be between 0 and 1")
        if self.forecaster_type is ForecasterType.ATLAS and not self.model_ref:
            raise ValueError("Atlas predictions require model_ref")
        if self.forecaster_type is ForecasterType.OWNER and self.model_ref is not None:
            raise ValueError("owner predictions cannot carry model_ref")
        if self.supersedes_prediction_id == self.id:
            raise ValueError("a prediction cannot supersede itself")


@dataclass(frozen=True, slots=True)
class ForecastResolution:
    question_id: UUID
    outcome: bool
    resolved_at: datetime
    evidence_refs: tuple[UUID, ...]
    resolution_note: str | None = None
    effective_tier: SensitivityTier = SensitivityTier.L1

    def __post_init__(self) -> None:
        _require_aware(self.resolved_at, "resolved_at")
        if not self.evidence_refs:
            raise ValueError("forecast resolution requires evidence provenance")
