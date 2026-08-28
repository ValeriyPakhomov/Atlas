"""Queue 01 repositories and point-in-time owner-intent queries."""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import Select, insert, or_, select
from sqlalchemy.orm import Session

from atlas.domain.entities import (
    AuthoredBy,
    Event,
    Evidence,
    ForecastPrediction,
    ForecastQuestion,
    ForecastQuestionStatus,
    ForecastResolution,
    Narrative,
    Objective,
    ObjectiveStatus,
    Preference,
    PreferenceStatus,
    RawItem,
    RunRecord,
    Source,
)
from atlas.persistence.models import (
    EventModel,
    EvidenceModel,
    ForecastPredictionModel,
    ForecastQuestionModel,
    ForecastResolutionModel,
    NarrativeModel,
    ObjectiveModel,
    PreferenceModel,
    RawItemModel,
    RunRecordModel,
    SourceModel,
    event_evidence,
    forecast_prediction_evidence,
    forecast_resolution_evidence,
    narrative_events,
)

ModelT = TypeVar("ModelT")


class Queue01Repository:
    """Persistence boundary for the exact Queue 01 entity set.

    Methods flush but do not commit. The caller owns the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def _one(self, statement: Select[tuple[ModelT]]) -> ModelT:
        return self._session.scalars(statement).one()

    def add_source(self, source: Source) -> None:
        self._session.add(
            SourceModel(
                id=source.id,
                name=source.name,
                source_type=source.source_type,
                canonical_url=source.canonical_url,
                jurisdiction=source.jurisdiction,
                default_reliability=source.default_reliability,
                latency_class=source.latency_class,
                terms_notes=source.terms_notes,
                enabled=source.enabled,
                created_at=source.created_at,
                effective_tier=source.effective_tier,
            )
        )
        self._session.flush()

    def get_source(self, source_id: UUID) -> Source:
        row = self._one(select(SourceModel).where(SourceModel.id == source_id))
        return Source(
            id=row.id,
            name=row.name,
            source_type=row.source_type,
            canonical_url=row.canonical_url,
            jurisdiction=row.jurisdiction,
            default_reliability=row.default_reliability,
            latency_class=row.latency_class,
            terms_notes=row.terms_notes,
            enabled=row.enabled,
            created_at=row.created_at,
            effective_tier=row.effective_tier,
        )

    def add_raw_item(self, item: RawItem) -> None:
        self._session.add(
            RawItemModel(
                id=item.id,
                source_id=item.source_id,
                external_id=item.external_id,
                canonical_url=item.canonical_url,
                published_at=item.published_at,
                observed_at=item.observed_at,
                ingested_at=item.ingested_at,
                title=item.title,
                raw_text=item.raw_text,
                raw_payload=item.raw_payload,
                content_hash=item.content_hash,
                language=item.language,
                parse_version=item.parse_version,
                effective_tier=item.effective_tier,
            )
        )
        self._session.flush()

    def get_raw_item(self, item_id: UUID) -> RawItem:
        row = self._one(select(RawItemModel).where(RawItemModel.id == item_id))
        return RawItem(
            id=row.id,
            source_id=row.source_id,
            external_id=row.external_id,
            canonical_url=row.canonical_url,
            published_at=row.published_at,
            observed_at=row.observed_at,
            ingested_at=row.ingested_at,
            title=row.title,
            raw_text=row.raw_text,
            raw_payload=row.raw_payload,
            content_hash=row.content_hash,
            language=row.language,
            parse_version=row.parse_version,
            effective_tier=row.effective_tier,
        )

    def add_evidence(self, evidence: Evidence) -> None:
        self._session.add(
            EvidenceModel(
                id=evidence.id,
                raw_item_id=evidence.raw_item_id,
                proposition=evidence.proposition,
                evidence_type=evidence.evidence_type,
                entities=list(evidence.entities),
                effective_at=evidence.effective_at,
                expires_at=evidence.expires_at,
                source_reliability=evidence.source_reliability,
                extraction_confidence=evidence.extraction_confidence,
                verification_status=evidence.verification_status,
                structured_payload=evidence.structured_payload,
                effective_tier=evidence.effective_tier,
            )
        )
        self._session.flush()

    def get_evidence(self, evidence_id: UUID) -> Evidence:
        row = self._one(select(EvidenceModel).where(EvidenceModel.id == evidence_id))
        return Evidence(
            id=row.id,
            raw_item_id=row.raw_item_id,
            proposition=row.proposition,
            evidence_type=row.evidence_type,
            entities=tuple(row.entities),
            effective_at=row.effective_at,
            expires_at=row.expires_at,
            source_reliability=row.source_reliability,
            extraction_confidence=row.extraction_confidence,
            verification_status=row.verification_status,
            structured_payload=row.structured_payload,
            effective_tier=row.effective_tier,
        )

    def add_event(self, event: Event) -> None:
        self._session.add(
            EventModel(
                id=event.id,
                event_type=event.event_type,
                canonical_title=event.canonical_title,
                summary=event.summary,
                occurred_at=event.occurred_at,
                first_reported_at=event.first_reported_at,
                last_updated_at=event.last_updated_at,
                geography=list(event.geography),
                entities=list(event.entities),
                sectors=list(event.sectors),
                assets=list(event.assets),
                credibility_score=event.credibility_score,
                novelty_score=event.novelty_score,
                urgency_score=event.urgency_score,
                status=event.status,
                dedupe_key=event.dedupe_key,
                effective_tier=event.effective_tier,
            )
        )
        self._session.flush()
        if event.evidence_ids:
            self._session.execute(
                insert(event_evidence),
                [
                    {"event_id": event.id, "evidence_id": evidence_id}
                    for evidence_id in event.evidence_ids
                ],
            )

    def get_event(self, event_id: UUID) -> Event:
        row = self._one(select(EventModel).where(EventModel.id == event_id))
        evidence_ids = tuple(
            self._session.scalars(
                select(event_evidence.c.evidence_id).where(event_evidence.c.event_id == event_id)
            )
        )
        return Event(
            id=row.id,
            event_type=row.event_type,
            canonical_title=row.canonical_title,
            summary=row.summary,
            occurred_at=row.occurred_at,
            first_reported_at=row.first_reported_at,
            last_updated_at=row.last_updated_at,
            credibility_score=row.credibility_score,
            novelty_score=row.novelty_score,
            urgency_score=row.urgency_score,
            status=row.status,
            dedupe_key=row.dedupe_key,
            evidence_ids=evidence_ids,
            geography=tuple(row.geography),
            entities=tuple(row.entities),
            sectors=tuple(row.sectors),
            assets=tuple(row.assets),
            effective_tier=row.effective_tier,
        )

    def add_narrative(self, narrative: Narrative) -> None:
        self._session.add(
            NarrativeModel(
                id=narrative.id,
                slug=narrative.slug,
                title=narrative.title,
                description=narrative.description,
                category=narrative.category,
                status=narrative.status,
                direction=narrative.direction,
                strength=narrative.strength,
                confidence=narrative.confidence,
                first_seen_at=narrative.first_seen_at,
                last_changed_at=narrative.last_changed_at,
                last_confirmed_at=narrative.last_confirmed_at,
                effective_tier=narrative.effective_tier,
            )
        )
        self._session.flush()
        if narrative.event_ids:
            self._session.execute(
                insert(narrative_events),
                [
                    {"narrative_id": narrative.id, "event_id": event_id}
                    for event_id in narrative.event_ids
                ],
            )

    def get_narrative(self, narrative_id: UUID) -> Narrative:
        row = self._one(select(NarrativeModel).where(NarrativeModel.id == narrative_id))
        event_ids = tuple(
            self._session.scalars(
                select(narrative_events.c.event_id).where(
                    narrative_events.c.narrative_id == narrative_id
                )
            )
        )
        return Narrative(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            category=row.category,
            status=row.status,
            direction=row.direction,
            strength=row.strength,
            confidence=row.confidence,
            first_seen_at=row.first_seen_at,
            last_changed_at=row.last_changed_at,
            last_confirmed_at=row.last_confirmed_at,
            event_ids=event_ids,
            effective_tier=row.effective_tier,
        )

    def add_run_record(self, run: RunRecord) -> None:
        self._session.add(
            RunRecordModel(
                run_id=run.run_id,
                as_of=run.as_of,
                source_results=run.source_results,
                counts=run.counts,
                model_calls=list(run.model_calls),
                cost=run.cost,
                latency_ms=run.latency_ms,
                deltas_created=run.deltas_created,
                alerts_emitted=run.alerts_emitted,
                missing_critical_data=list(run.missing_critical_data),
                errors=list(run.errors),
                effective_tier=run.effective_tier,
            )
        )
        self._session.flush()

    def get_run_record(self, run_id: UUID) -> RunRecord:
        row = self._one(select(RunRecordModel).where(RunRecordModel.run_id == run_id))
        return RunRecord(
            run_id=row.run_id,
            as_of=row.as_of,
            source_results=row.source_results,
            counts=row.counts,
            model_calls=tuple(row.model_calls),
            cost=row.cost,
            latency_ms=row.latency_ms,
            deltas_created=row.deltas_created,
            alerts_emitted=row.alerts_emitted,
            missing_critical_data=tuple(row.missing_critical_data),
            errors=tuple(row.errors),
            effective_tier=row.effective_tier,
        )

    def add_objective(self, objective: Objective, *, proposed_by_model: bool = False) -> None:
        if proposed_by_model and objective.authored_by is not AuthoredBy.ATLAS_PROPOSED:
            raise ValueError("a model-originated objective must be marked atlas_proposed")
        self._session.add(
            ObjectiveModel(
                id=objective.id,
                owner_id=objective.owner_id,
                title=objective.title,
                description=objective.description,
                category_key=objective.category_key,
                direction=objective.direction,
                horizon=objective.horizon,
                target_date=objective.target_date,
                target_value=objective.target_value,
                target_currency=objective.target_currency,
                priority=objective.priority,
                status=objective.status,
                authored_by=objective.authored_by,
                accepted_at=objective.accepted_at,
                valid_from=objective.valid_from,
                valid_to=objective.valid_to,
                effective_tier=objective.effective_tier,
            )
        )
        self._session.flush()

    def authoritative_objectives(self, owner_id: UUID, as_of: datetime) -> tuple[Objective, ...]:
        rows = self._session.scalars(
            select(ObjectiveModel)
            .where(
                ObjectiveModel.owner_id == owner_id,
                ObjectiveModel.status == ObjectiveStatus.ACTIVE,
                ObjectiveModel.accepted_at.is_not(None),
                ObjectiveModel.accepted_at <= as_of,
                ObjectiveModel.valid_from <= as_of,
                or_(ObjectiveModel.valid_to.is_(None), ObjectiveModel.valid_to > as_of),
            )
            .order_by(ObjectiveModel.priority, ObjectiveModel.id)
        )
        return tuple(self._objective_from_row(row) for row in rows)

    @staticmethod
    def _objective_from_row(row: ObjectiveModel) -> Objective:
        return Objective(
            id=row.id,
            owner_id=row.owner_id,
            title=row.title,
            description=row.description,
            category_key=row.category_key,
            direction=row.direction,
            horizon=row.horizon,
            target_date=row.target_date,
            target_value=row.target_value,
            target_currency=row.target_currency,
            priority=row.priority,
            status=row.status,
            authored_by=row.authored_by,
            accepted_at=row.accepted_at,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            effective_tier=row.effective_tier,
        )

    def add_preference(self, preference: Preference, *, proposed_by_model: bool = False) -> None:
        if proposed_by_model and preference.authored_by is not AuthoredBy.ATLAS_PROPOSED:
            raise ValueError("a model-originated preference must be marked atlas_proposed")
        self._validate_preference_owner(preference)
        if preference.status is PreferenceStatus.ACTIVE and preference.accepted_at is not None:
            self._reject_preference_cycle(preference)
        self._session.add(
            PreferenceModel(
                id=preference.id,
                owner_id=preference.owner_id,
                higher_objective_id=preference.higher_objective_id,
                lower_objective_id=preference.lower_objective_id,
                strength=preference.strength,
                rationale=preference.rationale,
                authored_by=preference.authored_by,
                accepted_at=preference.accepted_at,
                status=preference.status,
                valid_from=preference.valid_from,
                valid_to=preference.valid_to,
                effective_tier=preference.effective_tier,
            )
        )
        self._session.flush()

    def _validate_preference_owner(self, preference: Preference) -> None:
        owners = tuple(
            self._session.scalars(
                select(ObjectiveModel.owner_id).where(
                    ObjectiveModel.id.in_(
                        [preference.higher_objective_id, preference.lower_objective_id]
                    )
                )
            )
        )
        if len(owners) != 2 or any(owner != preference.owner_id for owner in owners):
            raise ValueError("both preference objectives must belong to the same owner")

    def _reject_preference_cycle(self, preference: Preference) -> None:
        if preference.accepted_at is None:
            return
        effective_start = max(preference.valid_from, preference.accepted_at)
        conditions = [
            PreferenceModel.owner_id == preference.owner_id,
            PreferenceModel.status == PreferenceStatus.ACTIVE,
            PreferenceModel.accepted_at.is_not(None),
            or_(
                PreferenceModel.valid_to.is_(None),
                PreferenceModel.valid_to > effective_start,
            ),
        ]
        if preference.valid_to is not None:
            conditions.extend(
                [
                    PreferenceModel.valid_from < preference.valid_to,
                    PreferenceModel.accepted_at < preference.valid_to,
                ]
            )
        edges = list(
            self._session.execute(
                select(
                    PreferenceModel.higher_objective_id,
                    PreferenceModel.lower_objective_id,
                ).where(*conditions)
            ).tuples()
        )
        edges.append((preference.higher_objective_id, preference.lower_objective_id))
        graph: dict[UUID, set[UUID]] = {}
        for higher, lower in edges:
            graph.setdefault(higher, set()).add(lower)

        target = preference.higher_objective_id
        pending = [preference.lower_objective_id]
        visited: set[UUID] = set()
        while pending:
            node = pending.pop()
            if node == target:
                raise ValueError("active ordinal preferences must be acyclic")
            if node in visited:
                continue
            visited.add(node)
            pending.extend(graph.get(node, ()))

    def authoritative_preferences(self, owner_id: UUID, as_of: datetime) -> tuple[Preference, ...]:
        rows = self._session.scalars(
            select(PreferenceModel)
            .where(
                PreferenceModel.owner_id == owner_id,
                PreferenceModel.status == PreferenceStatus.ACTIVE,
                PreferenceModel.accepted_at.is_not(None),
                PreferenceModel.accepted_at <= as_of,
                PreferenceModel.valid_from <= as_of,
                or_(PreferenceModel.valid_to.is_(None), PreferenceModel.valid_to > as_of),
            )
            .order_by(PreferenceModel.id)
        )
        return tuple(self._preference_from_row(row) for row in rows)

    @staticmethod
    def _preference_from_row(row: PreferenceModel) -> Preference:
        return Preference(
            id=row.id,
            owner_id=row.owner_id,
            higher_objective_id=row.higher_objective_id,
            lower_objective_id=row.lower_objective_id,
            strength=row.strength,
            rationale=row.rationale,
            authored_by=row.authored_by,
            accepted_at=row.accepted_at,
            status=row.status,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            effective_tier=row.effective_tier,
        )

    def add_forecast_question(self, question: ForecastQuestion) -> None:
        self._session.add(
            ForecastQuestionModel(
                id=question.id,
                question=question.question,
                domain_key=question.domain_key,
                resolution_criteria=question.resolution_criteria,
                resolve_by=question.resolve_by,
                created_at=question.created_at,
                status=question.status,
                effective_tier=question.effective_tier,
            )
        )
        self._session.flush()

    def get_forecast_question(self, question_id: UUID) -> ForecastQuestion:
        row = self._one(
            select(ForecastQuestionModel).where(ForecastQuestionModel.id == question_id)
        )
        return ForecastQuestion(
            id=row.id,
            question=row.question,
            domain_key=row.domain_key,
            resolution_criteria=row.resolution_criteria,
            resolve_by=row.resolve_by,
            created_at=row.created_at,
            status=row.status,
            effective_tier=row.effective_tier,
        )

    def add_forecast_prediction(self, prediction: ForecastPrediction) -> None:
        self._session.add(
            ForecastPredictionModel(
                id=prediction.id,
                question_id=prediction.question_id,
                forecaster_type=prediction.forecaster_type,
                probability=prediction.probability,
                made_at=prediction.made_at,
                model_ref=prediction.model_ref,
                prompt_or_artifact_version_refs=list(prediction.prompt_or_artifact_version_refs),
                note=prediction.note,
                supersedes_prediction_id=prediction.supersedes_prediction_id,
                effective_tier=prediction.effective_tier,
            )
        )
        self._session.flush()
        if prediction.evidence_refs:
            self._session.execute(
                insert(forecast_prediction_evidence),
                [
                    {"prediction_id": prediction.id, "evidence_id": evidence_id}
                    for evidence_id in prediction.evidence_refs
                ],
            )

    def forecast_predictions(self, question_id: UUID) -> tuple[ForecastPrediction, ...]:
        rows = self._session.scalars(
            select(ForecastPredictionModel)
            .where(ForecastPredictionModel.question_id == question_id)
            .order_by(ForecastPredictionModel.made_at, ForecastPredictionModel.id)
        )
        predictions: list[ForecastPrediction] = []
        for row in rows:
            evidence_refs = tuple(
                self._session.scalars(
                    select(forecast_prediction_evidence.c.evidence_id).where(
                        forecast_prediction_evidence.c.prediction_id == row.id
                    )
                )
            )
            predictions.append(
                ForecastPrediction(
                    id=row.id,
                    question_id=row.question_id,
                    forecaster_type=row.forecaster_type,
                    probability=row.probability,
                    made_at=row.made_at,
                    model_ref=row.model_ref,
                    prompt_or_artifact_version_refs=tuple(row.prompt_or_artifact_version_refs),
                    evidence_refs=evidence_refs,
                    note=row.note,
                    supersedes_prediction_id=row.supersedes_prediction_id,
                    effective_tier=row.effective_tier,
                )
            )
        return tuple(predictions)

    def add_forecast_resolution(self, resolution: ForecastResolution) -> None:
        question = self._one(
            select(ForecastQuestionModel).where(ForecastQuestionModel.id == resolution.question_id)
        )
        self._session.add(
            ForecastResolutionModel(
                question_id=resolution.question_id,
                outcome=resolution.outcome,
                resolved_at=resolution.resolved_at,
                resolution_note=resolution.resolution_note,
                effective_tier=resolution.effective_tier,
            )
        )
        question.status = ForecastQuestionStatus.RESOLVED
        self._session.flush()
        self._session.execute(
            insert(forecast_resolution_evidence),
            [
                {"question_id": resolution.question_id, "evidence_id": evidence_id}
                for evidence_id in resolution.evidence_refs
            ],
        )

    def get_forecast_resolution(self, question_id: UUID) -> ForecastResolution:
        row = self._one(
            select(ForecastResolutionModel).where(
                ForecastResolutionModel.question_id == question_id
            )
        )
        evidence_refs = tuple(
            self._session.scalars(
                select(forecast_resolution_evidence.c.evidence_id).where(
                    forecast_resolution_evidence.c.question_id == question_id
                )
            )
        )
        return ForecastResolution(
            question_id=row.question_id,
            outcome=row.outcome,
            resolved_at=row.resolved_at,
            evidence_refs=evidence_refs,
            resolution_note=row.resolution_note,
            effective_tier=row.effective_tier,
        )
