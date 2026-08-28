# UX Roadmap

The interface must never block engine development, and the engines must never arrive
without an interface ready to expose them. This is the schedule that satisfies both.

---

## 1. The one correction to the obvious sequence

The intuitive plan ships UI at Queue 16 (Dashboard). **That is too late.**

`PROGRAM.md` §12 identifies the owner's daily `useful / noise / wrong` marking as the
highest-leverage habit in the entire programme — it is the only feedback signal, and it
cannot be reconstructed retroactively. It requires a surface. Therefore:

> **V0 ships with Queue 14 (Daily Brief), not Queue 16.**

Queue 16 stops being "build the UI" and becomes "expand the UI into State, Outlook and the
time machine". The minimum viable interface is a rendered brief with a feedback control —
small enough to build in days, valuable enough to start the compounding loop months
earlier.

---

## 2. Phases

### Phase A — Now, during Queues 02–05 · *design only, no production code*

Engines are being built; the product is being defined. Nothing here touches the frontend
stack.

- These ten documents (done).
- Design system in Figma or code sandbox: type scale, colour tokens (validated), spacing,
  the fourteen components in all states.
- High-fidelity design of **three screens only**: Today (busy day), Today (quiet day),
  Impact detail.
- Prototype populated from `SYNTHETIC_DESIGN_DATA.md`.
- Feedback control designed and interaction-tested.

**Why only three screens.** The visual language is decided by these three. Designing thirty
screens against an unbuilt backend produces thirty screens that need redoing. Today and
Impact carry every component that matters — badges, confidence, evidence class, causal
chain, provenance, freshness, empty and degraded states. Get them right and the rest are
compositions.

**Exit:** a designer, a Figma agent or a frontend engineer could build Today without asking
what the product is.

### Phase B — Queues 06–09 · *validate against real shapes*

World State, Personal State, Portfolio and Impact become real. The design meets actual data
for the first time.

- Validate `StateDimensionRow` against a real dimension registry (ADR-0006 makes keys data,
  so the row must render an unknown key gracefully).
- Validate `ImpactCard` against real `typed_causal_chain` shapes and real priority
  components.
- Validate `DataFreshness` against real staleness.
- Confirm `personal_relevance` and `default_sort` are computable server-side.

**Rule:** discrepancies are fixed in the *specification*, never by changing the
architecture to make a component easier (masterplan §42).

### Phase C — Queues 10–12 · *scenario and decision components*

- `ScenarioCard` against real probability sets, including `DEGRADED` and `unknown_mass`
  (ADR-0009).
- `DecisionComposer` and the hindsight guard against real frozen context.
- `ForecastComparison` against the Queue 01 forecast ledger.

### Phase D — Queue 13 · *wire Today to the cycle*

`run_atlas_cycle` produces a `RunRecord`. Define and implement the `TodayView` read model
(`UX_DATA_CONTRACTS.md` §2.1). Today renders real cycle output, still without the brief's
prose.

**This is the first moment Atlas is looked at daily.**

### Phase E — Queue 14 · **ship V0**

Six routes: `/`, `/brief/:date`, `/impact/:id`, `/decisions`, `/decision/:id`,
`/settings/data`.

Acceptance for V0:
1. The owner reads a brief every morning and marks each item.
2. A quiet day renders correctly and reads as deliberate.
3. Every claim reaches its evidence in ≤3 interactions.
4. A stale or conflicting value is visible and correctable.
5. A decision can be recorded in under two minutes with its context frozen.

### Phase F — Queue 15 · *alerts*

Alerts reuse the attention model and introduce **no new vocabulary**. `ACTION` is the only
interrupting class. Delivery channels (Telegram, push) are replaceable adapters holding no
alert semantics of their own.

### Phase G — Queue 16 · *expand*

State (World and Me), Outlook, scenario detail, objectives, calibration, the as-of cursor.
This is expansion, not the first build — the visual language is already settled.

### Phase H — Queue 17 · *Ask*

`⌘K` over the read-only MCP surface. Answers as cards with citations. Includes the ADR-0012
removal test: with every external client disconnected, the cycle and a replay are unchanged.

### Phase I — later

Counterfactual comparison, opportunity scan surfacing, full time-machine diffing,
geography detail.

---

## 3. What to design immediately

In order:

1. **Today, quiet day.** Design this *first*, deliberately. It is the most common state and
   the one that decides whether the product survives. A system designed busy-first always
   produces a quiet day that looks broken.
2. **Today, busy day** with the `ACTION` from the synthetic dataset.
3. **Impact detail**, all three disclosure tiers.
4. The feedback control.
5. The six data-condition states as a component sheet.

## 4. What must wait

| Wait for | Because |
| --- | --- |
| State · World | Queue 06 defines whether dimensions are registry rows (ADR-0006 pending) |
| Scenario visuals | Queue 10 settles `unknown_mass` representation (ADR-0009 pending) |
| Calibration | Meaningless below ~50 resolved decisions |
| Counterfactuals | Requires engines from Queues 08–10 |
| Time machine | Requires several months of snapshots to be worth building |
| Any mobile-native work | Out of scope; responsive web only |

## 5. Dependencies on pending ADRs

| ADR | Status | Product surface waiting on it |
| --- | --- | --- |
| 0006 dimensions as data | Proposed | `StateDimensionRow`, World sorting |
| 0008 attention + priority | Proposed | `AttentionBadge`, all impact ranking |
| 0009 probability integrity | Proposed | `ScenarioCard`, the unassessed segment |
| 0012 external workspaces | Proposed | Ask, and any client integration |

These block *fidelity*, not *design*. The three Phase-A screens can be designed now because
they depend on the accepted ADRs (0003, 0010, 0011) and on shapes already in
`DATA_MODEL.md`.

## 6. How UX evolves

```
Queue 14        a brief you read every morning and mark
      ↓         the feedback loop starts compounding
Queue 16        a state you can interrogate and correct
      ↓         trust in the picture becomes durable
Queue 17        a system you can ask, from anywhere
      ↓         Atlas becomes reachable rather than visited
later           futures you can compare before choosing
```

Each step adds depth to the same four sections. The information architecture does not
change, because it is the domain model — and the domain model is not going to change.
