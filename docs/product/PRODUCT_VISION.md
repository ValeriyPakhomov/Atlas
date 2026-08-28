# Atlas Product Vision

## 1. What Atlas is

> A persistent personal strategic intelligence that continuously maintains a time-aware
> model of the external world and of the owner, detects changes that materially affect
> them, evaluates risks and opportunities, compares possible futures, helps make better
> decisions, and learns from outcomes over years.

The interface exists to make that intelligence usable **without exposing its machinery**.
The owner should never have to understand narratives, dedupe layers, dimension registries
or artefact versioning to get value. Those exist so the answers can be trusted; they are
not the product.

## 2. What Atlas is not

| Not this | Because |
| --- | --- |
| A dashboard | Dashboards show inventory. Atlas shows change. |
| A chatbot | Chat is a lens over state, never the state itself. |
| A news reader | News is input. The product is what the news means for one person. |
| A portfolio tracker | Capital is one domain of Personal State, not the product. |
| A Bloomberg for one | Density is not intelligence. Atlas removes information. |
| A trading system | Atlas produces no alpha and never executes (ADR-0003). |
| A task manager | Atlas decides what matters; commodity tools track the doing. |

## 3. The five questions

Every screen earns its place by answering at least one:

1. **What changed?**
2. **Why does it matter to me?**
3. **What should I consider doing?**
4. **How sure are we?**
5. **What would change this conclusion?**

Question 5 is the one most products omit and the one that makes the other four
trustworthy. A conclusion that cannot be falsified is an opinion.

## 4. The primary loop

```
Atlas runs continuously in the background
        ↓
owner opens Atlas  ──────────────────────────► sees only material changes   (30 seconds)
        ↓
understands personal impact
        ↓
reviews Atlas reasoning                                                     (5–20 minutes)
        ↓
takes / rejects / postpones a decision
        ↓
Atlas records what was known at that moment
        ↓
later evaluates the outcome and calibrates
```

Two properties matter more than any screen:

- **The 30-second exit is legitimate.** Most days the owner should be able to close Atlas
  after five lines and be correct in doing so.
- **The loop must close.** A system that recommends but never records what happened cannot
  calibrate, and an uncalibrated Atlas is a confident stranger.

## 5. Interface as a function of the architecture

The product structure is not a navigation aesthetic. It is the core equation made visible:

```
        STATE                    OUTLOOK                 DECISIONS
   World × Personal    →    Impacts + Scenarios    →   Choices + Outcomes
   "what Atlas believes"    "what it implies"          "what I did about it"

                    ┌──────────────── TODAY ────────────────┐
                    │  the delta across all three, today    │
                    └───────────────────────────────────────┘
```

`Today` is not a fifth thing. It is a **time-sliced lens** over the other three: only what
changed, only if it matters. This is why the IA survives Atlas growing from a daily brief
into a strategic decision system — the structure is the domain model, and the domain model
is not going to change.

## 6. The load-bearing product bet

Generic assistants will acquire memory, browsers, email, calendars, agents, MCP and local
models. None of that is Atlas's product. Atlas's product is:

- longitudinal **structured** state with validity intervals, so "what did I believe on
  3 March" is answerable;
- a **decision–outcome ledger** recorded before outcomes are known;
- **personal causal rules** learned from this owner's history;
- **deterministic, auditable arithmetic**;
- **replay**.

The interface must therefore optimise for *trust and continuity*, not for capability
breadth. Every screen either strengthens the owner's confidence that Atlas's picture is
accurate, current and explicable — or it is decoration.

## 7. Cognitive load is the primary constraint

Atlas fails in exactly one likely way: it works, and the owner stops reading it.

The interface is therefore designed around **subtraction**:

- a hard cap on what appears above the fold;
- a single interrupting attention class;
- omission of unchanged sections rather than rendering them as "no change";
- quiet days that look deliberate;
- one minute a day of feedback (`useful / noise / wrong`) as the only routine input asked
  of the owner — and the single highest-value element in the product, because it is the
  signal the whole system learns from.

## 8. Product boundaries

**In scope, now:** Today, Daily Brief, Impact, State (World and Me), Scenarios, Objectives,
Decisions, Outcomes, Forecast ledger, data-health and correction surfaces.

**In scope, later:** counterfactual option comparison, opportunity discovery, time
machine, Ask Atlas, calibration analytics.

**Never in scope:** trading terminal, execution UI, news feed, social features,
gamification, widget marketplace, avatars, generative decoration, a 40-KPI wall.

**Explicitly deferred, not rejected:** native mobile. Atlas begins as a private responsive
web product (`docs/PROGRAM.md` phases).

## 9. Definition of a good Atlas day

- The owner opens Atlas, reads five lines, and closes it — correctly.
- Or: the owner reads one impact, opens its causal chain, disagrees with one link,
  corrects a stale value, and records a `WAIT` decision with a review date.
- In neither case did the owner scroll a feed, dismiss a notification, or wonder what a
  number meant.

---

## 10. The product blueprint

| Document | Answers |
| --- | --- |
| [PRODUCT_PRINCIPLES.md](PRODUCT_PRINCIPLES.md) | The twenty rules that prevent drift |
| [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) | Four sections, two global affordances, and why |
| [TODAY_AND_DAILY_BRIEF.md](TODAY_AND_DAILY_BRIEF.md) | The canonical home surface and brief |
| [SCREEN_SYSTEM.md](SCREEN_SYSTEM.md) | Routes, states, responsive split |
| [COMPONENT_SYSTEM.md](COMPONENT_SYSTEM.md) | Fourteen components and their contracts |
| [DESIGN_DIRECTION.md](DESIGN_DIRECTION.md) | Typography, validated colour, motion |
| [DOMAIN_SURFACES.md](DOMAIN_SURFACES.md) | Sources, geopolitics, portfolio, mobility, work, telltrack |
| [UX_DATA_CONTRACTS.md](UX_DATA_CONTRACTS.md) | What the frontend needs from the API |
| [SYNTHETIC_DESIGN_DATA.md](SYNTHETIC_DESIGN_DATA.md) | One coherent day to design against |
| [UX_ROADMAP.md](UX_ROADMAP.md) | What to design now, and what must wait |
| [VISUAL_REFERENCE_PROTOCOL.md](VISUAL_REFERENCE_PROTOCOL.md) | How references are used without diluting the direction |
