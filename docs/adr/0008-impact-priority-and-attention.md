# ADR-0008 — Impact priority is a weighted geometric composite; attention is separate

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Blueprint §12.3 proposes:

```
impact_priority = severity × exposure × confidence × urgency × (1 + irreversibility_weight)
```

Two problems.

**Numerical.** A product of four factors normalised to 0..1 collapses toward zero and
loses discrimination exactly where it matters. Four factors at 0.7 give 0.24; at 0.5 they
give 0.06. Ranking becomes dominated by whichever factor happens to be lowest, and small
measurement noise in one component reorders the list. The trailing `(1 + irreversibility)`
term mixes multiplicative and additive semantics on a different scale, so the formula is
not dimensionally coherent.

**Conceptual, and more serious.** Multiplying by `confidence` buries high-severity
low-confidence impacts. But a severe, irreversible, poorly-evidenced impact is not
low-priority — it is precisely the case that warrants a `VERIFY` decision. Ranking it away
is the exact failure A06 and A11 exist to prevent: the system quietly discards the thing
the owner most needs to look at.

## Decision

**Two separate quantities**, both stored with their components.

### 1. Priority — how much this matters if true

A weighted geometric mean of the magnitude factors, scaled by irreversibility:

```
priority = (severity^ws · exposure^we · urgency^wu)^(1/(ws+we+wu)) × (1 + irreversibility)
```

- All inputs normalised 0..1; `irreversibility` in 0..1, so the multiplier is 1..2.
- Weights `ws, we, wu` are configuration, defaulting to 1. Tuning is a data change.
- The geometric mean keeps the **conjunctive** semantics that made a product attractive —
  zero exposure still yields zero priority, correctly — while staying on a 0..1 scale that
  discriminates across the range.
- `confidence` is deliberately **absent**.

### 2. Attention — what the owner should do about it now

Confidence enters here, as a routing decision rather than a ranking multiplier. Atlas has
one attention taxonomy across impacts, briefs and alerts:

| Attention class | Meaning |
| --- | --- |
| `ACTION` | High materiality and sufficient confidence; surface with a decision candidate. The top interrupting class still requires a qualifying deterministic rule or strong evidence. |
| `VERIFY` | Potentially high materiality with insufficient confidence; surface the evidence needed to resolve it. |
| `REVIEW` | Material but non-urgent, or not yet eligible for interruption; include in deliberate review. |
| `BACKGROUND` | Record for context and learning; do not interrupt or lead the brief. |
| `SUPPRESS` | Duplicate, stale, invalid or below the configured relevance floor; retain the suppression reason. |

Thresholds and qualifying rules are configuration, and classification is deterministic
code. V1 does not model a numeric "expected value of interruption": Atlas has no behavioural
data that would make such a number honest yet (A12).

### Storage

Every component is persisted individually alongside the two derived values, plus the
weight set and threshold set applied. A ranking is therefore always explainable and
always reproducible for a past run (A05, A07).

## Consequences

- The brief can honestly say "this may be significant and we are not sure — here is what
  would settle it", which is a more useful output than a confidently ranked list.
- Ranking becomes stable under small perturbations in any single component.
- Tuning weights does not require a deployment, but it **does** change historical
  rankings if recomputed — so rankings are stored per run, never recomputed on read.
- Slightly more complex than the blueprint formula. Justified: the simple version is
  wrong in a way that hides risk.

## Enforcement

- Queue 09 acceptance gains: a fixture with high severity, high irreversibility and low
  confidence must classify as `VERIFY` and must appear in the brief.
- Property test: priority is monotonic in each factor, lies in 0..2, and is zero when any
  magnitude factor is zero.
- No code path may multiply confidence into priority.

## Alternatives considered

- **Weighted arithmetic sum.** Rejected: loses the conjunctive property — an impact with
  zero exposure would still score, which is meaningless.
- **Keep the product, add a separate "uncertain but severe" list.** Rejected: two ranking
  systems that disagree, with the product still mis-ranking within its own list.
