# Cost Model

How Atlas stays cheap at scale, and the one property that makes it unusual: **it gets
cheaper as it learns.**

---

## 1. Where the money actually goes

Atlas reads on the order of 60 items a day — roughly 22,000 a year. Naively, each item is
an extraction call and each material change is a reasoning call. That naive shape is what
makes systems like this cost hundreds a month and get switched off.

The dominant cost is **model calls on ingestion volume**. Everything below attacks that
number rather than the price per call.

## 2. The triage funnel

Nothing reaches a model until deterministic code has failed to dispose of it. Each stage is
strictly cheaper than the one after it, and every stage records *why* it dropped something
(the Reading Room renders those reasons).

| Stage | Mechanism | Cost | Typical survival |
| --- | --- | --- | --- |
| 0 | Exact idempotency: external id, canonical URL, content hash | free | ~60% |
| 1 | **Exposure gate** — does this item name anything the owner is exposed to? | free | ~25% |
| 2 | Local embedding similarity to the exposure profile | local only | ~15% |
| 3 | `FAST` extraction on survivors | Haiku | ~15% |
| 4 | `REASON` synthesis, only where a material delta was produced | Opus | **~1–2%** |

**Stage 1 is the one that matters.** It is a trie match over the owner's exposure set —
instruments held, currencies carried, countries with a role, entities named in an
objective. An item about semiconductors never reaches a model if the owner has no
semiconductor exposure. This is not only cost: it is the same mechanism that stops the
brief from drowning the owner, so the cheap path and the good path are the same path.

Effect: roughly a **50–100× reduction in reasoning calls** versus sending everything.

## 3. The quiet day is the main cost control

If no world delta clears materiality, the entire downstream — impact engine, scenario
update, brief prose — is skipped. Most days are quiet.

This is why "a quiet day is a successful output" is not only a product principle. A quiet
day should cost **cents**, and a system that cannot be quiet cannot be cheap.

## 4. Atlas gets cheaper as it learns

Every `INFERRED_CAUSAL` impact that survives promotion to a `DIRECT_RULE` (ADR-0014) moves
permanently from a model call to deterministic code. The reasoning that cost tokens in
month three costs nothing in month nine, and it is faster and auditable besides.

This inverts the usual curve. Most AI products get more expensive per user over time as
context grows; Atlas's per-cycle model spend should **decline** as its rule base fills in.
Designing for that is a first-class goal, not a side effect.

## 5. Standing levers

| Lever | Applies to | Saving |
| --- | --- | --- |
| **Prompt caching** | The exposure profile and dimension registry are byte-identical across every extraction call in a cycle | ~90% of the cached input |
| **Batch API** | Overnight relevance scoring and extraction are not latency-sensitive | 50% |
| **Content-addressed extraction cache** | Same `content_hash` ⇒ same extraction, forever. Never re-extract, including during replay and backfill | 100% on repeats |
| **Incremental world state** | Recompute only dimensions whose supporting narratives changed | proportional |
| **Strict tools + structured outputs** | A malformed extraction is a wasted call; schema enforcement removes most retries | retry rate |
| **Local embeddings** | Free after hardware, and required for L2/L3 anyway (ADR-0010) | 100% of embedding spend |
| **Effort tuning** | Extraction does not need high effort; reasoning does | per route |

## 6. What we deliberately do not do to save money

- **Never skip provenance to save tokens.** An unattributed conclusion is worthless, so the
  saving is not a saving.
- **Never batch away freshness.** A stale conclusion delivered cheaply is worse than none.
- **Never downgrade the reasoning model to hit a budget.** If the budget binds, cut the
  *volume* reaching that model — the funnel, not the model, is the lever.
- **Never cache a personal-state read.** Cheap and wrong is the failure mode Atlas exists
  to avoid.

## 7. Target

| Phase | Model spend | Shape |
| --- | --- | --- |
| First slice (Queue 14) | **$10–30/month** | Funnel + caching + batch |
| Calibrated (Queue 12+) | **$20–60/month** | More decisions, more reasoning |
| Rules matured (year 2) | **$15–40/month** | Promotion offsets growth |
| Local FAST class | **under $20/month** | Only reasoning remains paid |

Per-run cost is recorded on the `RunRecord`, so **cost per useful brief item** is a
measured quantity rather than a monthly surprise.
