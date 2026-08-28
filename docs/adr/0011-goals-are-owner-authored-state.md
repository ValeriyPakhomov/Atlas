# ADR-0011 — Goals, preferences and constraints are owner-authored canonical state

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

`Goal` today is `id, owner_id, title, category, horizon, target_date?, target_value?,
priority, status`. That is a to-do item with a deadline. It cannot express what Atlas
actually needs to reason with.

The gap is load-bearing rather than cosmetic, because two capabilities are **undefinable**
without it:

- An **opportunity** is not "something good happened". It is a favourable change that is
  favourable *relative to something the owner wants*. Without goals in canonical state,
  Atlas can rank impacts by magnitude but cannot say whether they help.
- A **counterfactual** compares trajectories. Comparison requires a criterion. Without
  goals, "option A is better than option B" has no referent.

There is also a governance problem. Values are the one thing in Atlas that the model must
never author. A system that infers "you seem to value optionality" from conversation and
then optimises against that inference is not a decision-support system; it is a system
that decided what you want.

Finally, goals change, and a decision must be judged against what the owner wanted **at
decision time**, not what they want now. That makes goals temporal state (A02), not
configuration.

## Decision

### Objective — canonical, owner-authored, temporally versioned

```
Objective
- id, owner_id
- title, description
- category            # financial | geographic | career | startup | health | relational | resilience
- direction           # attain | avoid | maintain
- horizon             # short | medium | long
- target_date?, target_value?, target_currency?
- priority            # ordinal within owner, not a score
- status              # draft | active | achieved | abandoned | superseded
- authored_by         # owner | atlas_proposed
- accepted_at?        # null while atlas_proposed; set when the owner accepts
- valid_from, valid_to
```

`direction = avoid` covers what §5.1 called an **AntiGoal**. A separate entity would
duplicate every field to express a sign.

### Preference — ordinal only

```
Preference
- id, owner_id
- higher_objective_id, lower_objective_id
- strength           # weak | strong
- rationale
- valid_from, valid_to
```

Pairwise ordinal comparisons only. **No utility functions, no trade-off rates, no
exchange coefficients.** People cannot state "I would give up 3 months of runway for 10%
more optionality" reliably, and a badly elicited number is worse than an honest ordering
because it propagates false precision into every downstream ranking (A12).

### Constraints are Policies, not a new entity

`Policy` already exists, is deterministic, and already returns
`PASS | WARN | BREACH | UNKNOWN_DATA`. A constraint is a policy that exists because of an
objective. Therefore:

```
Policy gains:  objective_id?   # the objective this constraint serves, when it serves one
```

That is the whole change. Introducing a separate `Constraint` entity alongside `Policy`
would create two overlapping concepts with one evaluator, and every future queue item
would have to decide which to use.

### The authority rule

An LLM may create an `Objective` or `Preference` only with `authored_by = atlas_proposed`
and `status = draft`. Such a record is **inert**: no engine may read a draft or unaccepted
objective when ranking, scoring, or generating impacts, opportunities or decisions. It
becomes authoritative only when the owner sets `accepted_at`.

This is A04 applied to the one domain where the stakes are highest.

## Consequences

- `Impact` gains `objective_refs[]`, so goal relevance is stored rather than recomputed —
  which is what makes an "opportunity" view over impacts possible without a new engine.
- Decisions become judgeable against the objectives that were `active` at their
  `decision_time`, because objectives are temporally versioned. Without this, every
  retrospective is contaminated by hindsight about what the owner wanted.
- Cost: two small tables and one nullable column, added in Queue 01. Cheap now, and
  effectively unreconstructable later — you cannot recover what you wanted last March.
- Atlas can propose objectives (e.g. "you appear to be managing toward a 12-month runway;
  make it explicit?") without ever acting on its own proposal.

## Enforcement

- A test asserts that no engine query returns objectives with `accepted_at IS NULL`.
- A test asserts an LLM-originated write with `authored_by = owner` is rejected.
- Queue 09 acceptance gains: an impact touching no active objective is classified, ranked
  and stored, but is not presented as an opportunity.

## Alternatives considered

- **Full value model with utility and trade-off rates.** Rejected: elicitation is
  unreliable, and the resulting precision is fake (A12). Ordinal preferences carry the
  decision-relevant information.
- **Separate `Constraint` and `AntiGoal` entities.** Rejected as ontology for its own
  sake: both are expressible with one field on an entity that already exists.
- **Keep goals as configuration, not temporal state.** Rejected: makes honest
  retrospectives impossible.
