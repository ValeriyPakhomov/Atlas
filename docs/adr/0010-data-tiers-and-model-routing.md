# ADR-0010 — Data sensitivity tiers govern model routing

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Atlas holds a complete financial, geographic and residency picture of one person, and it
sends text to model providers in order to reason. Those two facts are in tension, and
`SECURITY.md` currently resolves it only by prohibition lists — what may never be stored.
It says nothing about what may be **transmitted**, to whom, under what transformation.

Without an explicit rule the default is the worst one: whatever text happens to be in
scope for a prompt goes to whatever provider is configured. Residency documents, precise
location and account identifiers would leave the perimeter as an accident of prompt
construction rather than as a decision.

This must be settled **before** any provider code is written (Queue 04 and every LLM call
thereafter), because retrofitting a routing rule onto existing call sites is exactly the
kind of change that gets applied to 90% of them.

## Decision

Every value Atlas handles carries a sensitivity tier, and the tier determines which model
class may receive it. The full operational specification is `docs/DATA_TIERS.md`; this ADR
fixes the binding rules.

| Tier | Content | May be sent to |
| --- | --- | --- |
| **L0** | Public: news, market prices, macro series, regulations, filings | any configured provider |
| **L1** | Derived public: events, narratives, world state, scenarios | any configured provider |
| **L2** | Personal structured: balances, positions, currency and geography weights, runway | external provider **only after transformation** — ratios or buckets, no identifiers, no institution names, no absolute amounts |
| **L3** | Sensitive personal: residency and document status, identity-linked deadlines, precise location, account and wallet identifiers, health, relationships | **local model only; never leaves the owner's perimeter** |

Binding rules:

1. **The tier travels with the data.** Tier is a property of the field in the schema, not
   a judgement made at the call site. A prompt assembled from tiered fields inherits the
   maximum tier present.
2. **Routing is enforced in the provider port, not in prompts.** `LLMProviderPort` rejects
   a request whose maximum tier exceeds the destination's clearance. A prompt cannot opt
   out, and a mistake is a typed error, not a leak.
3. **L2 leaves only transformed.** The transformation is deterministic code with its own
   tests: absolute amounts become weights or bucket labels, institutions become opaque
   account roles, and geography becomes ISO codes already public in L1.
4. **Until a local model is deployed, L3 is not reasoned over.** Atlas states the
   limitation rather than routing L3 externally "just this once". This is an accepted V1
   capability gap, recorded here so it is a decision rather than an oversight.
5. **Every model call records the maximum tier transmitted**, alongside provider, model
   and prompt version, so the transmission history is auditable after the fact.
6. **Local deployment is a clearance, not a bypass.** A local model is cleared for L3
   because the data does not leave the perimeter — not because local models are trusted
   more. All other rules, including A04 (no direct writes to canonical truth), still apply.

## Consequences

- The local-model work in `PROGRAM.md` §8 acquires a concrete purpose: it is what unlocks
  L3 reasoning, not a cost optimisation.
- Some V1 analysis is weaker than it could be, because L3 context is withheld from the
  strongest models. Accepted, and stated to the owner where it bites.
- Every provider integration carries an explicit clearance level in configuration, so
  adding a provider is a deliberate act.
- The transformation layer for L2 is real work (Queue 04 onward) and must be tested like
  arithmetic, because a leak here is silent.

## Enforcement

- A test asserts every persisted field has a declared tier; an untiered field fails the
  build rather than defaulting to permissive.
- A test asserts `LLMProviderPort` raises on a tier/clearance violation, for each tier.
- A test asserts the L2 transformation removes identifiers and absolute amounts, using
  fixtures containing planted identifiers.
- Run records include the maximum tier transmitted per call.

## Alternatives considered

- **Redact at prompt-construction time.** Rejected: puts the control at the most numerous
  and least reviewed layer, where one forgotten call site defeats it.
- **Trust provider zero-retention agreements and send everything.** Rejected: a contract
  is not a technical control, and it does not survive a provider change, a subprocessor,
  or a breach.
- **Run everything locally from day one.** Rejected: local reasoning quality is not yet
  adequate for the causal synthesis Atlas depends on (`PROGRAM.md` §8), and the delay
  would stall the whole programme.
