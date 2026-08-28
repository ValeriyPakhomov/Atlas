# Atlas Component System

Fourteen components. Each entry gives required data, interaction states and the rules that
make it correct. Consolidated deliberately: several proposed components were folded in
because near-duplicate components are how design systems rot.

**Consolidations.** `RecommendationBlock` → `DecisionCandidate`. `EvidenceList` +
`ProvenanceDrawer` → one `ProvenanceDrawer`. `AtlasView` is a typographic treatment, not a
component. `StateDimensionRow` and `ChangeCard` stay separate — one is standing state, the
other is a delta, and merging them is exactly how "what changed" becomes "what exists".

---

## 1. AttentionBadge

The vocabulary the entire product shares. `ACTION | VERIFY | REVIEW | BACKGROUND | SUPPRESS`
(ADR-0008).

| Class | Meaning | Where it appears | Interrupts? |
| --- | --- | --- | --- |
| `ACTION` | Material and sufficiently confident | Today lead, alert, Outlook | **Yes** — the only interrupting class |
| `VERIFY` | Potentially material, insufficient confidence | Today, Outlook | No |
| `REVIEW` | Material, not urgent | Today, Outlook | No |
| `BACKGROUND` | Context and learning | Outlook only | No |
| `SUPPRESS` | Duplicate, stale, invalid, below floor | Outlook behind a filter, with reason | No |

Rules: the badge is a **word**, never a bare dot or colour chip. Only `ACTION` carries the
accent hue; the rest are typographic weight. `ACTION` requires acknowledgement, which
records who saw it and when; the other classes require nothing.

**Data:** `attention_class`, `qualifying_rule?`, `acknowledged_at?`.
**States:** default · acknowledged · suppressed (with reason) · degraded (class computed
from incomplete data — shown with a dotted underline).

## 2. ConfidenceIndicator

Bands, never decimals in the primary reading (ADR-0009, A12).

`low` · `moderate` · `high`. Rendered as a word plus a three-segment ordinal mark. Numeric
value on hover/tap only. **Never coloured** — uncertainty is weight and opacity, because
colouring uncertainty makes low confidence read as danger.

**Data:** `confidence_band`, `confidence_value`, `basis` (evidence count, source
diversity, freshness, model disagreement).
**States:** default · degraded (basis incomplete) · unavailable (`—`, never 0).

## 3. EvidenceClassTag

`DIRECT_CALCULATED` · `DIRECT_RULE` · `INFERRED_CAUSAL` · `SPECULATIVE`.

Present on **every** claim Atlas makes. This is Principle 6 made mechanical: a
mark-to-market and a geopolitical hunch must be impossible to confuse at a glance.
Rendered as a small caps label: `calculated` · `rule` · `inferred` · `speculative`.

## 4. ChangeCard

One row in "What changed". Fixed left gutter carrying the kind — `WORLD` `YOU` `IMPACT`
`SCENARIO` `DECISION` — so kinds are separated by **position and label before colour**.

**Data:** `kind`, `headline`, `from`/`to` where ordinal, `materiality`, `link_target`,
`freshness?`.
**States:** default · first-seen · escalated (attention increased since last brief) ·
stale-input (derived from data past its SLA).

## 5. ImpactCard

Three disclosure tiers. The central component of the product.

**Collapsed** — one line plus one sentence:
`AttentionBadge` · domain · direction · claim · `ConfidenceIndicator` ·
`EvidenceClassTag` · `ObjectiveTag`s.

**Expanded** — adds: severity, exposure, urgency, irreversibility as labelled ordinal
terms (**not** percentage bars — the underlying values are bounded scores, and a bar
implies a precision the model does not have); `CausalChain`; invalidators; related
scenarios; `DecisionCandidate`.

**Forensic** — adds: full provenance to raw items, evidence class per link, the priority
computation with each component shown separately, `artifact_version_refs`, the sensitivity
tier of each input, and the model plus prompt version that produced any inferred link.

**Data:** the `Impact` entity in full, plus resolved objective titles and a computed
priority with components.
**States:** default · acknowledged · superseded (a newer impact replaces it; both remain
reachable) · degraded · suppressed.

Rule: the collapsed tier must be readable without the expanded tier. If a claim only makes
sense expanded, the claim is written wrong.

## 6. CausalChain

Three to six steps, horizontal on desktop, vertical on mobile. Each step carries its own
`EvidenceClassTag` — the chain typically degrades from calculated to inferred along its
length, and showing that is the point.

```
TR FX −1 → −2        local costs rise        income is TRY-linked      runway compresses
[rule]               [calculated]            [rule]                    [calculated]
```

**Explicitly not a node graph.** Force-directed graphs are unreadable at card size and
imply more rigour than a `typed_causal_chain` contains.

**Data:** ordered steps with `label`, `evidence_class`, `evidence_refs`, `confidence?`.
**States:** default · truncated (>6 steps, middle collapsed) · broken (a link lost its
evidence — shown as a gap, never silently bridged).

## 7. ProvenanceDrawer

Slide-over from any claim. Layers: claim → causal chain → evidence propositions → raw
items → sources with reliability class → the run that produced it.

Also shows the sensitivity tier of each input and, for inferred links, which model and
prompt version produced them (ADR-0010, ADR-0014).

**Rule:** always reachable in ≤3 interactions from any claim; never required to understand
the claim.

## 8. ScenarioCard

```
BASE CASE                                              45%   ▲ from 40%
Liquidity improves gradually without a growth shock

████████████░░░░░░░░░░░░░▒▒▒▒▒
base 45 · reflation 20 · recession 20 · not assessed 15

DRIVERS      + easing financial conditions      strengthening
             + improving risk appetite          stable
             − geopolitical uncertainty         strengthening

INVALIDATED BY   a funding-stress print, or CPI above 4%

FOR YOU      moderately favourable for crypto exposure   →2 impacts
```

Rules: probabilities in 5-point steps; movement shown **only** when a step is crossed;
**unassessed mass is its own hatched segment**, never redistributed (ADR-0009); no time
series of probability on the card — that belongs in scenario detail.

**Data:** `Scenario`, `ScenarioDriver[]`, `unknown_mass`, `integrity_status`,
`previous_probability`, invalidators, linked impacts.
**States:** default · moved · new · resolved · `DEGRADED` (banner naming the unevaluable
driver) · `UNRELIABLE` (probabilities suppressed entirely; the card states why).

## 9. ObjectiveTag & ObjectiveProposal

`ObjectiveTag` — a compact chip: direction glyph (`attain` `avoid` `maintain`) plus short
title. Appears on impacts, decisions and scenarios to show what is at stake.

`ObjectiveProposal` — the **Atlas noticed** treatment. Visually distinct from accepted
objectives (dashed border, `proposed` label) and functionally inert until accepted
(ADR-0011).

```
Atlas noticed
You appear to be optimising for geographic optionality.
Three decisions since June preserved mobility at a cost.
                          [Accept]  [Edit & accept]  [Not a goal]  [Not now]
```

`Not a goal` is recorded so it is not re-proposed. Nothing in Atlas reads a proposed
objective until `accepted_at` is set.

## 10. StateDimensionRow

One world dimension in a scannable row.

```
macro.liquidity     +1  ▁▂▄▄▅  rising    moderate   4h   ▲ from 0     you: exposed
```

Fields: key, ordinal score on a discrete −3…+3 scale (**seven positions, never a
continuous gauge**), sparkline of that score's own history, direction, confidence band,
freshness, delta since last snapshot, personal relevance.

Default sort: **personal relevance × recent delta**. Alphabetical is available and is not
the default — the world view is not a glossary.

## 11. DataFreshness

One primitive used everywhere a value appears: `current` · `{n}d stale` · `unverified` ·
`conflicting` · `unknown`. Carries source and `observed_at` on interaction, and a
`Correct` affordance where the value is owner-correctable.

Rule: any conclusion derived from a stale or conflicting input inherits a marker. Freshness
propagates downstream; it is not a property of leaf values alone.

## 12. DecisionCard & DecisionComposer

`DecisionCard` — question, type, date, status, review date, linked impacts and objectives,
and outcome when resolved.

`DecisionComposer` — captures, with most fields pre-filled from context: question, the
state snapshot reference, related impacts, scenarios at the time, **considered options**,
objectives active, policy results, Atlas recommendation, owner choice, rationale,
confidence, review date.

`considered_options` is a required field with at least two entries, one of which may be
"do nothing". Alternatives that are not recorded cannot be reconstructed, and without them
no regret or opportunity-cost analysis is possible later.

**The hindsight guard.** Viewing a past decision renders the frozen context. Current
values are hidden behind an explicit `show what we know now` toggle, and when enabled the
panel is visually marked as present-day. Default off, every time — this is not a
preference that persists.

## 13. OutcomeRetrospective

Two independent axes, never collapsed:

```
                    outcome good        outcome bad
decision good       worked              right call, bad luck
decision bad        lucky               mistake
```

Plus `unresolved` and `unresolvable`. The retrospective form asks the five questions from
`DECISION_JOURNAL.md`: was the premise correct; did the scenario move as expected; was the
impact over- or under-estimated; was the preparation useful; was confidence calibrated.

Where a forecast existed, `ForecastComparison` shows owner versus Atlas versus outcome.

## 14. ForecastComparison

Restrained by design. Question, resolution criteria, owner prediction, Atlas prediction,
resolution, and who was closer — attached to the decision or scenario it informs, never as
a standalone prediction market. Prediction history renders as an append-only list, since
`ForecastPrediction` supersedes rather than overwrites.

---

## Component acceptance criteria

| # | Criterion |
| --- | --- |
| C1 | Every component renders correctly in all six cross-cutting states (`SCREEN_SYSTEM.md` §3) |
| C2 | No component conveys meaning by colour alone; all pass greyscale review |
| C3 | Every claim-bearing component exposes `EvidenceClassTag` and `ConfidenceIndicator` |
| C4 | No probability or confidence renders at finer resolution than its method supports |
| C5 | Provenance is reachable from any claim in ≤3 interactions |
| C6 | No component derives ranking, thresholds, rounding or attention class client-side |
| C7 | Collapsed tiers are independently comprehensible |
| C8 | Atlas-proposed content is visually and functionally distinct from owner-authored content |
