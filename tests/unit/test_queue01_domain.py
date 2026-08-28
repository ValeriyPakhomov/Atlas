"""Queue 01 framework-neutral domain validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from atlas.domain.entities import (
    AuthoredBy,
    ForecasterType,
    ForecastPrediction,
    ForecastQuestion,
    ForecastResolution,
    Objective,
    ObjectiveDirection,
    ObjectiveHorizon,
    ObjectiveStatus,
    Preference,
    PreferenceStatus,
    PreferenceStrength,
    RawItem,
)
from atlas.domain.sensitivity import SensitivityTier

NOW = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


def test_mixed_raw_item_fails_high_by_default() -> None:
    item = RawItem(
        id=uuid4(),
        source_id=uuid4(),
        observed_at=NOW,
        ingested_at=NOW,
        content_hash="synthetic-hash",
        raw_text="unclassified free text",
    )
    assert item.effective_tier is SensitivityTier.L3


def test_active_objective_requires_owner_acceptance() -> None:
    with pytest.raises(ValueError, match="accepted"):
        Objective(
            id=uuid4(),
            owner_id=uuid4(),
            title="Maintain runway",
            description="Synthetic objective",
            category_key="resilience",
            direction=ObjectiveDirection.MAINTAIN,
            horizon=ObjectiveHorizon.MEDIUM,
            priority=1,
            status=ObjectiveStatus.ACTIVE,
            authored_by=AuthoredBy.ATLAS_PROPOSED,
            valid_from=NOW,
        )


def test_preference_cannot_rank_objective_against_itself() -> None:
    objective_id = uuid4()
    with pytest.raises(ValueError, match="against itself"):
        Preference(
            id=uuid4(),
            owner_id=uuid4(),
            higher_objective_id=objective_id,
            lower_objective_id=objective_id,
            strength=PreferenceStrength.STRONG,
            rationale="Synthetic preference",
            authored_by=AuthoredBy.OWNER,
            status=PreferenceStatus.DRAFT,
            valid_from=NOW,
        )


def test_forecast_requires_resolution_criteria_and_probability_bounds() -> None:
    with pytest.raises(ValueError, match="resolution_criteria"):
        ForecastQuestion(
            id=uuid4(),
            question="Will the synthetic event occur?",
            domain_key="test",
            resolution_criteria=" ",
            resolve_by=NOW + timedelta(days=1),
            created_at=NOW,
        )

    with pytest.raises(ValueError, match="probability"):
        ForecastPrediction(
            id=uuid4(),
            question_id=uuid4(),
            forecaster_type=ForecasterType.OWNER,
            probability=Decimal("1.01"),
            made_at=NOW,
        )


def test_atlas_prediction_requires_model_ref() -> None:
    with pytest.raises(ValueError, match="model_ref"):
        ForecastPrediction(
            id=uuid4(),
            question_id=uuid4(),
            forecaster_type=ForecasterType.ATLAS,
            probability=Decimal("0.5"),
            made_at=NOW,
        )


def test_forecast_resolution_requires_provenance() -> None:
    with pytest.raises(ValueError, match="provenance"):
        ForecastResolution(
            question_id=uuid4(),
            outcome=True,
            resolved_at=NOW,
            evidence_refs=(),
        )
