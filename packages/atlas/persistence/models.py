"""Queue 01 SQLAlchemy mappings.

Every column declares schema maximum/default sensitivity metadata. Mixed-content records
also store an effective tier used by routing and provenance (ADR-0010).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column

from atlas.domain.entities import (
    AuthoredBy,
    ForecasterType,
    ForecastQuestionStatus,
    ObjectiveDirection,
    ObjectiveHorizon,
    ObjectiveStatus,
    PreferenceStatus,
    PreferenceStrength,
)
from atlas.domain.sensitivity import SensitivityTier

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def tier_info(
    schema_max_tier: SensitivityTier,
    schema_default_tier: SensitivityTier,
) -> dict[str, str]:
    if schema_default_tier.rank > schema_max_tier.rank:
        raise ValueError("schema default tier cannot exceed schema maximum tier")
    return {
        "schema_max_tier": schema_max_tier.value,
        "schema_default_tier": schema_default_tier.value,
    }


def tiered_column(
    *args: Any,
    schema_max_tier: SensitivityTier,
    schema_default_tier: SensitivityTier,
    **kwargs: Any,
) -> MappedColumn[Any]:
    info = dict(kwargs.pop("info", {}))
    info.update(tier_info(schema_max_tier, schema_default_tier))
    return mapped_column(*args, info=info, **kwargs)


def tiered_sa_column(
    name: str,
    *args: Any,
    schema_max_tier: SensitivityTier,
    schema_default_tier: SensitivityTier,
    **kwargs: Any,
) -> Column[Any]:
    return Column(
        name,
        *args,
        info=tier_info(schema_max_tier, schema_default_tier),
        **kwargs,
    )


SENSITIVITY_ENUM = Enum(
    SensitivityTier,
    name="sensitivity_tier",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
)


class EffectiveTierMixin:
    effective_tier: Mapped[SensitivityTier] = tiered_column(
        SENSITIVITY_ENUM,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
        nullable=False,
    )


class SourceModel(EffectiveTierMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(
            "default_reliability >= 0 AND default_reliability <= 1",
            name="default_reliability_bounds",
        ),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L0,
        schema_default_tier=SensitivityTier.L0,
    )
    name: Mapped[str] = tiered_column(
        String(200), schema_max_tier=SensitivityTier.L0, schema_default_tier=SensitivityTier.L0
    )
    source_type: Mapped[str] = tiered_column(
        String(80), schema_max_tier=SensitivityTier.L0, schema_default_tier=SensitivityTier.L0
    )
    canonical_url: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L0,
        schema_default_tier=SensitivityTier.L0,
    )
    jurisdiction: Mapped[str | None] = tiered_column(
        String(32),
        nullable=True,
        schema_max_tier=SensitivityTier.L0,
        schema_default_tier=SensitivityTier.L0,
    )
    default_reliability: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    latency_class: Mapped[str] = tiered_column(
        String(40), schema_max_tier=SensitivityTier.L0, schema_default_tier=SensitivityTier.L0
    )
    terms_notes: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L0,
        schema_default_tier=SensitivityTier.L0,
    )
    enabled: Mapped[bool] = tiered_column(
        Boolean, schema_max_tier=SensitivityTier.L0, schema_default_tier=SensitivityTier.L0
    )
    created_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L0,
        schema_default_tier=SensitivityTier.L0,
    )


class RawItemModel(EffectiveTierMixin, Base):
    __tablename__ = "raw_items"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="source_external_id"),)

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    source_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    external_id: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    canonical_url: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    published_at: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    observed_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    ingested_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    title: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    raw_text: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L3,
    )
    raw_payload: Mapped[dict[str, Any]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L3
    )
    content_hash: Mapped[str] = tiered_column(
        String(128),
        unique=True,
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    language: Mapped[str | None] = tiered_column(
        String(16),
        nullable=True,
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    parse_version: Mapped[str] = tiered_column(
        String(80), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )


class EvidenceModel(EffectiveTierMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            "source_reliability >= 0 AND source_reliability <= 1",
            name="source_reliability_bounds",
        ),
        CheckConstraint(
            "extraction_confidence >= 0 AND extraction_confidence <= 1",
            name="extraction_confidence_bounds",
        ),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    raw_item_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("raw_items.id", ondelete="RESTRICT"),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    proposition: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    evidence_type: Mapped[str] = tiered_column(
        String(80), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    entities: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    effective_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    expires_at: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    source_reliability: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    extraction_confidence: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    verification_status: Mapped[str] = tiered_column(
        String(40), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    structured_payload: Mapped[dict[str, Any]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )


class EventModel(EffectiveTierMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("credibility_score BETWEEN 0 AND 1", name="credibility_bounds"),
        CheckConstraint("novelty_score BETWEEN 0 AND 1", name="novelty_bounds"),
        CheckConstraint("urgency_score BETWEEN 0 AND 1", name="urgency_bounds"),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    event_type: Mapped[str] = tiered_column(
        String(80), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    canonical_title: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    summary: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    occurred_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    first_reported_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    last_updated_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    geography: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    entities: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    sectors: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    assets: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    credibility_score: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    novelty_score: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    urgency_score: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    status: Mapped[str] = tiered_column(
        String(40), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    dedupe_key: Mapped[str] = tiered_column(
        String(128),
        unique=True,
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )


event_evidence = Table(
    "event_evidence",
    Base.metadata,
    tiered_sa_column(
        "event_id",
        PGUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
    tiered_sa_column(
        "evidence_id",
        PGUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="RESTRICT"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
)


class NarrativeModel(EffectiveTierMixin, Base):
    __tablename__ = "narratives"
    __table_args__ = (
        CheckConstraint("strength BETWEEN 0 AND 1", name="strength_bounds"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_bounds"),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    slug: Mapped[str] = tiered_column(
        String(160),
        unique=True,
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    title: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    description: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    category: Mapped[str] = tiered_column(
        String(80), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    status: Mapped[str] = tiered_column(
        String(40), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    direction: Mapped[str] = tiered_column(
        String(40), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    strength: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    confidence: Mapped[Decimal] = tiered_column(
        Numeric(5, 4), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    first_seen_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    last_changed_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    last_confirmed_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )


narrative_events = Table(
    "narrative_events",
    Base.metadata,
    tiered_sa_column(
        "narrative_id",
        PGUUID(as_uuid=True),
        ForeignKey("narratives.id", ondelete="CASCADE"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
    tiered_sa_column(
        "event_id",
        PGUUID(as_uuid=True),
        ForeignKey("events.id", ondelete="RESTRICT"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
)


class RunRecordModel(EffectiveTierMixin, Base):
    __tablename__ = "run_records"
    __table_args__ = (
        CheckConstraint("cost >= 0", name="cost_nonnegative"),
        CheckConstraint("latency_ms >= 0", name="latency_nonnegative"),
    )

    run_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    as_of: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    source_results: Mapped[dict[str, Any]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    counts: Mapped[dict[str, int]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    model_calls: Mapped[list[dict[str, Any]]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    cost: Mapped[Decimal] = tiered_column(
        Numeric(14, 6), schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    latency_ms: Mapped[int] = tiered_column(
        Integer, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    deltas_created: Mapped[int] = tiered_column(
        Integer, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    alerts_emitted: Mapped[int] = tiered_column(
        Integer, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    missing_critical_data: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    errors: Mapped[list[dict[str, Any]]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )


class ObjectiveModel(EffectiveTierMixin, Base):
    __tablename__ = "objectives"
    __table_args__ = (
        CheckConstraint("priority >= 0", name="priority_nonnegative"),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="valid_interval"),
        CheckConstraint(
            "status <> 'ACTIVE' OR accepted_at IS NOT NULL", name="active_requires_acceptance"
        ),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    owner_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    title: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L2
    )
    description: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L2
    )
    category_key: Mapped[str] = tiered_column(
        String(100), schema_max_tier=SensitivityTier.L2, schema_default_tier=SensitivityTier.L2
    )
    direction: Mapped[ObjectiveDirection] = tiered_column(
        Enum(ObjectiveDirection, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    horizon: Mapped[ObjectiveHorizon] = tiered_column(
        Enum(ObjectiveHorizon, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    target_date: Mapped[date | None] = tiered_column(
        Date,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    target_value: Mapped[Decimal | None] = tiered_column(
        Numeric(24, 8),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    target_currency: Mapped[str | None] = tiered_column(
        String(3),
        nullable=True,
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    priority: Mapped[int] = tiered_column(
        Integer, schema_max_tier=SensitivityTier.L2, schema_default_tier=SensitivityTier.L2
    )
    status: Mapped[ObjectiveStatus] = tiered_column(
        Enum(ObjectiveStatus, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    authored_by: Mapped[AuthoredBy] = tiered_column(
        Enum(AuthoredBy, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    accepted_at: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    valid_from: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    valid_to: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )


class PreferenceModel(EffectiveTierMixin, Base):
    __tablename__ = "preferences"
    __table_args__ = (
        CheckConstraint("higher_objective_id <> lower_objective_id", name="different_objectives"),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="valid_interval"),
        CheckConstraint(
            "status <> 'ACTIVE' OR accepted_at IS NOT NULL", name="active_requires_acceptance"
        ),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    owner_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    higher_objective_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("objectives.id", ondelete="RESTRICT"),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    lower_objective_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("objectives.id", ondelete="RESTRICT"),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    strength: Mapped[PreferenceStrength] = tiered_column(
        Enum(PreferenceStrength, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    rationale: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L2
    )
    authored_by: Mapped[AuthoredBy] = tiered_column(
        Enum(AuthoredBy, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    accepted_at: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    status: Mapped[PreferenceStatus] = tiered_column(
        Enum(PreferenceStatus, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L2,
    )
    valid_from: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )
    valid_to: Mapped[datetime | None] = tiered_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L2,
    )


class ForecastQuestionModel(EffectiveTierMixin, Base):
    __tablename__ = "forecast_questions"
    __table_args__ = (
        CheckConstraint("length(trim(resolution_criteria)) > 0", name="criteria_required"),
        CheckConstraint("resolve_by > created_at", name="resolve_after_creation"),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    question: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    domain_key: Mapped[str] = tiered_column(
        String(100), schema_max_tier=SensitivityTier.L2, schema_default_tier=SensitivityTier.L1
    )
    resolution_criteria: Mapped[str] = tiered_column(
        Text, schema_max_tier=SensitivityTier.L3, schema_default_tier=SensitivityTier.L1
    )
    resolve_by: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    created_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    status: Mapped[ForecastQuestionStatus] = tiered_column(
        Enum(ForecastQuestionStatus, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )


class ForecastPredictionModel(EffectiveTierMixin, Base):
    __tablename__ = "forecast_predictions"
    __table_args__ = (
        CheckConstraint("probability >= 0 AND probability <= 1", name="probability_bounds"),
        CheckConstraint(
            "(forecaster_type = 'ATLAS' AND model_ref IS NOT NULL) OR "
            "(forecaster_type = 'OWNER' AND model_ref IS NULL)",
            name="model_ref_matches_forecaster",
        ),
        CheckConstraint(
            "supersedes_prediction_id IS NULL OR supersedes_prediction_id <> id",
            name="does_not_supersede_self",
        ),
    )

    id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    question_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("forecast_questions.id", ondelete="RESTRICT"),
        index=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    forecaster_type: Mapped[ForecasterType] = tiered_column(
        Enum(ForecasterType, native_enum=False, create_constraint=True),
        schema_max_tier=SensitivityTier.L2,
        schema_default_tier=SensitivityTier.L1,
    )
    probability: Mapped[Decimal] = tiered_column(
        Numeric(7, 6), schema_max_tier=SensitivityTier.L2, schema_default_tier=SensitivityTier.L1
    )
    made_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    model_ref: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L1,
        schema_default_tier=SensitivityTier.L1,
    )
    prompt_or_artifact_version_refs: Mapped[list[str]] = tiered_column(
        JSONB, schema_max_tier=SensitivityTier.L1, schema_default_tier=SensitivityTier.L1
    )
    note: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    supersedes_prediction_id: Mapped[UUID | None] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("forecast_predictions.id", ondelete="RESTRICT"),
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )


forecast_prediction_evidence = Table(
    "forecast_prediction_evidence",
    Base.metadata,
    tiered_sa_column(
        "prediction_id",
        PGUUID(as_uuid=True),
        ForeignKey("forecast_predictions.id", ondelete="CASCADE"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
    tiered_sa_column(
        "evidence_id",
        PGUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="RESTRICT"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
)


class ForecastResolutionModel(EffectiveTierMixin, Base):
    __tablename__ = "forecast_resolutions"

    question_id: Mapped[UUID] = tiered_column(
        PGUUID(as_uuid=True),
        ForeignKey("forecast_questions.id", ondelete="RESTRICT"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    outcome: Mapped[bool] = tiered_column(
        Boolean, schema_max_tier=SensitivityTier.L2, schema_default_tier=SensitivityTier.L1
    )
    resolved_at: Mapped[datetime] = tiered_column(
        DateTime(timezone=True),
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )
    resolution_note: Mapped[str | None] = tiered_column(
        Text,
        nullable=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    )


forecast_resolution_evidence = Table(
    "forecast_resolution_evidence",
    Base.metadata,
    tiered_sa_column(
        "question_id",
        PGUUID(as_uuid=True),
        ForeignKey("forecast_resolutions.question_id", ondelete="CASCADE"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
    tiered_sa_column(
        "evidence_id",
        PGUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="RESTRICT"),
        primary_key=True,
        schema_max_tier=SensitivityTier.L3,
        schema_default_tier=SensitivityTier.L1,
    ),
)
