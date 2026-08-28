# Atlas Data Model

Vocabulary and canonical entities. Tables land in Queue 01+; this document fixes the
meaning of each entity so engines are written against a stable model.

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

**Goal** — `id, owner_id, title, category, horizon, target_date?, target_value?,
priority, status`.

**Policy** — `id, owner_id, name, policy_type, parameters_json, severity, enabled,
created_at`. Evaluation is deterministic (`POLICY` section of `IMPACT_ENGINE.md` and
Queue 11).

> **Never stored, anywhere:** seed phrases, private keys, withdrawal secrets, banking
> passwords. See `SECURITY.md`.

## Interaction entities

**Scenario** — `id, slug, title, horizon, thesis, probability, probability_method,
status, created_at, updated_at`.
**ScenarioDriver** — `scenario_id, narrative_id, direction, weight, current_score,
explanation`.

**Impact** (the central Atlas object) — `id, owner_id, world_delta_id, impact_domain,
target_id?, direction, severity, urgency, confidence, reversibility,
estimated_range_json?, causal_chain_json, explanation, generated_at`.

Impact domains: `portfolio, cash, currency, income, career, startup, migration,
residency, geography, housing, life_fortress, operational_security`.

Impact evidence classes: `DIRECT_CALCULATED, DIRECT_RULE, INFERRED_CAUSAL, SPECULATIVE`.

**Decision** — `id, owner_id, decision_type, created_at, valid_until?, status, title,
rationale, confidence, related_impacts[], related_scenarios[], policy_context[],
human_approved`. V1 decision types are non-executing: `OBSERVE, VERIFY, WAIT, PREPARE,
REVIEW_ALLOCATION, REVIEW_LOCATION, REVIEW_POLICY, NO_ACTION` (ADR-0003).

**Outcome** — `id, decision_id, evaluated_at, outcome_type, result_json,
forecast_score?, retrospective`. An outcome never mutates its decision.

## Operational entities

**RunRecord** — one per `run_atlas_cycle` execution: `run_id`, `as_of`, source results,
counts of raw items / events / narratives changed, model calls, cost, latency, deltas
created, alerts emitted, missing critical data, errors. This is what makes a run
replayable and auditable (blueprint §28).

**JobRun** — per ingestion stage, with structured error status.
