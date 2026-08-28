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
| [0006](0006-dimensions-as-data.md) | World-state dimensions are data, not code | **Proposed** |
| [0007](0007-deterministic-idempotency.md) | Deterministic idempotency; semantic similarity proposes, never decides | **Proposed** |
| [0008](0008-impact-priority-and-attention.md) | Impact priority is a weighted geometric composite; attention is separate | **Proposed** |
| [0009](0009-probability-integrity.md) | Probability integrity: incompleteness explicit, precision honest | **Proposed** |
| [0010](0010-data-tiers-and-model-routing.md) | Data sensitivity tiers govern model routing | **Proposed** |

ADRs 0006–0010 resolve contradictions found in Blueprint v1 and are **awaiting owner
acceptance**. Each blocks a specific queue item — see the table in `../BUILD_QUEUE.md`.
They are written as decisions rather than options because the blueprint requires a
proposed ADR, not a discussion, when the architecture is found wanting (§34.10); the
owner accepts, amends or rejects.

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
