# ADR-0013 — Autonomy ladder and the Execution Gateway boundary

- Status: Proposed
- Date: 2026-08-28
- Extends: ADR-0003 (does **not** supersede it)

## Context

ADR-0003 holds: Atlas V1 performs no external mutation, and `execution_enabled` is
`Literal[False]` with no code path to enable it. That remains correct.

But "never" and "unspecified" are different. If the architecture never describes what safe
execution would look like, then the day a genuinely useful bounded action appears —
renewing a residency application, rebalancing to satisfy a policy the owner already
authored — the pressure will be to add it wherever it is easiest. That is how execution
arrives: not by decision, but by increment.

The blueprint's non-goals list execution; it does not say what would have to be true for
execution to be safe. This ADR says it, without enabling anything.

## Decision

### The ladder is two-dimensional

A single global "autonomy level" is the wrong model: reading market data and moving funds
are not points on one line. Authority is `(domain, level, bounds, expiry)`.

**Levels:**

| Level | Name | Meaning |
| --- | --- | --- |
| L0 | OBSERVE | Read and store only |
| L1 | ADVISE | Recommend; the owner acts entirely outside Atlas |
| L2 | SIMULATE | Model an action's effects; nothing leaves the system |
| L3 | PREPARE | Produce an exact, validated `ActionProposal`; never transmit it |
| L4 | CONFIRMED | Owner approves one specific proposal; the Gateway transmits it |
| L5 | BOUNDED | Deterministic, pre-authorised actions inside hard limits |
| L6 | DISCRETIONARY | A model chooses and performs consequential actions |

L2 and L3 are **not ordered** — preparation does not require simulation, and either may
exist without the other. They are distinct capabilities at comparable risk, not rungs.

**Atlas V1 operates at L0–L1 in every domain.** L2 is reachable within V1 (it is pure
computation and touches nothing external). L3 and above require the Gateway below to
exist first.

### L6 is architecturally impossible, not merely forbidden

The Execution Gateway accepts an action only when presented with a matching
`(CapabilityGrant, Approval)` pair. There is no code path that accepts a model-generated
action without both. A prohibition in a document can be forgotten during a refactor; a
missing function signature cannot.

### The Execution Gateway is a separate system

```
Atlas Core  →  ActionProposal  →  Policy / Risk Gate  →  EXECUTION GATEWAY  →  broker / registry / exchange
   (no keys)     (typed, signed)      (deterministic)     (separate process,
                                                           separate creds,
                                                           separate schema)
```

Non-negotiable properties:

1. **Separate process and deployment.** Not a module of the API. Compromising Atlas Core
   must not yield the ability to move anything.
2. **Atlas Core holds no keys.** No seed phrases, private keys, withdrawal secrets,
   banking credentials or unrestricted broker authority — ever, at any autonomy level.
   This is unchanged from `SECURITY.md` and is not relaxed by any grant.
3. **Grants are bounded and they expire.** A `CapabilityGrant` names the domain, maximum
   level, hard limits (maximum value per action, maximum frequency, permitted
   counterparties) and an expiry date. Renewal is a deliberate act. **The failure mode of
   L5 is a policy written once against a world that then changed**; expiry is the control
   that bounds it.
4. **Every action is idempotent.** Each proposal carries an idempotency key; the Gateway
   guarantees at-most-once transmission (A08).
5. **The Gateway owns its own audit schema.** `ExecutionRecord` lives in the Gateway, not
   in Atlas Core. Atlas Core learns outcomes by reading back a record, exactly as it reads
   any other external observation — with provenance.
6. **Enabling any of this requires an ADR superseding ADR-0003**, plus a security review.
   This ADR does not enable it.

### What is reserved now

`ActionProposal`, `CapabilityGrant`, `Approval` and `ExecutionRecord` are **reserved
vocabulary only** (`DATA_MODEL.md`). No tables in Queue 01. An empty table is an
invitation; a documented reservation is a boundary.

## Consequences

- The path to safe execution exists on paper, so it will not be improvised later under
  time pressure.
- V1 behaviour is completely unchanged. `execution_enabled` stays `Literal[False]`.
- When execution is eventually considered, the question is "should we build the Gateway",
  which is a visible, reviewable decision — not "should we add a call here".

## Enforcement

- `tests/unit/test_read_only_guarantee.py` continues to assert V1 behaviour.
- A boundary test asserts no `packages/atlas` module imports a broker, exchange or wallet
  SDK.
- Decision types stay the eight non-executing types from ADR-0003.

## Alternatives considered

- **Say nothing until execution is needed.** Rejected: silence is what lets execution
  arrive incrementally through the easiest available path.
- **One global autonomy level.** Rejected: it forces read-only market data and fund
  movement onto the same scale.
- **Gateway as a module behind a flag.** Rejected: a flag is not a security boundary, and
  it puts credentials in the same process as the reasoning that requests their use.
