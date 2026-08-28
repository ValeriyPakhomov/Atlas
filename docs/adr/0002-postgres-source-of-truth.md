# ADR-0002 — PostgreSQL is the source of truth; semantic memory is not

- Status: Accepted
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

The failure mode that destroys systems of this shape is a vector store that answers
"how much BTC do I hold?" from an embedding of a six-month-old conversation. Semantic
recall is fuzzy, unversioned, un-auditable and silently stale. Atlas makes financial,
residency and mobility judgements where a stale answer is worse than no answer.

Constitution A01 and A02 require structured truth and point-in-time reasoning.

## Decision

PostgreSQL holds all canonical state: sources, raw items, evidence, events,
narratives, world-state snapshots and dimensions, personal state, accounts,
positions, cash, income, geography, goals, policies, scenarios, impacts, decisions,
outcomes and run records.

Semantic memory (`packages/atlas/memory`, Queue 18) sits behind a `SemanticMemoryPort`
and stores only **qualitative** material: prior reasoning, preferences, lessons,
recurring concerns, owner explanations. It is never read as an authority for a
quantity, a status, a probability, a threshold or a date.

Temporal modelling is mandatory on material tables:

- `event_time`, `published_at`, `observed_at`, `ingested_at`, `valid_from`, `valid_to`,
  `decision_time`, `evaluated_at` as applicable to the entity;
- state changes **append and close the previous validity interval**; they never
  `UPDATE` history in place;
- `run_id` and provenance columns on every derived row (A05).

Retrieval order for any query is fixed (blueprint §18.3): current structured state →
historical structured records → world state and narratives → semantic memory → fresh
research. Semantic memory is consulted last and can only add colour, never override.

Storage technology choices are constrained: PostgreSQL 16 with `pgvector` for
embeddings; Alembic for migrations; Redis optional for queueing and caching but never
authoritative. Introducing another database or queue technology requires a new ADR
(blueprint §34.7).

## Consequences

- Every engine can be replayed from the database alone; no hidden state in a vector
  index or in an LLM context window.
- More schema work up front, and migrations become a first-class discipline.
- `pgvector` lives in the same database, so semantic search cannot drift out of sync
  with the rows it describes.

## Enforcement

- Queue 01 acceptance requires migrations to apply from zero.
- Queue 07 acceptance requires that stale semantic memory cannot alter a personal-state
  snapshot.
- Queue 18 acceptance requires that memory cannot mutate canonical state outside an
  explicit validated workflow.

## Alternatives considered

- **Vector-first / memory-first architecture.** Rejected by A01; the blueprint calls
  this out as an explicit anti-pattern (§1.1).
- **Event-sourcing with a separate event-store product.** Rejected for V1: append-only
  tables in Postgres deliver the replay guarantee without a second technology.
