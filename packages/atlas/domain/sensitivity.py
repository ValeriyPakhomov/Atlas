"""Sensitivity primitives shared by every Atlas domain record (ADR-0010)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SensitivityTier(StrEnum):
    """Ordered data-sensitivity tiers."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"

    @property
    def rank(self) -> int:
        return int(self.value[1])


def maximum_tier(*tiers: SensitivityTier) -> SensitivityTier:
    """Return the effective tier inherited by a combined value."""

    if not tiers:
        raise ValueError("at least one sensitivity tier is required")
    return max(tiers, key=lambda tier: tier.rank)


@dataclass(frozen=True, slots=True)
class TierContract:
    """Schema-level maximum/default classification for a persisted field."""

    schema_max_tier: SensitivityTier
    schema_default_tier: SensitivityTier

    def __post_init__(self) -> None:
        if self.schema_default_tier.rank > self.schema_max_tier.rank:
            raise ValueError("schema default tier cannot exceed schema maximum tier")

    def validate(self, effective_tier: SensitivityTier) -> None:
        if effective_tier.rank > self.schema_max_tier.rank:
            raise ValueError("effective tier exceeds schema maximum tier")


@dataclass(frozen=True, slots=True)
class ClassifiedValue[T]:
    """A value carrying both its schema contract and actual classification."""

    value: T
    contract: TierContract
    effective_tier: SensitivityTier

    def __post_init__(self) -> None:
        self.contract.validate(self.effective_tier)


def classify_free_text(
    explicit_tier: SensitivityTier | None,
    *,
    contains_personal_content: bool,
    schema_contract: TierContract,
) -> SensitivityTier:
    """Classify mixed free text, failing unknown personal content high to L3."""

    if explicit_tier is None:
        effective = (
            SensitivityTier.L3 if contains_personal_content else schema_contract.schema_default_tier
        )
    else:
        effective = explicit_tier
    schema_contract.validate(effective)
    return effective


class ProjectionValidation(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TransformationReceipt:
    """Provenance for a deterministic privacy projection."""

    source_ref: UUID
    source_effective_tier: SensitivityTier
    transformer: str
    transformer_version: str
    output_tier: SensitivityTier
    transformed_at: datetime
    validation_result: ProjectionValidation

    def __post_init__(self) -> None:
        if self.transformed_at.tzinfo is None:
            raise ValueError("transformation time must be timezone-aware")
        if not self.transformer.strip() or not self.transformer_version.strip():
            raise ValueError("transformer and version are required")
        if self.output_tier.rank > SensitivityTier.L2.rank:
            raise ValueError("privacy projection output must be externally routable L0-L2")
        if self.validation_result is not ProjectionValidation.PASSED:
            raise ValueError("failed privacy projections cannot produce a receipt")
