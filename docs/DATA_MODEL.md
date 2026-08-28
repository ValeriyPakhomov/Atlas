# Atlas Data Model

Vocabulary and canonical entities. This document distinguishes the stable vocabulary from
the queue item that creates each table; documenting a future entity does not authorise an
empty placeholder table.

**Queue 01 implements only:** common ID/time/provenance and sensitivity primitives;
`Source`, `RawItem`, `Evidence`, `Event`, `Narrative`, `RunRecord`, `Objective`,
`Preference`, `ForecastQuestion`, `ForecastPrediction` and `ForecastResolution`, plus
their SQLAlchemy persistence and repositories. All other entities below land with their
named later queue item.

Identifiers are UUID/ULID. Pydantic is used at API boundaries, SQLAlchemy/SQLModel or
explicit SQL at persistence boundaries, and stdlib dataclasses inside the domain
package (ADR-0001).

## Temporal columns

A02 requires these to be distinct, never collapsed into one `timestamp`:

| Column | Meaning |
| --- | --- |
| `occurred_at` / event time | when the thing happened in the world |
| `published_at` | when the source published it |
| `observed_at` | when Atlas saw the value (e.g. a price mark) |
| `ingested_at` | when Atlas stored it |
| `valid_from` / `valid_to` | the interval during which a state row is true |
| `decision_time` | when a decision was taken, with the evidence then available |
| `evaluated_at` | when an outcome was scored |

State changes **append a new row and close the previous interval**. Nothing is
overwritten. Derived rows carry `run_id` and provenance (A05).

At `as_of = T`, authoritative owner intent contains only records accepted by the owner,
with `status = active` and `valid_from <= T < valid_to` (or no `valid_to`). Closed versions
remain queryable for replay.

## Sensitivity columns

Persistence mappings declare `schema_max_tier` and `schema_default_tier` next to every
column. Each relevant record/value carries an `effective_tier`; mixed or unclassified
personal free text fails high to L3. Effective tier may not exceed the schema maximum and
derived values inherit the maximum effective tier of their inputs (ADR-0010).

## Provenance chain

```
Source -> RawItem -> Evidence -> Event -> Narrative -> WorldStateDelta -> Impact -> Decision -> Outcome
```

Every link is stored. There is no "AI believes" state without this chain.

## Ingestion entities

**Source** — `id, name, source_type, canonical_url, jurisdiction, default_reliability,
latency_class, terms_notes, enabled, created_at`. Reliability classes A–D are defined
in `SOURCE_POLICY.md`.

**RawItem** — immutable capture: `id, source_id, external_id, canonical_url,
published_at, observed_at, ingested_at, title, raw_text, raw_payload_json,
content_hash, language, parse_version`. Unique on `(source_id, external_id)` where
available, otherwise on `content_hash` (A08).

**Evidence** — a normalised factual proposition: `id, raw_item_id, proposition,
evidence_type, entities[], effective_at, expires_at?, source_reliability,
extraction_confidence, verification_status, structured_payload_json`.

**Event** — a canonical real-world event supported by many Evidence rows: `id,
event_type, canonical_title, summary, occurred_at, first_reported_at, last_updated_at,
geography[], entities[], sectors[], assets[], credibility_score, novelty_score,
urgency_score, status, dedupe_key`.

**Narrative** — a persistent evolving theme linking events over time: `id, slug, title,
description, category, status, direction, strength, confidence, first_seen_at,
last_changed_at, last_confirmed_at`. Lifecycle:
`candidate → active → strengthening/weakening → dormant → resolved`.

## World state

**WorldStateSnapshot** — `id, as_of, run_id, overall_regime, confidence, generated_at`.

**WorldStateDimension** — `snapshot_id, dimension_key, score (−3..+3), direction,
confidence (0..1), freshness, evidence_count, rationale, primary_narratives[]`.

**WorldStateDelta** — `from_snapshot_id, to_snapshot_id, dimension_key, old_score,
new_score, materiality, cause_narratives[], evidence_ids[], explanation`. The daily
brief consumes **deltas**, not full snapshots.

Dimension keys are enumerated in `WORLD_STATE.md`. V1 starts with ten, not the full list.

## Personal state

**PersonalStateSnapshot** — `id, owner_id, as_of, base_currency, current_country,
current_city, monthly_burn_base, liquid_net_worth_base, total_known_net_worth_base,
data_freshness, generated_at`. Children are structured categories, never one JSON blob.

**Account** — `id, owner_id, account_type, institution, jurisdiction, base_currency,
access_mode (manual | read-only-api | import), last_synced_at`.

**Position** — `id, account_id, instrument_id, quantity, cost_basis?,
market_value_base, currency, observed_at, source`.

**CashBalance** — `id, account_id, currency, amount, amount_base, observed_at`.

**IncomeStream** — `id, owner_id, category, geography, currency, expected_monthly_low,
expected_monthly_base, expected_monthly_high, confidence, mobility_dependency,
ai_disruption_exposure, active`.

**GeographyState** — `owner_id, country, city?, role (current_base | candidate |
fallback | work_market), residence_status, valid_until?, next_deadline?,
mobility_friction, currency_exposure, career_fit, fortress_score?`.

**Objective** *(Queue 01)* — owner-authored canonical intent: `id, owner_id, title,
description, category_key, direction (attain | avoid | maintain), horizon (short | medium |
long), target_date?, target_value?, target_currency?, priority, status (draft | active |
achieved | abandoned | inactive | superseded), authored_by (owner | atlas_proposed),
accepted_at?, valid_from, valid_to?, effective_tier`. `category_key` is registry/data-driven,
not a PostgreSQL enum. Atlas-proposed or unaccepted rows are inert (ADR-0011).

**Preference** *(Queue 01)* — temporal pairwise ordinal intent: `id, owner_id,
higher_objective_id, lower_objective_id, strength (weak | strong), rationale,
authored_by (owner | atlas_proposed), accepted_at?, status (draft | active | inactive |
superseded), valid_from, valid_to?, effective_tier`. Active accepted preferences must be
acyclic at every `as_of`. No utility functions or numeric exchange rates.

**Policy** — `id, owner_id, name, policy_type, parameters_json, severity, enabled,
created_at, objective_id?`. The objective link is implemented with Policy in Queue 11, not
as an empty Queue 01 table. Evaluation is deterministic (`POLICY` section of
`IMPACT_ENGINE.md` and Queue 11).

> **Never stored, anywhere:** seed phrases, private keys, withdrawal secrets, banking
> passwords. See `SECURITY.md`.

## Interaction entities

### Forecast ledger (Queue 01; no forecasting engine)

V1 questions are binary and objectively resolvable. The ledger stores primitives; Brier
scores and calibration curves are derived analytics and are not canonical columns.

**ForecastQuestion** — `id, question, domain_key, resolution_criteria, resolve_by,
created_at, status (open | resolved | cancelled), effective_tier`. Resolution criteria are
mandatory.

**ForecastPrediction** — immutable append-only prediction: `id, question_id,
forecaster_type (owner | atlas), probability (0..1), made_at, model_ref?,
prompt_or_artifact_version_refs[], evidence_refs[], note?, supersedes_prediction_id?,
effective_tier`. Updating a forecast appends a prediction linked to the row it supersedes.

**ForecastResolution** — one provenance-backed resolution per question: `question_id,
outcome (true | false), resolved_at, evidence_refs[], resolution_note?, effective_tier`.

**Scenario** — `id, slug, title, horizon, thesis, probability, probability_method,
status, created_at, updated_at`.
**ScenarioDriver** — `scenario_id, narrative_id, direction, weight, current_score,
explanation`.

**Impact** (Queue 09; the central Atlas object) — `id, owner_id, world_delta_id,
impact_domain, target_id?, direction, severity, urgency, confidence, reversibility,
estimated_range_json?, typed_causal_chain, objective_refs[], attention_class, explanation,
generated_at, artifact_version_refs[]`. The attention class is exactly
`ACTION | VERIFY | REVIEW | BACKGROUND | SUPPRESS` (ADR-0008).

Impact domains: `portfolio, cash, currency, income, career, startup, migration,
residency, geography, housing, life_fortress, operational_security`.

Impact evidence classes: `DIRECT_CALCULATED, DIRECT_RULE, INFERRED_CAUSAL, SPECULATIVE`.

**Decision** (Queue 12) — `id, owner_id, decision_type, created_at, valid_until?, status,
title, rationale, confidence, related_impacts[], related_scenarios[], policy_context[],
considered_options[], objectives_active_at_decision[], artifact_version_refs[],
human_approved`. V1 decision types are non-executing: `OBSERVE, VERIFY, WAIT, PREPARE,
REVIEW_ALLOCATION, REVIEW_LOCATION, REVIEW_POLICY, NO_ACTION` (ADR-0003).

**Outcome** — `id, decision_id, evaluated_at, outcome_type, result_json,
forecast_score?, retrospective`. An outcome never mutates its decision.

## Operational entities

**RunRecord** *(Queue 01 foundation; populated fully in Queue 13)* — one per
`run_atlas_cycle` execution: `run_id`, `as_of`, source results,
counts of raw items / events / narratives changed, model calls, cost, latency, deltas
created, alerts emitted, missing critical data, errors. This is what makes a run
replayable and auditable (blueprint §28).

**JobRun** — per ingestion stage, with structured error status.
