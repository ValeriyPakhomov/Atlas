# ADR-0003 — Atlas V1 is read-only with respect to external systems

- Status: Accepted
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Atlas reasons about money, exchange accounts, residency status and relocation. The
blueprint is emphatic (§0, §1.1, A09, §31) that Atlas is not a trading bot, a
robo-adviser or an execution agent. The risk is not that someone deliberately adds
trading; it is that an "obviously harmless" write path — a rebalance helper, a form
submitter, a wallet call — arrives incrementally.

## Decision

Atlas V1 performs **no** external mutation. It may read state and produce analysis. It
must not place trades, move funds, sign transactions, submit applications, or mutate
any critical external system.

Consequences that follow directly:

- Decision types are non-executing by construction:
  `OBSERVE`, `VERIFY`, `WAIT`, `PREPARE`, `REVIEW_ALLOCATION`, `REVIEW_LOCATION`,
  `REVIEW_POLICY`, `NO_ACTION`.
- Provider credentials must be read-only, with trading and withdrawal disabled at the
  provider. A credential that *can* withdraw is a violation even if unused.
- MCP tools (Queue 17) are read-only, except explicitly scoped owner updates to
  personal state, which are human-confirmed.
- "Do nothing" is a first-class output (A11), not a degraded one.

`Settings.execution_enabled` is typed `Literal[False]` and frozen. There is no
environment variable, flag or override that turns it on; setting `ATLAS_EXECUTION_ENABLED`
raises a validation error at startup. The field exists so the guarantee is assertable
and observable, not so it can be flipped.

Any future execution capability is a **separate subsystem and security boundary**
requiring its own ADR, its own credentials, its own audit trail and explicit
per-action human approval. It is not a feature flag in this codebase.

## Consequences

- Atlas cannot act on a time-critical opportunity by itself. Accepted: the owner is
  the actor, and the cost of a wrong autonomous action here is unbounded.
- Some ingestion is limited to read-only API scopes, which occasionally means less data.
  Accepted.

## Enforcement

- `tests/unit/test_read_only_guarantee.py` asserts the default, asserts that the
  environment cannot enable execution, and asserts settings immutability.
- `/health` reports `execution_enabled` so the guarantee is visible in production.
- Code review rejects any outbound call with a side effect on an external account.

## Alternatives considered

- **Execution behind a feature flag.** Rejected: a flag is an invitation, and the
  blueprint requires a separate security boundary (§26).
- **"Prepare and stage" order objects.** Rejected for V1: staging is one refactor away
  from sending, and `PREPARE` decisions already capture the owner-facing value.
