# Model Routing

Which model serves which Atlas workload, and why. Concrete now, provider-neutral by
construction: the choices below sit behind `LLMProviderPort` (ADR-0010, ADR-0012), so
replacing any row is configuration.

Verified against the current Claude API reference rather than recalled — several of these
parameters changed in 2025–26 and stale patterns fail with a 400.

---

## 1. The three classes

| Class | Workload | Model | Config |
| --- | --- | --- | --- |
| **FAST** | Extraction, classification, entity resolution, **news relevance scoring** | `claude-haiku-4-5` | No `effort` parameter — it errors on Haiku 4.5. Strict tools. 200K context |
| **REASON** | Causal synthesis, impact inference, scenario challenge, the Atlas view | `claude-opus-5` | `thinking: {type: "adaptive"}`, `output_config: {effort: "high"}` — `xhigh` for scenario work |
| **WRITE** | Brief prose from already-approved structures | `claude-sonnet-5` | `thinking: {type: "adaptive"}`, `effort: "low"` — the structure is decided; only phrasing is generated |

Rationale for the split: FAST carries roughly 80% of call volume at 1/5 the input price of
REASON, and its work — pulling a proposition out of a paragraph, matching an entity, scoring
relevance — is not where judgement lives. REASON is where Atlas's actual value is produced,
so it gets the strongest model and real thinking depth. WRITE is deliberately *not* Opus:
by the time prose is written, every decision is already made, and paying reasoning rates to
phrase a settled conclusion is waste.

> `claude-opus-5` runs adaptive thinking **by default** — omitting `thinking` no longer
> means "no thinking" as it did on Opus 4.8. Do not disable it to save cost; lower `effort`
> instead. Disabled thinking on Opus 5 can emit a tool call as visible text that never runs.

## 2. Structured output is the validator

ADR-0004 requires that a model never writes canonical truth — it proposes, and a validator
checks schema, bounds and provenance. That validator is partly free:

- **`strict: true`** on every tool that proposes a mutation (world-state change, evidence
  extraction, objective proposal). Requires `additionalProperties: false` and `required` on
  the schema; guarantees `tool_use.input` validates exactly.
- **`output_config: {format: {...}}`** for non-tool structured responses. The old
  top-level `output_format` parameter is deprecated.

Atlas's own bounds checks (clamping scores, rejecting missing provenance, `unknown_mass`
integrity) still run afterwards — the API guarantees *shape*, not *legitimacy*.

## 3. Cost control

| Lever | Where it applies |
| --- | --- |
| **Prompt caching** | The stable system prompt and the dimension registry are identical across every extraction call. Cache them; verify with `usage.cache_read_input_tokens` — if it is zero across repeated calls, something volatile is in the prefix |
| **Batch API — 50%** | Overnight news relevance scoring and evidence extraction are not latency-sensitive. Results return in any order; key by `custom_id` |
| **Deterministic first** | Most ingestion, dedupe, scoring and policy work needs no model at all (ADR-0004). The cheapest call is the one not made |
| **Effort tuning** | Raise `effort` per route on measurement, not by default. `low` is right for subagent-shaped work |

Per-run cost is recorded in the `RunRecord`, so cost per useful brief item is measurable
rather than a month-end surprise.

## 4. Data tiers gate the routing

ADR-0010 outranks this document. Whatever the table above says, the provider port refuses a
request whose maximum sensitivity tier exceeds the destination's clearance:

- **L3** (residency documents, identity-linked deadlines, precise location, account
  identifiers) — **local model only**. Until one is deployed, Atlas does not reason over L3
  and says so.
- **L2** (balances, positions, weights) — external providers only after the deterministic
  transformation that strips identifiers and absolute amounts.
- **Embeddings inherit the tier of their source text**, which is why embeddings migrate to
  local inference first (`PROGRAM.md` §8).

## 5. Where this lands in the queue

`packages/atlas/providers` (Queue 04) implements the port. Prompts are versioned artefacts
under ADR-0014, and every call records provider, model, prompt version, tokens, cost,
latency, validation failures and the maximum tier transmitted.

## 6. Review cadence

Re-evaluate annually or when a model class ships that changes the FAST/REASON price ratio
materially. Model IDs here are exact strings — never append date suffixes.
