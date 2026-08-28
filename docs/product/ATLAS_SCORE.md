# The Atlas Score

A single number on the home screen, plus a score per domain. This document defines how
they are computed, because **a score that hides its inputs is astrology with a progress
ring**.

The rule that makes it safe: *the score is derived, never judged.* No model produces it.
Every point is traceable to a stored input, and tapping the score lists what moved it.

---

## 1. Domain Score — 0…100

Computed per domain (`capital`, `turkey`, `mobility`, `career`, `markets`, …) from things
Atlas already stores.

```
world_component  = Σ  w_d · norm(dimension_score_d)      # −3…+3 → 0…100, w_d = owner exposure
policy_penalty   = Σ  { WARN: −8, BREACH: −28, UNKNOWN_DATA: excluded }
impact_drag      = Σ  priority_i × 22   for adverse impacts of class ACTION|VERIFY|REVIEW
impact_lift      = Σ  priority_i × 14   for favourable impacts

score = clamp( world_component − policy_penalty − impact_drag + impact_lift , 0 , 100 )
```

Notes that matter more than the constants:

- **Weights are exposure, not opinion.** `w_d` comes from the owner's actual position —
  currency weights, geography roles, income attribution. A dimension the owner has no
  exposure to contributes nothing.
- **Lift is weighted lower than drag (14 vs 22)** deliberately. A favourable change rarely
  compensates for an equal-magnitude adverse one when the adverse one is irreversible.
- **Every contribution row is persisted** with its label and value. The domain screen is
  a rendering of those rows, not a second computation.
- **The constants are configuration**, versioned as artefacts (ADR-0014), so a change to
  them is visible and replayable rather than a silent re-scoring of history.

## 2. Overall Atlas Score

Weighted mean of the domain scores, weighted by the **priority of the objectives each
domain serves** (ADR-0011). A domain the owner has no active objective in is excluded
rather than averaged in at a neutral value.

## 3. Staleness — the rule that keeps the number honest

> If any input to a domain is past its freshness SLA, that domain reports `—`, not a
> number, and is excluded from the overall score with the exclusion stated.

This is A06 applied to the most tempting place to violate it. A score is the easiest thing
in the product to fake, because nobody can see it is wrong. `Markets — 9d` on the home
screen is a better product than `Markets 61` computed from nine-day-old positions.

## 4. Delta over level

The number is the context; **the change is the message.** `68 ▽6` reads correctly; a bare
`68` does not, because the owner has no scale for it. The screen always shows the movement
and, on tap, which domains produced it.

Movement below 2 points displays as unchanged. Score noise is not news.

## 5. News Relevance Score — 0…100

Not "how important is this story" — Atlas has no view on that and does not need one. It is
**how much this story bears on you**:

```
relevance = 100 × reliability(source_class) × novelty × materiality × exposure_match
```

| Factor | Source |
| --- | --- |
| `reliability` | Source class A/B/C/D (`SOURCE_POLICY.md`) — A 1.0, B 0.85, C 0.6, D 0.35 |
| `novelty` | 0 if the event is already in the store with no new evidence |
| `materiality` | The world-delta materiality the item contributes to, or 0 |
| `exposure_match` | Owner exposure to the entities, geographies and assets named |

Below a floor of **30** an item is not surfaced — but it **stays visible in the Sources
screen with its discard reason**. Seeing why 58 of 63 items were dropped builds more trust
than reading them would, and it is the surface where the owner corrects Atlas.

Only `novelty` and `exposure_match` need a model, and only to resolve entities — the
arithmetic is deterministic.

## 6. What the score must never do

- Never be produced or adjusted by a model.
- Never be shown without its delta.
- Never be imputed for a stale or missing domain.
- Never aggregate across incommensurable domains **beyond** the objective-weighted mean —
  and never at all for options or countries, where Principle 19 forbids a single figure.
- Never become the product. It is an index into the impacts, not a replacement for reading
  them.

## 7. Why this is safe when a "87/100 city score" is not

Principle 19 rejects aggregate scores across incommensurable dimensions. The Atlas Score
survives that rule for three reasons: it aggregates **one owner's exposure over time**
rather than options against each other; every point decomposes into stored rows; and it
never selects between alternatives — that stays with the counterfactual comparison, which
deliberately has no total.
