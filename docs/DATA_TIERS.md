# Data Tiers and Model Routing

Operational specification for ADR-0010. This document is normative: it is the reference a
queue item consults when deciding what tier a new field carries and where its content may
travel.

## Why this exists

Atlas reasons by sending text to models. It also holds the owner's complete financial,
residency and geographic picture. Absent an explicit rule, the boundary between those two
facts is decided implicitly, at each call site, by whoever wrote that prompt. This
document makes it a schema property enforced at one chokepoint instead.

## The four tiers

### L0 — Public

Content that is public regardless of Atlas: news articles, market prices, macro series,
central-bank releases, regulations, filings, exchange reference data.

Clearance: any configured provider. No transformation.

### L1 — Derived public

Atlas's interpretation of L0: events, evidence propositions, narratives, world-state
snapshots, dimensions, deltas, scenario definitions and their drivers.

L1 is derived **only** from L0 and never embeds personal state. A narrative may say "TRY
under pressure"; it may not say "the owner holds TRY".

Clearance: any configured provider. No transformation.

### L2 — Personal structured

The owner's financial shape: balances, positions, cash by currency, asset-class and
currency weights, concentration, runway, monthly burn, income-stream categories, Objectives,
policy thresholds.

Clearance: external providers **only after the L2 transformation** below. Local models:
unrestricted.

### L3 — Sensitive personal

Residency and visa status, identity-linked deadlines, document details, precise current
location, account and wallet identifiers, institution names tied to the owner, health,
relationships, and any free text the owner wrote about their circumstances.

Clearance: **raw L3 is local-model only.** A deterministic privacy projection may produce
a separate L2 derivative, but never reclassifies or mutates the L3 source.

Until a local model is deployed (`PROGRAM.md` Phase 3), Atlas does not reason over L3. It
stores it, computes deterministically over it, and reports the limitation where it
affects an answer.

## Schema and effective classification

Every relevant persisted value has three classification properties:

| Property | Meaning |
| --- | --- |
| `schema_max_tier` | Highest tier the field contract permits |
| `schema_default_tier` | Classification used when the ingestion contract supplies no more specific value |
| `effective_tier` | Actual classification of this stored record/value |

`effective_tier` may not exceed `schema_max_tier`. Mixed-content fields such as
`RawItem.raw_text` carry an effective tier on the record; the column declaration alone is
not sufficient. Unknown or unclassified personal free text fails high to L3. A derived or
assembled value inherits the maximum effective tier of every input.

## Privacy projection

Deterministic, allowlist-based code, unit-tested against fixtures containing planted
identifiers. Applied before any personal content reaches an external provider. Projection
can consume L2, or raw L3 when producing a distinct L2 derivative; the source is unchanged.

| Removed or replaced | Becomes |
| --- | --- |
| Absolute amounts (`$47,312 USD`) | Weight or bucket (`31% of liquid`, `runway 14–16 months`) |
| Institution names | Opaque role (`exchange_a`, `bank_eu_1`) |
| Account and wallet identifiers | Dropped entirely |
| Instrument identifiers of owned positions | Kept — instrument identity is L0 |
| Precise city | Country ISO code, already public in L1 |
| Free-text owner notes | Dropped — reclassify as L3 |

The transformation is lossy on purpose. A model reasoning about "31% of liquid net worth
in one asset, runway 14 months" produces the same causal analysis as one given exact
figures, because the arithmetic was never the model's job (ADR-0004).

Every projection writes a transformation receipt containing the source reference, source
effective tier, transformer/version, output tier, transformation time and validation
result. A validation failure produces no routable derivative.

### What the transformation does not do

It does not attempt anonymisation in the formal sense. A sufficiently determined observer
combining transformed L2 with public context could narrow the owner. The transformation
reduces exposure; the actual control for anything identity-bearing is tier L3 and local
execution.

## Enforcement points

1. **Schema and value.** Every persisted field declares maximum/default tiers, and every
   relevant stored value carries an effective tier. Missing mixed/free-text classification
   fails high.
2. **Prompt assembly.** A prompt's tier is the maximum effective tier of its inputs.
   Computed, never asserted by the caller.
3. **Provider port.** `LLMProviderPort` holds each provider's clearance and raises a typed
   `TierViolation` when a request exceeds it. This is the chokepoint; it is the only place
   the rule is enforced, so it is the only place it can be got wrong.
4. **Run record.** Each model call records the maximum tier transmitted, so an audit can
   answer "what has ever left the perimeter" from stored data.

## Storage perimeter and model perimeter

- The **model perimeter** forbids raw L3 transmission to an external model provider.
- The **storage perimeter** permits L3 in the selected managed PostgreSQL deployment under
  project access controls, TLS, encryption at rest and tested off-provider backups.

Managed storage does not grant model clearance. Secrets absolutely prohibited by
`SECURITY.md` remain forbidden regardless of tier.

## Provider clearance configuration

```
provider:
  anthropic:   { clearance: L2, transform_required: true  }
  openai:      { clearance: L2, transform_required: true  }
  local_vllm:  { clearance: L3, transform_required: false }
  local_llama: { clearance: L3, transform_required: false }
```

Clearance is configuration so it is reviewable in one place, and adding a provider is a
deliberate act rather than a side effect of setting an API key.

## Embeddings carry tiers too

An embedding of L3 text is L3. Vectors are not anonymous — they support reconstruction
attacks well enough that treating them as opaque is unsafe.

Consequence: **the embedding model for L2 and L3 content must be local.** This is the
concrete reason `PROGRAM.md` §8 puts embeddings first in the local migration order, ahead
of the much larger extraction workload.

## Interaction with semantic memory

Semantic memory (Queue 18) stores qualitative context — much of it L3 by nature ("the
owner does not want a base with high water risk"). It therefore runs against a local
embedding model and a local store, and its retrieval results inherit L3.

This is compatible with ADR-0002: memory remains non-authoritative. Tiering constrains
where it may be processed; ADR-0002 constrains what it may claim.

## Reclassification

Tiers only move upward without ceremony. Moving a field **down** — deciding something is
less sensitive than first classified — requires the same review as an ADR change, because
it retroactively permits transmission of data already collected under a stricter promise.

## Founder decision

Transformed L2 may reach an approved external provider; raw L3 may not. This can be
tightened later by lowering provider clearance to L1 without changing domain contracts.

Production persistence uses Neon PostgreSQL 16 in AWS Frankfurt (`eu-central-1`). Local
development and tests use Docker PostgreSQL 16. Atlas uses standard PostgreSQL,
SQLAlchemy, Alembic and `DATABASE_URL`; no Neon-specific dependency may enter the domain.
Administrative and migration workflows use a direct connection where required; application
runtime may use a pooled connection. Logical backups are encrypted and stored off-provider.
