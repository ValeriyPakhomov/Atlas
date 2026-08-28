# Architecture Decision Records

An ADR records a decision that constrains future work. The Architecture Constitution
(`docs/ARCHITECTURE.md`, rules A01–A12) is binding; **an ADR is the only instrument
that may change it.**

## Rules

- One decision per record. Numbered sequentially, never renumbered.
- Status is one of `Proposed`, `Accepted`, `Superseded by ADR-NNNN`, `Rejected`.
- Accepted ADRs are immutable. To change a decision, write a new ADR that supersedes
  the old one and update the old record's status line only.
- If a build-queue item shows that an accepted decision is wrong, **stop the queue item
  and propose an ADR** rather than quietly implementing something else (blueprint §34.10).

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-monorepo.md) | Single Atlas monorepo with an enforced dependency rule | Accepted |
| [0002](0002-postgres-source-of-truth.md) | PostgreSQL is the source of truth; semantic memory is not | Accepted |
| [0003](0003-read-only-v1.md) | Atlas V1 is read-only with respect to external systems | Accepted |
| [0004](0004-deterministic-compute.md) | Deterministic code computes; LLMs interpret | Accepted |
| [0005](0005-open-source-boundaries.md) | Upstream projects are consumed at a boundary, never forked | Accepted |

## Template

```markdown
# ADR-NNNN — Title

- Status: Proposed
- Date: YYYY-MM-DD
- Supersedes / Superseded by: —

## Context
## Decision
## Consequences
## Enforcement
## Alternatives considered
```
