"""ADR-0010 schema/effective classification invariants."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from atlas.domain.sensitivity import (
    ClassifiedValue,
    ProjectionValidation,
    SensitivityTier,
    TierContract,
    TransformationReceipt,
    classify_free_text,
    maximum_tier,
)


def test_combined_value_inherits_maximum_effective_tier() -> None:
    inherited = maximum_tier(SensitivityTier.L0, SensitivityTier.L2, SensitivityTier.L1)
    assert inherited is SensitivityTier.L2


def test_schema_contract_rejects_effective_tier_above_maximum() -> None:
    contract = TierContract(SensitivityTier.L2, SensitivityTier.L1)
    with pytest.raises(ValueError, match="exceeds"):
        ClassifiedValue("private", contract, SensitivityTier.L3)


def test_unknown_personal_free_text_fails_high() -> None:
    contract = TierContract(SensitivityTier.L3, SensitivityTier.L1)
    assert (
        classify_free_text(None, contains_personal_content=True, schema_contract=contract)
        is SensitivityTier.L3
    )


def test_public_free_text_uses_schema_default() -> None:
    contract = TierContract(SensitivityTier.L3, SensitivityTier.L0)
    assert (
        classify_free_text(None, contains_personal_content=False, schema_contract=contract)
        is SensitivityTier.L0
    )


def test_only_validated_l0_l2_projection_receipt_is_constructible() -> None:
    now = datetime(2026, 8, 28, tzinfo=UTC)
    receipt = TransformationReceipt(
        source_ref=uuid4(),
        source_effective_tier=SensitivityTier.L3,
        transformer="allowlist_projection",
        transformer_version="1",
        output_tier=SensitivityTier.L2,
        transformed_at=now,
        validation_result=ProjectionValidation.PASSED,
    )
    assert receipt.output_tier is SensitivityTier.L2

    with pytest.raises(ValueError, match="failed privacy projections"):
        TransformationReceipt(
            source_ref=uuid4(),
            source_effective_tier=SensitivityTier.L3,
            transformer="allowlist_projection",
            transformer_version="1",
            output_tier=SensitivityTier.L2,
            transformed_at=now,
            validation_result=ProjectionValidation.FAILED,
        )
