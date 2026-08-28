# Domain Surfaces

Answers to a specific set of product questions: what daily management surfaces should
exist for news and sources, geopolitics and economics, portfolio, documents and mobility,
and work — and whether Atlas should integrate with telltrack.

Two of these requests, taken literally, would damage the product. Both have a real need
underneath, and both are answered here with a surface that serves the need without the
damage.

---

## 1. Politics, geopolitics, economics — **filters, not screens**

**Request:** dedicated areas for politics/geopolitics and for economics.

**Answer:** these are `category` values on world dimensions, and they become **filters on
State · World**, not top-level destinations.

| If they were screens | Consequence |
| --- | --- |
| Navigation grows by topic | Every new domain adds an item; the IA never stabilises |
| Each becomes a topic feed | A screen with a subject and no owner question drifts into a news reader |
| Personal relevance ordering breaks | World's default sort is *personal relevance × recent delta*. Grouping by topic replaces "what matters to you" with "what category this belongs to" |

The categories already exist in the model: `macro`, `markets`, `crypto`, `energy`,
`commodities`, `geopolitics`, `technology`, `regulation`, `geography`, `migration`,
`climate`. State · World gets a filter row over them.

```
State · World          [all] macro  markets  crypto  geopolitics  technology  geography
macro.liquidity        +1  ▁▂▄▄▅  rising    moderate   4h   ▲ from 0     you: exposed
geopolitics.global     −1  ▄▄▃▃▃  stable    low        1d   —            indirect
```

Same content, same depth, zero navigation cost. A category with no owner exposure sorts to
the bottom rather than occupying a tab.

---

## 2. News and sources — **a reading room, not a feed**

**Request:** a news feed with links to sources.

**The need is legitimate.** "Show me what Atlas actually read, let me click through, let me
judge the sources myself" is a trust requirement, and trust is the product. Atlas asks the
owner to act on conclusions; it owes them the raw material.

**The literal implementation is not.** A recency-ordered feed is the single most reliable
way to destroy this product:

- it trains browsing instead of deciding — the opposite of the primary loop;
- it makes the owner feel informed while the signal degrades, because volume reads as value;
- it re-introduces exactly what dedupe, materiality thresholds and the brief exist to remove;
- once it exists, it becomes the home screen by habit, and Atlas becomes a news reader with
  a state engine attached.

### The surface that serves the need

**Reading Room** — `/state/sources` · **V1** · reached from the brief's `Coverage` line,
never from the navigation bar.

```
Coverage · 28 Aug          7 sources · 6 current, 1 stale · 63 items · 5 material

MATERIAL (5)
  TR inflation print, August            Reuters · A · 06:12    → 2 evidence → D1
  BIS quarterly liquidity note          BIS · A · 04:30        → 1 evidence → D3
  Perp funding rates hit 3-month high   Coinglass · C · 05:55  → 1 evidence → D2
  …
REVIEWED, NOT MATERIAL (58)                                              show ▾
  Fed official comments on inflation    Bloomberg · B          duplicate of Event #4412
  BTC daily move +4.1%                  exchange · C           no impact ≥ REVIEW
  …
CONFLICTING (1)
  TR inflation, August    Source A 61.8%  ·  Source B 58.4%    unresolved → blocks I2
```

Four properties make this a ledger and not a feed:

1. **Ordered by consequence, not recency.** Material first, with what each item produced.
2. **Discards are shown with the reason.** Seeing *why* 58 items were dropped builds far
   more trust than reading them would. It is also the surface where the owner can tell
   Atlas it was wrong to drop something.
3. **Every row terminates in the model** — evidence, event, delta — not in a headline.
4. **It is reached from a claim or from Coverage.** There is no browsing entry point.

Same links, same sources, opposite behaviour: it answers *"what did Atlas base this on"*,
not *"what happened today"*.

---

## 3. Portfolio — **specified, and deliberately restrained**

Already covered: Personal State domain on `/state`, standing exposure on `/outlook`.

The discipline that matters: Atlas says **"this portfolio is vulnerable to X"**, never
"BTC is +3.1% today". Price movement enters the product only when it produces an impact of
class `REVIEW` or above.

Views: liquid structure, allocation, currency exposure, concentration, runway, scenario
exposure. **Not** built: candlesticks, order tickets, watchlists, P&L streaks, a ticker.

---

## 4. Documents, citizenship, mobility — **a real gap, now specified**

**Request:** information about documents, citizenship and movements.

This is the least-specified domain in Atlas relative to its importance, and it deserves a
first-class surface. For someone with a permit clock running, this is as consequential as
the portfolio — arguably more, because the failure is discrete and irreversible.

**Mobility & Documents** — `/state/mobility` · **V1**

```
DOCUMENTS
  Turkish residence permit    valid to 12 Nov 2026    76 days    BREACH ≥90d policy
                              renewal lead 30–45d · unverified
  Passport                    valid to 03 Mar 2031    expires in 4y 6m
                              < 6 months blocks most visa applications

ALLOWANCES
  Schengen 90/180             used 31 of 90          resets 14 Oct
  Turkey tax residence        184 of 183 days        threshold crossed 12 Aug

BASES
  Istanbul   current_base     permit-dependent · TRY exposure 21% · career fit moderate
  Milan      candidate        no status yet · EU objective O2 · friction high
  Tbilisi    fallback         visa-free 365d · friction low · career fit low

WHAT EACH DOCUMENT GATES
  Turkish permit  →  current base, local banking, local income continuity
  Passport ≥6mo   →  every visa application including the EU track (O2)
```

Design rules:

- **Deadlines are countdowns in days**, never progress rings. A ring implies a proportion
  of something; a permit is not 62% used.
- **Every document states what it gates.** A date alone is not decision-relevant; "this
  blocks the EU track" is.
- **Day-counters are first-class.** Schengen 90/180 and tax-residence thresholds are
  deterministic arithmetic over travel records — exactly the kind of thing a person tracks
  badly in their head and Atlas computes perfectly.
- **Unverified assertions are marked.** "Renewal lead time 30–45 days" is `UNVERIFIED`
  until confirmed, and any conclusion built on it inherits that.
- **This is L3 data** (ADR-0010): identity-linked documents and precise location never
  leave the perimeter. The surface carries the local-only indicator.

**One open question for Queue 07, not an ADR.** `GeographyState` carries
`residence_status`, `valid_until` and `next_deadline`, which covers country-scoped status.
A passport is not country-scoped in the same way, and travel-day counters need a movement
record. Whether that is two more fields or one small entity is a Queue 07 scoping decision —
it is a modelling detail, not an architectural one, and it does not warrant an ADR.

---

## 5. Work and career — **exposure, not coaching**

**Request:** information about work, and advice on how to move.

The honest boundary matters here.

**What Atlas can genuinely do**, because it holds the state:

- income streams with currency, geography, **mobility dependency** and **AI-disruption
  exposure** — all already fields on `IncomeStream`;
- the interaction: "this contract is TRY-denominated while your costs are TRY and your
  permit expires in 76 days" — that is a cross-domain impact no career tool can produce;
- how a work decision moves an objective: accepting a six-week Istanbul contract extends
  permit exposure and delays O2;
- concentration: one client at 60% of income is a risk with the same shape as one asset at
  60% of a portfolio, and Atlas already has the operator for it.

**What Atlas should not do**: generic career advice. "Build your network, learn AI skills"
is what any model says to anyone. It has no provenance, no personal exposure behind it, and
it is precisely the commodity output that would dilute the product.

The test: *could a general assistant say this without knowing my state?* If yes, Atlas
should not say it.

Surface: work lives inside `/state` (income and objectives) and appears on Today only as
`career`, `income` or `startup` impacts. It is not a separate section.

---

## 6. Telltrack integration — **not now; later as a one-way source, never as shared state**

### The architectural answer

ADR-0012 already decides the shape: telltrack is an **external system**, so the only legal
path for its content is the same as any other source —

```
telltrack  →  TelltrackAdapter (SourceAdapter contract)  →  RawItem
           →  extraction  →  Evidence  →  proposed personal-state update
           →  owner confirms  →  canonical state
```

Never: shared database, shared entities, telltrack writing Atlas state, or Atlas reading
telltrack as truth. Telltrack's memory is its own; Atlas's canonical state is Postgres
(ADR-0002).

### The timing answer: not now

| Reason | |
| --- | --- |
| Anti-metric | `PROGRAM.md` §16 — source count growing before usefulness is the named failure mode. Atlas has not yet produced a single brief |
| Two moving targets | Both products are unfinished. Coupling them multiplies the failure surface and neither team learns anything clean |
| Tier machinery | Telltrack content is work, clients and money — L2/L3. Routing it safely needs ADR-0010 enforcement, which is Queue 04+ |
| It is a Queue-02-class adapter | Which means it belongs after the vertical slice proves daily value, not before |

**Earliest sensible point:** after Queue 14, once Atlas has produced briefs the owner
actually reads. Then it is a small, well-understood adapter rather than an integration
project.

### The insight that matters more than the data flow

Both products have a **Watch** concept, and both intend to notify.

If both notify independently, the owner acquires two competing attention systems — and
each one's Attention Covenant is enforced only within itself. The combined interruption
load is governed by nobody. That is a worse outcome than either product alone, and no
amount of data integration fixes it.

So the integration question is really an **attention** question, and it should be settled
before any adapter is written:

> **One system owns interruption per domain.** Atlas owns strategic and world-driven
> attention (capital, geography, residency, scenarios). Telltrack owns work-context
> attention (commitments, situations, follow-ups). Neither escalates into the other's
> domain, and neither notifies about something the other has already raised.

Settling that costs nothing today and prevents the failure that would otherwise only show
up after both products ship.

### If integration does happen, the acceptance test

Per ADR-0012's removal test: **disconnect telltrack entirely, and Atlas's canonical state,
daily cycle, replay and decisions must be byte-identical.** If removing telltrack changes
anything Atlas concluded, the boundary has been violated and the integration is wrong.

---

## 7. Summary of decisions

| Request | Decision | Where it lives |
| --- | --- | --- |
| Today with Atlas commentary | Already specified | `TODAY_AND_DAILY_BRIEF.md` §3 §4 |
| News feed with source links | **Reframed** as the Reading Room — consequence-ordered, discards shown, reached from Coverage | `/state/sources` · V1 |
| Politics / geopolitics screen | **Filter**, not a screen | State · World |
| Economy screen | **Filter**, not a screen | State · World |
| Portfolio | Specified, restrained | `/state`, `/outlook` |
| Documents, citizenship, movements | **New surface** — genuine gap | `/state/mobility` · V1 |
| Work and career advice | Exposure and interaction, not coaching | `/state`, impacts on Today |
| Telltrack integration | **Not now.** Later as a one-way source adapter; settle the attention boundary first | Post-Queue 14 |
