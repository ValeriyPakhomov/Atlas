# Personal State Engine

*Full implementation: Queue 07. This document fixes the contract.*

Personal State has exactly two layers, and their roles are never reversed.

## 1. Canonical structured state (authoritative)

PostgreSQL tables for current facts: accounts, cash balances, positions, income
streams, geography and residency status, accepted Objectives and Preferences, policies,
critical dates. Every row is
temporally versioned (`valid_from`/`valid_to`), so a snapshot for any past `as_of` is
reproducible from point-in-time records.

## 2. Qualitative memory (never authoritative)

Semantic memory holds explanations, preferences, reasoning and context.

```
Structured (authoritative)          Semantic (colour only)
current_base = Istanbul             "Owner values geographic optionality and does not
candidate_base = Milan               want a long-term base with high water and
policy.liquid_runway_months >= 12    geopolitical risk or persistent nervous-system load."
```

Semantic memory may **never** be the source for portfolio quantities, balances,
residence status, scenario probabilities, policy thresholds, current location or
critical dates (ADR-0002).

Owner intent is structured state, not semantic colour. At a requested `as_of`, only
accepted active Objective and Preference versions whose validity interval contains that
time are authoritative (ADR-0011). Atlas proposals remain inert until explicit acceptance.

## Freshness and incompleteness

`PersonalStateSnapshot.data_freshness` is computed, not asserted. An owned asset with
no price produces an **explicitly incomplete** snapshot, not an estimate (A06). Downstream
engines must handle and surface incompleteness rather than rounding it away.

## Mutation path

Personal state changes arrive through a trusted data adapter or a human-confirmed
structured update (`POST /personal/updates`). An LLM may propose; it never writes
(A04). Every mutation is audit-logged (`SECURITY.md`).

## Owner-genericity

The owner is a single-user profile, not a hard-coded person. No owner specifics in core
domain code — a multi-user product must remain possible without a domain rewrite.

## Acceptance (Queue 07)

- The current snapshot is reproducible from point-in-time records.
- Stale semantic memory cannot alter it.
