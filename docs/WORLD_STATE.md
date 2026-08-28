# World State Engine

*Full implementation: Queue 06. This document fixes the contract.*

World State is a **state transition system**, not a summariser, and not a large LLM
paragraph. It is a versioned set of scored dimensions with provenance.

## Inputs and outputs

Inputs: previous snapshot; new and changed narratives; deterministic market
observations; source freshness; contradiction and disagreement metrics.

Outputs: a new snapshot; a set of typed deltas; provenance; explicit uncertainty.

## Dimension scale

Each dimension carries `score` on a normalised −3..+3 scale, a `direction`
(`rising | falling | stable | uncertain`), `confidence` (0..1), `freshness`,
`evidence_count`, a `rationale` and its `primary_narratives`.

### V1 dimensions (start with ten)

`macro.liquidity`, `macro.rates`, `macro.usd`, `markets.risk_appetite`,
`crypto.regime`, `crypto.leverage`, `geography.turkey_economy`, `geography.turkey_fx`,
`technology.ai_capability`, `geopolitics.global`

### Full V1 key space (added only as evidence justifies)

`macro.growth`, `macro.inflation`, `markets.volatility`, `crypto.liquidity`,
`energy.oil`, `commodities.food`, `geopolitics.europe`, `geopolitics.middle_east`,
`technology.ai_capex`, `regulation.crypto`, `regulation.ai`,
`geography.turkey_social_stress`, `migration.eu`, `migration.us`, `climate.food_water`

Hundreds of dimensions are an anti-goal.

## Update contract

An LLM may propose a change only in this shape:

```json
{
  "dimension": "macro.liquidity",
  "previous_score": 0,
  "proposed_score": 1,
  "direction": "rising",
  "confidence": 0.72,
  "materiality": 0.64,
  "supporting_narratives": ["..."],
  "contradicting_narratives": ["..."],
  "rationale": "..."
}
```

A deterministic validator clamps scores to the scale, applies bounded step limits,
and **rejects any proposal with missing provenance** (A04, A05).

## V1 approach

No black-box ML model. Deterministic market features, source and evidence weights, a
bounded LLM proposal, deterministic materiality and confidence rules, and a
human-reviewable rationale. Auditable and replayable beats clever.

## Acceptance (Queue 06)

- World State replays two historical fixture days identically.
- Only **material** changes produce deltas — an unchanged world produces no noise.
- Every delta carries provenance back to evidence.
