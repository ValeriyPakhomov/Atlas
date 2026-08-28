# Scenario Engine

*Full implementation: Queue 10.*

Scenarios are **hypotheses about future world trajectories**, not "predictions from AI".

## Structure

A small number of scenarios per domain and horizon: 3–5, never dozens.

Horizons: `7–30 days`, `3–6 months`, `12–24 months`.

Example market set: `soft_landing`, `reflation`, `recession`, `liquidity_melt_up`,
`geopolitical_shock`.

Each scenario has drivers (`ScenarioDriver`) mapping narratives to direction and
weight, so a probability change is always traceable to a narrative change.

## Probability discipline

Probabilities within a set **sum to 1**. The update mechanism is deterministic where it
counts:

1. start from human or system priors;
2. map narratives to scenario drivers;
3. calculate weighted evidence pressure (deterministic);
4. generate an LLM explanation of the proposed change;
5. apply **bounded** deterministic update limits;
6. renormalise;
7. store previous and new values with the run that caused the change.

A single news item may not move a scenario by an arbitrary large margin. The bound is a
parameter, not a model judgement.

## Calibration

When a horizon resolves, store the outcome and compute a Brier score (or another proper
scoring rule) where the outcome is objectively resolvable. The purpose is to learn
**which scenario families Atlas is bad at** — calibration, not decoration (A12).

## Acceptance (Queue 10)

- Probabilities are always valid (sum to 1, within bounds).
- One low-quality source cannot cause an extreme jump.
- Every change is replayable from stored inputs.
