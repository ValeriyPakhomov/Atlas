"""Queue 01 acceptance tests against PostgreSQL 16."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from atlas.domain.entities import (
    AuthoredBy,
    Event,
    Evidence,
    ForecasterType,
    ForecastPrediction,
    ForecastQuestion,
    ForecastResolution,
    Narrative,
    Objective,
    ObjectiveDirection,
    ObjectiveHorizon,
    ObjectiveStatus,
    Preference,
    PreferenceStatus,
    PreferenceStrength,
    RawItem,
    RunRecord,
    Source,
)
from atlas.domain.sensitivity import SensitivityTier
from atlas.persistence.repositories import Queue01Repository

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 28, 12, tzinfo=UTC)


def _objective(
    owner_id: UUID,
    title: str,
    *,
    status: ObjectiveStatus = ObjectiveStatus.ACTIVE,
    authored_by: AuthoredBy = AuthoredBy.OWNER,
    accepted_at: datetime | None = NOW,
    valid_from: datetime = NOW - timedelta(days=1),
    valid_to: datetime | None = None,
) -> Objective:
    return Objective(
        id=uuid4(),
        owner_id=owner_id,
        title=title,
        description=f"Description for {title}",
        category_key="personal.capital",
        direction=ObjectiveDirection.ATTAIN,
        horizon=ObjectiveHorizon.LONG,
        priority=1,
        status=status,
        authored_by=authored_by,
        accepted_at=accepted_at,
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _preference(
    owner_id: UUID,
    higher: UUID,
    lower: UUID,
    *,
    status: PreferenceStatus = PreferenceStatus.ACTIVE,
    authored_by: AuthoredBy = AuthoredBy.OWNER,
    accepted_at: datetime | None = NOW,
) -> Preference:
    return Preference(
        id=uuid4(),
        owner_id=owner_id,
        higher_objective_id=higher,
        lower_objective_id=lower,
        strength=PreferenceStrength.STRONG,
        rationale="Owner-confirmed ordering",
        authored_by=authored_by,
        status=status,
        accepted_at=accepted_at,
        valid_from=NOW - timedelta(hours=1),
    )


def _provenance_chain(repo: Queue01Repository) -> tuple[Source, RawItem, Evidence]:
    source = Source(
        id=uuid4(),
        name="Public filing",
        source_type="regulator",
        created_at=NOW,
        default_reliability=Decimal("0.95"),
    )
    raw = RawItem(
        id=uuid4(),
        source_id=source.id,
        observed_at=NOW,
        ingested_at=NOW,
        content_hash=uuid4().hex,
        raw_text="Issuer filed audited results.",
        effective_tier=SensitivityTier.L1,
    )
    evidence = Evidence(
        id=uuid4(),
        raw_item_id=raw.id,
        proposition="Audited revenue increased.",
        evidence_type="filing",
        effective_at=NOW,
        source_reliability=Decimal("0.95"),
        extraction_confidence=Decimal("0.90"),
        verification_status="verified",
    )
    repo.add_source(source)
    repo.add_raw_item(raw)
    repo.add_evidence(evidence)
    return source, raw, evidence


def test_postgresql_16_and_migration_head(db_session: Session) -> None:
    version = db_session.scalar(text("SHOW server_version"))
    revision = db_session.scalar(text("SELECT version_num FROM alembic_version"))
    assert version is not None and version.startswith("16.")
    assert revision is not None


def test_provenance_round_trip(db_session: Session) -> None:
    repo = Queue01Repository(db_session)
    source, raw, evidence = _provenance_chain(repo)
    event = Event(
        id=uuid4(),
        event_type="earnings",
        canonical_title="Audited results published",
        summary="Revenue increased year over year.",
        occurred_at=NOW,
        first_reported_at=NOW,
        last_updated_at=NOW,
        credibility_score=Decimal("0.95"),
        novelty_score=Decimal("0.70"),
        urgency_score=Decimal("0.30"),
        status="confirmed",
        dedupe_key=uuid4().hex,
        evidence_ids=(evidence.id,),
    )
    narrative = Narrative(
        id=uuid4(),
        slug=f"revenue-{uuid4().hex}",
        title="Revenue acceleration",
        description="Audited results support the narrative.",
        category="company",
        status="active",
        direction="strengthening",
        strength=Decimal("0.70"),
        confidence=Decimal("0.80"),
        first_seen_at=NOW,
        last_changed_at=NOW,
        last_confirmed_at=NOW,
        event_ids=(event.id,),
    )
    run = RunRecord(run_id=uuid4(), as_of=NOW, counts={"evidence": 1})
    repo.add_event(event)
    repo.add_narrative(narrative)
    repo.add_run_record(run)

    assert repo.get_source(source.id) == source
    assert repo.get_raw_item(raw.id) == raw
    assert repo.get_evidence(evidence.id) == evidence
    assert repo.get_event(event.id) == event
    assert repo.get_narrative(narrative.id) == narrative
    assert repo.get_run_record(run.run_id) == run


def test_foreign_key_integrity(db_session: Session) -> None:
    repo = Queue01Repository(db_session)
    orphan = RawItem(
        id=uuid4(),
        source_id=uuid4(),
        observed_at=NOW,
        ingested_at=NOW,
        content_hash=uuid4().hex,
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        repo.add_raw_item(orphan)


def test_temporal_authority_and_inert_proposals(db_session: Session) -> None:
    repo = Queue01Repository(db_session)
    owner_id = uuid4()
    historical = _objective(
        owner_id,
        "Historical",
        accepted_at=NOW - timedelta(days=30),
        valid_from=NOW - timedelta(days=30),
        valid_to=NOW - timedelta(days=2),
    )
    current = _objective(owner_id, "Current")
    proposal = _objective(
        owner_id,
        "Unaccepted proposal",
        status=ObjectiveStatus.DRAFT,
        authored_by=AuthoredBy.ATLAS_PROPOSED,
        accepted_at=None,
    )
    future_acceptance = _objective(
        owner_id,
        "Accepted only in the future",
        accepted_at=NOW + timedelta(days=1),
    )
    for objective in (historical, current):
        repo.add_objective(objective)
    repo.add_objective(proposal, proposed_by_model=True)
    repo.add_objective(future_acceptance)

    with pytest.raises(ValueError, match="atlas_proposed"):
        repo.add_objective(
            _objective(
                owner_id,
                "Spoofed model proposal",
                status=ObjectiveStatus.DRAFT,
                accepted_at=None,
            ),
            proposed_by_model=True,
        )

    past = repo.authoritative_objectives(owner_id, NOW - timedelta(days=10))
    present = repo.authoritative_objectives(owner_id, NOW)
    assert [item.id for item in past] == [historical.id]
    assert [item.id for item in present] == [current.id]
    assert proposal.id not in {item.id for item in present}
    assert future_acceptance.id not in {item.id for item in present}

    inert_preference = _preference(
        owner_id,
        current.id,
        historical.id,
        status=PreferenceStatus.DRAFT,
        authored_by=AuthoredBy.ATLAS_PROPOSED,
        accepted_at=None,
    )
    repo.add_preference(inert_preference, proposed_by_model=True)
    future_preference = _preference(
        owner_id,
        current.id,
        historical.id,
        accepted_at=NOW + timedelta(days=1),
    )
    repo.add_preference(future_preference)
    assert repo.authoritative_preferences(owner_id, NOW) == ()

    with pytest.raises(ValueError, match="atlas_proposed"):
        repo.add_preference(
            _preference(
                owner_id,
                current.id,
                historical.id,
                status=PreferenceStatus.DRAFT,
                accepted_at=None,
            ),
            proposed_by_model=True,
        )


def test_preference_cycles_are_rejected(db_session: Session) -> None:
    repo = Queue01Repository(db_session)
    owner_id = uuid4()
    objectives = [_objective(owner_id, name) for name in ("A", "B", "C")]
    for objective in objectives:
        repo.add_objective(objective)
    repo.add_preference(_preference(owner_id, objectives[0].id, objectives[1].id))
    repo.add_preference(_preference(owner_id, objectives[1].id, objectives[2].id))

    with pytest.raises(ValueError, match="acyclic"):
        repo.add_preference(_preference(owner_id, objectives[2].id, objectives[0].id))


def test_forecast_ledger_is_append_only_and_primitive(db_session: Session) -> None:
    repo = Queue01Repository(db_session)
    _, _, evidence = _provenance_chain(repo)
    question = ForecastQuestion(
        id=uuid4(),
        question="Will the binary milestone occur?",
        domain_key="company.milestone",
        resolution_criteria="True iff the regulator publishes approval by the deadline.",
        resolve_by=NOW + timedelta(days=30),
        created_at=NOW,
    )
    first = ForecastPrediction(
        id=uuid4(),
        question_id=question.id,
        forecaster_type=ForecasterType.ATLAS,
        probability=Decimal("0.55"),
        made_at=NOW,
        model_ref="model:v1",
        prompt_or_artifact_version_refs=("prompt:v1",),
        evidence_refs=(evidence.id,),
    )
    second = ForecastPrediction(
        id=uuid4(),
        question_id=question.id,
        forecaster_type=ForecasterType.ATLAS,
        probability=Decimal("0.70"),
        made_at=NOW + timedelta(days=1),
        model_ref="model:v1",
        prompt_or_artifact_version_refs=("prompt:v2",),
        evidence_refs=(evidence.id,),
        supersedes_prediction_id=first.id,
    )
    repo.add_forecast_question(question)
    repo.add_forecast_prediction(first)
    repo.add_forecast_prediction(second)
    repo.add_forecast_resolution(
        ForecastResolution(
            question_id=question.id,
            outcome=True,
            resolved_at=NOW + timedelta(days=20),
            evidence_refs=(evidence.id,),
            resolution_note="Approval published.",
        )
    )

    predictions = repo.forecast_predictions(question.id)
    assert [prediction.id for prediction in predictions] == [first.id, second.id]
    assert repo.get_forecast_resolution(question.id).outcome is True
    columns = set(
        db_session.scalars(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'forecast_predictions'"
            )
        )
    )
    assert "brier_score" not in columns

    with pytest.raises(DBAPIError, match="append-only"), db_session.begin_nested():
        db_session.execute(
            text("UPDATE forecast_predictions SET probability = 0.1 WHERE id = :id"),
            {"id": first.id},
        )
    with pytest.raises(DBAPIError, match="append-only"), db_session.begin_nested():
        db_session.execute(
            text("DELETE FROM forecast_predictions WHERE id = :id"), {"id": second.id}
        )
