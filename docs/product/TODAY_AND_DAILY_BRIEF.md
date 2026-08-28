# Today and the Daily Brief

The canonical specification for the most important surface in Atlas. `Today` and the
Daily Brief are the **same artefact** viewed at two moments: Today is the brief for the
current cycle; `/brief/:date` is that brief preserved. There is no second content model.

---

## 1. Design target

| Read depth | Time | The owner must come away knowing |
| --- | --- | --- |
| Glance | 5 s | Whether anything needs them |
| Scan | 30 s | What changed and roughly why it matters |
| Read | 2–5 min | The reasoning, the exposure, what to consider |
| Investigate | 5–20 min | Provenance, causal chain, scenario movement, and enough to decide |

**The 30-second exit is a success state, not a failure to engage.** On a typical day the
owner should be able to stop after the Signal and be correct.

---

## 2. Canonical brief structure

Nine sections, in this fixed order. **Sections 5–9 are omitted entirely when empty** — a
section rendered as "no change" is noise wearing a label.

```
1  SIGNAL              always present, one sentence
2  WHAT CHANGED        material deltas only, max 3 above the fold
3  WHAT IT MEANS       ranked impacts, collapsed
4  ATLAS VIEW          causal synthesis, ≤150 words, marked as interpretation
5  WHAT I WOULD CONSIDER   decision candidates (NO_ACTION is a valid entry)
6  SCENARIOS           only if a probability crossed a step or a driver changed
7  WHAT WOULD CHANGE THIS  invalidators
8  WHAT ATLAS DOESN'T KNOW unknown mass, stale, conflicting, unverified
9  WATCHING            named triggers with thresholds
```

### Improvements over the initial proposal

- **`Risks` and `Opportunities` are merged into §3.** Separating them forces every impact
  into a binary that many do not fit — TRY weakness simultaneously cuts local costs and
  local income. One ranked list carries `direction` per impact and groups by direction
  only when both are present. This also matches the architecture: an opportunity is an
  `Impact`, not a separate entity.
- **`What would change this` (§7) is new** and is the section that converts a conclusion
  into a falsifiable claim. Without it, Atlas produces opinions.
- **`Scenarios` becomes conditional.** Reporting stable probabilities daily trains the
  owner to skip the section, which is exactly where a real move would then be missed.
- **`Executive signal` becomes a deterministic claim** with model-written phrasing, not a
  model-written judgement (see §3).

---

## 3. Section specifications

### §1 Signal — always present

One sentence, plus a count line. The *claim* is deterministic; only the phrasing is
generated.

| Condition (deterministic) | Claim |
| --- | --- |
| Any impact with `attention_class = ACTION` | "One change materially affects *{domain}*." |
| No `ACTION`, ≥1 `VERIFY` | "Nothing requires action; one conclusion needs verification." |
| No `ACTION`/`VERIFY`, ≥1 `REVIEW` | "Nothing urgent; *{n}* items worth review." |
| None of the above | "Nothing materially changed. No action required." |
| Integrity `DEGRADED`/`UNRELIABLE` dominates | "Atlas's picture is incomplete today — *{reason}*." |

Count line: `{n} things matter · {m} need attention`, where *matter* = `REVIEW` and above,
*attention* = `ACTION`. Both counts come from the backend; the frontend never derives them.

> The last row matters more than it looks: when data health is bad, the brief leads with
> that rather than with conclusions built on it (A06).

### §2 What changed

Material deltas, grouped by the five change kinds and rendered in a **fixed left gutter**
so kinds can never blend (see §5). **Hard cap: 3 above the fold**; the remainder collapse
behind `{n} more`. The cap is a forcing function — without it the section grows until it
is skipped.

### §3 What it means for you

Ranked `Impact` cards in collapsed form, ordered by backend-computed priority. Direction
is shown per impact; when both favourable and adverse impacts are present they are grouped
under quiet subheads, not split into separate sections.

Each collapsed impact shows: attention badge, domain, direction, one-sentence claim,
confidence band, evidence class, affected objectives.

### §4 Atlas view

The one place Atlas writes prose. Set in serif to mark it as interpretation (see
`DESIGN_DIRECTION.md` §3). Hard limits: **150 words**, and every causal claim links to the
impact or narrative it came from. If there is nothing to synthesise, the section is
omitted rather than padded.

### §5 What I would consider

Zero or more decision candidates, each with a V1 decision type (`OBSERVE`, `VERIFY`,
`WAIT`, `PREPARE`, `REVIEW_ALLOCATION`, `REVIEW_LOCATION`, `REVIEW_POLICY`, `NO_ACTION`),
the mechanism, the impacts it responds to, and a proposed review date.

`NO_ACTION` appears as an explicit entry when Atlas actively considered acting and decided
against it — that is different from the section being empty, and the difference is worth
showing.

### §6 Scenarios — conditional

Included only when, since the previous brief: a probability crossed a 5-point display
step, a driver entered or left a set, or integrity status changed. Otherwise omitted.

### §7 What would change this

For the top one or two conclusions: the observation that would most change Atlas's mind,
and its current status. This is the section that makes the brief auditable a week later.

### §8 What Atlas doesn't know

Present whenever any of these hold: `unknown_mass` above the floor, a source stale beyond
its SLA, conflicting sources on a live claim, an unverified critical fact, or a policy
returning `UNKNOWN_DATA`. Each entry names the missing thing and what it blocks.

### §9 Watching

Named triggers with thresholds and current distance to trigger — "BTC leverage: watching
for funding above *x* (now *y*)". This is what makes a quiet day feel like coverage rather
than absence.

---

## 4. Inclusion and exclusion logic

The brief is assembled deterministically. The model writes phrasing; it does not choose
membership.

### Include an item if and only if

1. it is a `WorldStateDelta` whose materiality ≥ threshold **and** which resolves to at
   least one `Impact` of class `ACTION`, `VERIFY` or `REVIEW`; **or**
2. it is an `Impact` whose `attention_class` ∈ {`ACTION`, `VERIFY`, `REVIEW`}; **or**
3. it is a scenario change meeting §3 §6 conditions; **or**
4. it is a personal-state change the **owner did not make themselves** — an adapter sync,
   a deadline entering a policy window, a policy transitioning to `WARN`/`BREACH`; **or**
5. it is a decision reaching its review date; **or**
6. it is a data-integrity condition per §3 §8.

### Exclude unconditionally

| Excluded | Rule |
| --- | --- |
| A story already reported | Unless a **new** delta on the same narrative, or the attention class increased |
| Price movement | Unless it produces an impact ≥ `REVIEW`. "BTC rose 4%" is not a brief item |
| Multiple reports of one event | Dedupe resolves to one `Event`; the brief shows one item with a source count |
| Stable personal facts | Restating "runway is 14 months" when it was 14 months yesterday |
| Any recommendation without a `typed_causal_chain` | Structurally rejected before rendering |
| Confidence language unsupported by evidence | Band must derive from evidence count, source diversity, freshness and disagreement |
| `SUPPRESS`-class impacts | Retained with reason; reachable only from Outlook with a filter |
| Sections with no content | Omitted, never rendered as "no change" |

### Repetition rule

An item may reappear on a later day **only** if its attention class increased or its
evidence materially changed. Otherwise it lives in Outlook as standing exposure. Without
this rule every brief eventually contains every open item.

### Volume ceiling

Above the fold: **1 signal + 3 changes + 3 impacts**. Everything else is one interaction
away. If Atlas has more than three things that matter on an ordinary day, that is itself
the finding, and §1 says so.

---

## 5. The five kinds of change

Never blended. Fixed order, fixed gutter label, distinguished by **position and label**
before colour — so the distinction survives greyscale, colour-blindness and dark mode.

```
WORLD      US liquidity conditions improved            +1 → 0 was 0    moderate
YOU        crypto exposure unchanged                   55% of liquid   9d stale
IMPACT     risk/reward improved moderately             REVIEW          inferred
SCENARIO   soft landing 45% → 50%                      +1 driver
DECISION   "hold allocation" reaches review in 3 days  WAIT
```

Reading order is causal: the world moved, here is your position, here is the interaction,
here is what it does to the futures, here is what it means for a choice you already made.
That ordering is the product's argument, made structural.

---

## 6. Today layout

```
┌────────────────────────────────────────────────────────────────┐
│ Atlas · Friday 28 August                            As of ▾  ⌘K│
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  One change materially affects your residency timeline.        │  §1 signal
│  3 things matter · 1 needs attention                           │
│                                                                │
│  ─── WHAT CHANGED ─────────────────────────────────────────    │  §2
│  WORLD     Turkey FX pressure intensified      −1 → −2         │
│  YOU       Residence permit: 76 days remain    entered window  │
│  IMPACT    Local purchasing power deteriorating  REVIEW        │
│                                          2 more ▾              │
│                                                                │
│  ─── WHAT IT MEANS FOR YOU ────────────────────────────────    │  §3
│  [ACTION]  Residency · adverse · high confidence · rule        │
│            Permit expires inside your 90-day policy window     │
│            affects: EU base by 2028 · avoid single-country     │
│                                                        open ▾  │
│  [REVIEW]  Currency · adverse · moderate · rule + measured     │
│  [VERIFY]  Startup · adverse · low · inferred                  │
│                                                                │
│  ─── ATLAS VIEW ───────────────────────────────────────────    │  §4  (serif)
│  Turkish FX weakness is now compounding with a permit          │
│  deadline you had planned to handle later …                    │
│                                                                │
│  ─── WHAT I WOULD CONSIDER ────────────────────────────────    │  §5
│  PREPARE   Begin permit renewal documentation   review in 7d   │
│  NO_ACTION Crypto allocation — leverage elevated but exposure  │
│            is within policy                                    │
│                                                                │
│  ─── WHAT WOULD CHANGE THIS ───────────────────────────────    │  §7
│  A confirmed renewal appointment would remove the ACTION.      │
│                                                                │
│  ─── WHAT ATLAS DOESN'T KNOW ──────────────────────────────    │  §8
│  Portfolio feed 9 days stale · scenario set DEGRADED (15%      │
│  unassessed) · two sources disagree on TR inflation            │
│                                                                │
│  ─── WATCHING ─────────────────────────────────────────────    │  §9
│  US liquidity · BTC funding above 0.05% · permit appointment   │
│                                                                │
│  Was this useful?   [useful] [noise] [wrong]      per item      │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. The quiet day

The most important screen in Atlas, because it is the most common one and the one that
decides whether the owner keeps opening the product.

```
┌────────────────────────────────────────────────────────────────┐
│ Atlas · Tuesday 2 September                         As of ▾  ⌘K│
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Nothing materially changed. No action required.               │
│  0 things matter                                               │
│                                                                │
│  ─── WATCHING ─────────────────────────────────────────────    │
│  US liquidity            stable 6 days                         │
│  BTC leverage            elevated, no threshold crossed        │
│  Turkey residency        76 → 71 days, appointment pending     │
│  AI capability           no new evidence since 28 Aug          │
│                                                                │
│  ─── COVERAGE ─────────────────────────────────────────────    │
│  7 sources · all current · 41 items reviewed · 0 material      │
│                                                                │
│                                        Yesterday's brief →     │
└────────────────────────────────────────────────────────────────┘
```

Design rules for quiet days:

- **Never pad.** No "meanwhile in markets", no filler charts, no news.
- **Show work, not content.** `Coverage` proves Atlas looked — sources checked, items
  reviewed, none material. That single line is what converts emptiness into confidence.
- **Countdowns still tick.** Watches with a numeric distance keep the page alive without
  manufacturing events.
- **Same layout, fewer sections.** A quiet day must be recognisably the same page, not a
  different empty-state screen.

---

## 8. The high-risk day

When several material things change at once, the failure mode is an alarm wall where
everything looks equally urgent and the owner triages nothing.

Rules:

1. **The cap does not lift.** Still three above the fold. More material items make the cap
   more important, not less.
2. **Exactly one item may occupy the lead position**, sized larger. If two impacts are
   `ACTION`, the one with higher priority leads and the second appears as a peer beneath
   with the same badge — never two competing hero cards.
3. **A triage band appears** between §1 and §2, present only on high-load days:
   ```
   NOW      Residence permit — 76 days, inside policy window
   VERIFY   Startup competitive pressure — evidence thin
   LATER    3 items in Outlook
   ```
4. **Signal changes shape**: "Three changes matter today; one needs action now." The count
   line does the calming.
5. **No colour escalation.** `ACTION` already carries the single accent. Adding more red
   because there is more news is exactly the fatigue mechanism to avoid.
6. **Everything not in the top three is stated as a number, not a list.** "3 items in
   Outlook" is calmer and more honest than three more cards.

---

## 9. Feedback capture

One control per item: `useful · noise · wrong`, plus an optional note.

- Weight: this is the highest-value UI element in Atlas. It is the only routine input, it
  takes under a minute a day, and it is the signal source pruning, threshold tuning and
  rule promotion all learn from (`PROGRAM.md` §3, §12).
- It must be **one tap, no confirmation, reversible**, and never a modal.
- Placement: inline on each item, and a single summary control at the end for the brief as
  a whole.
- `wrong` opens an optional one-line "what was wrong" field — this is the highest-signal
  text the owner ever produces and is worth the extra interaction.

---

## 10. Acceptance criteria

| # | Criterion | How it is checked |
| --- | --- | --- |
| T1 | Signal renders in every state including total silence | Fixture set incl. quiet, degraded, high-load |
| T2 | Above the fold never exceeds 1 signal + 3 changes + 3 impacts | Layout test at 375 px and 1440 px |
| T3 | No section renders as "no change" | Snapshot test on a quiet-day fixture |
| T4 | The five change kinds are distinguishable in greyscale | Greyscale render review |
| T5 | Every impact shows attention, direction, confidence band, evidence class | Component contract test |
| T6 | No probability displays finer than a 5-point step | Render assertion (ADR-0009) |
| T7 | Every recommendation reaches evidence within three interactions | Interaction-depth audit |
| T8 | An item repeated from a prior brief carries an increased attention class or new evidence | Brief-diff test across two fixture days |
| T9 | A degraded scenario set leads §1 rather than being buried | Degraded fixture |
| T10 | Feedback is one tap, reversible, no modal | Interaction test |
