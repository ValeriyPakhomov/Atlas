# Decision Journal and Feedback Loop

*Full implementation: Queue 12.*

The journal is what turns Atlas from a generator of opinions into a system that can be
held to account.

## What is journaled

Every material output. A daily brief containing **no** decision is a valid outcome (A11).

For a material decision, store what was true *at decision time*:

- what Atlas observed;
- what changed;
- the evidence available then;
- scenario probabilities then;
- the personal state used;
- the policy state;
- the decision/action class;
- confidence;
- expiry / review time.

## Decision types (V1, non-executing)

`OBSERVE`, `VERIFY`, `WAIT`, `PREPARE`, `REVIEW_ALLOCATION`, `REVIEW_LOCATION`,
`REVIEW_POLICY`, `NO_ACTION` — by ADR-0003 none of these touch an external system.

## Outcome evaluation

Later, an `Outcome` answers:

- Was the factual premise correct?
- Did the scenario move as expected?
- Was the impact over- or under-estimated?
- Was the recommended preparation useful?
- Was confidence calibrated?

## Immutability

An `Outcome` is a **new row**. A retrospective never mutates the original decision, and
no LLM may rewrite history after the fact. This is the whole point: a decision record
that can be edited in hindsight cannot calibrate anything.

## Acceptance (Queue 12)

- A decision snapshot preserves the evidence and state used at decision time.
- A retrospective cannot mutate the original decision.
