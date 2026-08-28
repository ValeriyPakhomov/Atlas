# ADR-0007 — Deterministic idempotency; semantic similarity proposes, never decides

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Blueprint §7.2 specifies five deduplication layers: exact external ID, canonical URL,
normalised content hash, **near-duplicate semantic similarity**, and event-level
entity/time/topic matching.

Layers 4 and 5 are model-dependent. If they participate in idempotency, then A08
(re-ingesting a batch creates no duplicates) and A07 (replay and live share one engine)
both break the moment an embedding model, its version, or its quantisation changes:
the same input yields a different merge decision, and a replay of last month's data
produces a different event graph than the original run did.

This is not hypothetical. Embedding models are upgraded routinely, and §8 of `PROGRAM.md`
plans an explicit migration to local embedding models — which would silently rewrite
history's shape if similarity were authoritative.

## Decision

Split the pipeline into a deterministic spine and an advisory layer.

**Deterministic and authoritative (idempotency):**

1. exact `(source_id, external_id)`;
2. canonical URL, using a fixed, versioned canonicalisation function;
3. normalised content hash, using a fixed, versioned normalisation function.

These three decide whether a `RawItem` is new. They involve no model, and their versions
(`parse_version`, `canonicalisation_version`, `hash_version`) are stored on the row. A
re-ingested batch is idempotent under these alone.

**Advisory (merge proposals):**

4. near-duplicate semantic similarity;
5. event-level entity/time/topic matching.

These produce an `EventMergeProposal`, never a silent merge:

```
EventMergeProposal
- id, run_id
- source_event_id, target_event_id
- method              # semantic_similarity | entity_time_topic
- score
- model_name, model_version, embedding_dim   # null for rule-based methods
- threshold_applied
- decision            # auto_accepted | pending | accepted | rejected
- decided_at, decided_by                      # system | owner
```

Rules:

1. **A proposal above the auto-accept threshold is applied and recorded.** The applied
   decision is persisted, so replay reads the stored decision rather than recomputing
   similarity. This is what makes replay deterministic across model changes (A07).
2. **Changing the embedding model does not rewrite history.** It changes only proposals
   generated after the change. Past merges keep the model version that produced them.
3. **A rejected proposal is remembered**, so the same pair is not re-proposed every run.
4. **Duplicate reporting still merges into one Event** (Queue 03 acceptance) — that
   requirement is met by the deterministic layers plus applied proposals, not by
   recomputation.

## Consequences

- Replay is genuinely deterministic: the event graph for a past `as_of` is reconstructible
  from stored decisions alone.
- The embedding model becomes swappable without a data migration, which unblocks the
  local-model plan in `PROGRAM.md` §8.
- Cost: an extra table and a decision lifecycle. Worth it — this is the difference between
  a system that can audit its own history and one that cannot.
- Some near-duplicates will be missed by the deterministic layers and only caught later by
  a proposal. Acceptable: a temporarily duplicated event is visible and fixable; a
  silently non-reproducible history is not.

## Enforcement

- Queue 03 acceptance gains: ingest a fixture batch, change the configured embedding model
  in the test, replay the same `as_of`, and assert the event graph is byte-identical.
- Idempotency tests use the deterministic layers only, with the advisory layer disabled,
  proving the spine stands alone.

## Alternatives considered

- **Pin the embedding model forever.** Rejected: it makes the local-model migration
  impossible and defers the problem rather than solving it.
- **Recompute similarity during replay with the pinned historical model.** Rejected:
  requires keeping every retired model runnable indefinitely, for no benefit over storing
  the decision the model produced.
