# UX Data Contracts

What the product surfaces need from the API. **This document changes no backend
architecture.** It describes read-model *shapes*; endpoint naming, transport and
implementation remain the API's decision (Queue 17).

---

## 1. The governing rule

> **The backend emits presentation-ready semantics. The frontend emits pixels.**

The frontend performs **no** business logic. Specifically it never:

- ranks impacts or computes priority;
- classifies attention;
- applies thresholds or materiality tests;
- rounds probabilities or derives confidence bands;
- decides which brief sections to include;
- computes freshness or staleness;
- resolves objective or evidence references.

All of that is deterministic domain logic (ADR-0004) and must be computed once, server
side, so that a brief rendered on the web, in Telegram, or by an external assistant
through MCP is **the same brief**. A rounding rule implemented in a React component is a
rounding rule that Telegram gets wrong.

Consequences the read models must therefore satisfy:

- probabilities arrive with **both** the exact value and `display_probability` (5-point
  step) plus `changed_since_previous`;
- confidence arrives as **both** `value` and `band`;
- every ranked list arrives **already ordered**, with `priority` and its components;
- omitted sections are **absent**, not empty arrays — absence is the instruction not to
  render a heading;
- every claim carries `evidence_class` and a provenance handle.

---

## 2. Read models

Shapes are illustrative, not literal schemas.

### 2.1 `TodayView` / `BriefView`

The same shape; Today is the brief for the current cycle.

```
BriefView
  date, run_id, generated_at, as_of
  signal          { claim_type, sentence, matters_count, attention_count }
  integrity       { status, reasons[] }              // DEGRADED leads the brief
  changes[]       { kind: WORLD|YOU|IMPACT|SCENARIO|DECISION,
                    headline, from?, to?, materiality, link, freshness?,
                    is_escalation, above_fold: bool }
  impacts[]       ImpactSummary        // ordered; see 2.2
  atlas_view?     { prose, word_count, claim_links[] }
  candidates[]    { decision_type, title, mechanism, impact_refs[],
                    proposed_review_date }
  scenarios?      ScenarioSetView      // absent unless materially moved
  invalidators[]  { conclusion_ref, observation, current_status }
  unknowns[]      { kind: UNKNOWN|STALE|MISSING|CONFLICTING|UNVERIFIED|DEGRADED,
                    subject, detail, blocks[] }
  watching[]      { subject, trigger_description, current_value?, distance? }
  coverage        { sources_checked, sources_current, items_reviewed, items_material }
```

`coverage` exists specifically for quiet days: it is what proves Atlas looked.

`above_fold` is computed server-side so the volume ceiling is enforced once, not
re-derived per client.

### 2.2 `ImpactSummary` and `ImpactDetail`

```
ImpactSummary                          // collapsed tier
  id, domain, direction, claim
  attention_class, confidence { value, band }, evidence_class
  objectives[] { id, title, direction }
  priority, is_opportunity            // favourable + objective-linked
  freshness_flags[]

ImpactDetail                           // expanded tier
  ...ImpactSummary
  components { severity, exposure, urgency, irreversibility }   // ordinal terms + values
  causal_chain[] { step_label, evidence_class, evidence_refs[], confidence? }
  invalidators[]
  related_scenarios[], related_decisions[]
  estimated_range?
  generated_at, world_delta_ref

ImpactForensics                        // forensic tier, separate fetch
  provenance[]    // impact → delta → narrative → event → evidence → raw_item → source
  priority_computation { formula_version, components{}, weights{}, result }
  artifact_version_refs[]
  input_tiers[]                        // sensitivity tier per input
  model_refs[]    // model + prompt version for inferred links only
```

The three tiers are **three fetches**. Forensics is heavy and rarely opened; loading it
with every impact would make Today slow for a view most days nobody uses.

### 2.3 `ScenarioSetView`

```
ScenarioSetView
  domain, horizon, as_of, run_id
  integrity_status                      // COMPLETE | DEGRADED | UNRELIABLE
  degraded_reason?
  unknown_mass { value, display_value } // rendered as its own hatched segment
  scenarios[] { id, slug, title, thesis,
                probability, display_probability, previous_display_probability,
                changed_since_previous, probability_method,
                drivers[] { narrative_title, direction, weight, trend },
                invalidators[], personal_implication?, impact_refs[] }
```

When `integrity_status = UNRELIABLE` the client renders the reason and **no probabilities**.
Suppression is a backend decision, not a client one.

### 2.4 `WorldStateView`

```
WorldStateView
  as_of, run_id, overall_regime, confidence { value, band }
  dimensions[] { key, label, category,
                 score, scale_min, scale_max, direction,
                 confidence { value, band }, freshness, evidence_count,
                 delta_since_previous?, materiality?,
                 personal_relevance,           // derived from impacts referencing it
                 score_history[],              // for the sparkline
                 primary_narratives[] }
  default_sort                                  // server-specified ordering
```

`personal_relevance` and `default_sort` come from the server precisely so the client is not
computing "does the owner care about this".

### 2.5 `PersonalStateView`

```
PersonalStateView
  as_of, base_currency, data_freshness_summary
  capital   { liquid_total, allocations[], currency_weights[], concentration, runway_months }
  income[]  { category, geography, currency, expected_range, confidence, active }
  geography[] { country, city?, role, residence_status, valid_until?, next_deadline?,
                mobility_friction, currency_exposure, career_fit }
  objectives[]  { ...Objective, is_proposed, accepted_at }
  preferences[] { higher, lower, strength, rationale }
  policies[]    { name, result: PASS|WARN|BREACH|UNKNOWN_DATA, objective_ref?, detail }
  values[]      { path, value, source, observed_at, freshness_state, correctable }
```

Every displayed value carries `source`, `observed_at`, `freshness_state` and `correctable`.
`values[]` is what `/settings/data` renders, and it is the mechanism behind
Principle 16 — corrections need to know what they are correcting.

### 2.6 `DecisionView`

```
DecisionView
  id, question, decision_type, status, created_at, valid_until?, review_date
  frozen_context {                       // as it was at decision_time
     impacts[], scenarios[], objectives_active[], policy_results[],
     personal_snapshot_ref, world_snapshot_ref }
  considered_options[]  { label, rationale, chosen: bool }
  atlas_recommendation?, owner_choice, rationale, confidence
  artifact_version_refs[]
  outcome? { outcome_type, decision_quality, outcome_quality, retrospective,
             forecast_comparison? }
  present_day_context?                   // only when explicitly requested
```

`frozen_context` is served by default; `present_day_context` requires an explicit query
parameter. The hindsight guard is enforced by the API, not by frontend discipline.

### 2.7 `CalibrationView`

```
CalibrationView
  resolved[] { question, resolution_criteria, resolved_at, outcome,
               owner_prediction?, atlas_prediction?, closer: owner|atlas|tie }
  by_domain[] { domain_key, n, owner_brier?, atlas_brier? }
  open[]      { question, resolve_by, latest_predictions[] }
```

Brier scores are **derived analytics**, computed server-side from the ledger primitives —
they are not canonical columns (`DATA_MODEL.md`).

### 2.8 `AskResponse` — Queue 17

```
AskResponse
  answer_blocks[] { type: claim|list|comparison|refusal, text, citations[] }
  citations[]     { entity_type, entity_id, label, as_of }
  state_used      { world_snapshot_ref, personal_snapshot_ref, as_of }
  refusal?        { reason }   // "not answerable from current state"
```

Answers render as **cards with citation chips**, never as a prose blob. A question Atlas
cannot answer from state produces a `refusal` — research is a separate, explicit action,
not a silent fallback.

---

## 3. Cross-cutting requirements

| Requirement | Reason |
| --- | --- |
| Every view carries `as_of` and `run_id` | Time is first-class (A02); the client renders the historical treatment from it |
| Every derived record carries `artifact_version_refs` | Replay integrity (ADR-0014) |
| Every value carries an effective sensitivity tier | The client renders the L3 indicator; it never infers tier (ADR-0010) |
| Six data-condition states are typed, not free text | The client has a designed state for each |
| Lists arrive ordered with their ordering key | No client-side ranking |
| Absent ≠ empty | Absence means "do not render"; `[]` means "render the empty state" |

## 4. Explicitly not requested

This document asks for **no** new backend capability, engine or entity beyond what Queues
02–16 already deliver. Every field above is either already in `DATA_MODEL.md`, or is a
deterministic projection of it (`display_probability`, `confidence.band`,
`personal_relevance`, `above_fold`, `coverage`). If any field turns out to require a new
engine, it is dropped from the read model — the UI adapts to the architecture, never the
reverse.
