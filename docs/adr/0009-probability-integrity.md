# ADR-0009 — Probability integrity: incompleteness is explicit, precision is honest

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Two blueprint tensions concern the same thing — not claiming more than the method
supports.

**Incompleteness.** §13.1 requires that probabilities within a scenario set sum to 1. A06
requires failing loudly on missing critical data. When a driver cannot be evaluated
because its data is stale or absent, renormalising to 1 silently redistributes that
scenario's mass across the others, manufacturing confidence out of a data outage. The set
looks healthy precisely when it is least trustworthy.

**Precision.** A12 forbids fake precision. §22.1's dashboard mock shows `Base 48% / Bear
22% / Reflation 18% / Tail 12%`. Two significant figures on a subjectively-primed,
bounded-update probability implies a resolution the method does not have. Worse, it
invites the owner to read a move from 48% to 46% as signal when it is noise.

## Decision

### Incompleteness is a first-class member of the set

Every scenario set carries an explicit `unknown_mass` component:

```
ScenarioSet
- id, domain, horizon, as_of, run_id
- unknown_mass            # 0..1, mass not attributable to any scenario
- integrity_status        # COMPLETE | DEGRADED | UNRELIABLE
- degraded_reason?        # which drivers could not be evaluated
```

Rules:

1. `Σ scenario.probability + unknown_mass = 1`. The invariant holds without lying.
2. When a driver cannot be evaluated, its contribution moves to `unknown_mass` — it is
   **never** redistributed across the remaining scenarios.
3. Status thresholds are deterministic: `COMPLETE` when `unknown_mass` is below the
   configured floor; `DEGRADED` above it; `UNRELIABLE` above the ceiling, at which point
   the set is not used to derive decisions at all and the brief says so.
4. A `DEGRADED` or `UNRELIABLE` set is surfaced with its reason. Silence is not an option
   (A06).

### Presentation precision is bounded by method

1. **Store full precision; present rounded.** Probabilities are stored as exact decimals
   and displayed rounded to the nearest 5 percentage points.
2. **A change is shown only when it exceeds the rounding step.** A move from 0.48 to 0.46
   displays as "50% → 45%" only if it actually crosses the boundary; otherwise the brief
   reports no change, which is a truthful and valuable output (A11).
3. **Confidence is presented as a band** — `low` / `moderate` / `high` — with the numeric
   value available on request, never as a headline decimal.
4. **Never display more digits than `probability_method` supports.** A probability derived
   from a Brier-calibrated history may show finer resolution than one derived from a
   system prior; the method determines the display, and the method is stored.

## Consequences

- The owner can distinguish "we think Bear is unlikely" from "we cannot currently assess
  Bear" — a distinction the sum-to-1 formulation destroys.
- Scenario history becomes less noisy: fewer displayed changes, each meaning something.
- Cost: one extra column, one extra status, and slightly more work in the update
  mechanism. Trivial compared to acting on a fabricated probability.

## Enforcement

- Queue 10 acceptance gains: a fixture with an unevaluable driver must produce
  `unknown_mass > 0` and status `DEGRADED`, and must **not** change the other scenarios'
  probabilities.
- Property test: the sum invariant holds for every stored set.
- A rendering test asserts no surface emits a probability with finer resolution than the
  configured step.

## Alternatives considered

- **Renormalise and lower confidence.** Rejected: confidence is a different axis, and
  lowering it does not tell the owner *which* scenario is unassessed.
- **Round at storage time.** Rejected: destroys the ability to detect genuine slow drift
  across many small updates, and makes calibration scoring inaccurate.
