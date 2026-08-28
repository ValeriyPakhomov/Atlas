# ADR-0004 — Deterministic code computes; LLMs interpret

- Status: Accepted
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

An LLM that reports a runway of "about 14 months" is worse than useless: it is
confidently wrong at a decision point where the owner will act. Constitution A03,
A04, A06 and A12 draw a hard line between arithmetic and interpretation.

## Decision

**Deterministic code owns**: portfolio weights, currency and geography exposure,
concentration, runway, drawdown and mark-to-market, policy evaluation, freshness
scores, evidence counts, dedupe hashes, alert thresholds, scenario scoring mechanics,
probability normalisation and impact priority arithmetic.

**LLMs own**: extraction, classification, entity resolution proposals, causal
synthesis, challenge and falsification, and prose. An LLM may *propose* a structured
mutation; it never writes canonical state directly (A04). Every proposal passes a
typed validator that checks schema, bounds, provenance and permission before storage.

Rules that follow:

1. Every deterministic operator is a pure function: typed in, typed out, no network,
   fully unit-tested, explicit about missing data.
2. **Fail loud on missing critical data** (A06). An owned asset with no price yields an
   explicit incomplete result. Never a guessed number, never a silent zero, never an
   LLM estimate standing in for a market value.
3. **Time is injected, never read.** All library code takes an `as_of` derived from a
   `Clock` (`atlas.domain.clock`). A live cycle and a historical replay differ only in
   the injected clock and data source (A02, A07).
4. **Bounded updates.** State and probability changes are clamped by deterministic
   limits; a single low-quality item cannot move a scenario by an arbitrary margin.
5. **Calibrated confidence** (A12). Confidence derives from evidence quality, source
   diversity, model disagreement, freshness and historical calibration. No fabricated
   precision.
6. **Idempotency** (A08). Every external record carries an idempotency key or stable
   content hash; re-ingesting a batch creates no duplicate events or decisions.
7. Prompts are versioned assets under source control, not inline strings. Every model
   call records provider, model, prompt version, tokens, cost, latency, validation
   failures and retries.

## Consequences

- More code than "ask the model". That is the point: the arithmetic is auditable,
  testable and replayable.
- Deterministic paths are cheap and fast; model spend concentrates where judgement
  actually lives.
- Some outputs will read as "incomplete". Correct — see A06.

## Enforcement

- `tests/unit/test_determinism_guards.py` scans every library source file for direct
  wall-clock reads (`datetime.now`, `date.today`, `time.time`, …) outside the clock
  module and fails the build.
- Queue 08 acceptance requires full unit coverage of critical arithmetic branches and
  no LLM dependency in the portfolio engine.
- Queue 13 acceptance requires deterministic fixture replay of the daily cycle.

## Alternatives considered

- **Let the model compute and validate the answer afterwards.** Rejected: validation of
  a number needs the number, which means writing the deterministic operator anyway.
- **Function-calling with a calculator tool.** Rejected as the primary path: it makes
  arithmetic non-replayable and dependent on model routing. Deterministic operators
  are called directly by the cycle.
