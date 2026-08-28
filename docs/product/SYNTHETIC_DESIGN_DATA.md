# Synthetic Design Data

One coherent fictional day, for designing and prototyping before the engines exist. Every
screen and component in this repository can be populated from it, and the result tells a
single story rather than a set of disconnected demo cards.

**No real owner data.** Every figure is invented. This file is L0 by construction and is
the only owner-shaped data that may ever live in this public repository
(`docs/SECURITY.md`).

---

## The story in one paragraph

It is Friday 28 August 2026. Global liquidity is improving and the dollar is softening —
mildly favourable for the owner's crypto exposure. But three things pull the other way:
Turkish FX pressure has intensified, compressing local purchasing power; the owner's
Turkish residence permit has just entered its 90-day policy window with 76 days left; and
crypto leverage is elevated against a portfolio that is 55% crypto. Meanwhile the portfolio
feed has been stale for nine days, two sources disagree on Turkish inflation, and one
scenario driver could not be evaluated — so the scenario set is `DEGRADED` with 15%
unassessed. **Atlas is moderately confident about the world and not confident about the
owner's current position, and it says so.**

This is deliberately the interesting case: one `ACTION`, real ambiguity, and visible data
problems. Design against it, then design the quiet day (§9).

---

## 1. World state — 2026-08-28, run `run_2026-08-28T07:00Z`

Overall regime: *cautious improvement* · confidence moderate

| Dimension | Score | Dir | Conf | Fresh | Δ | Relevance |
| --- | --- | --- | --- | --- | --- | --- |
| `macro.liquidity` | `+1` | rising | moderate | 4h | `+1 from 0` | exposed |
| `macro.rates` | `−1` | falling | high | 4h | — | exposed |
| `macro.usd` | `0` | falling | moderate | 4h | `0 from +1` | exposed |
| `markets.risk_appetite` | `+1` | rising | moderate | 6h | — | exposed |
| `crypto.regime` | `+1` | rising | moderate | 2h | — | exposed |
| `crypto.leverage` | `+2` | rising | high | 2h | `+2 from +1` | **exposed** |
| `geography.tr.economy` | `−2` | falling | high | 1d | — | **exposed** |
| `geography.tr.fx` | `−2` | falling | high | 6h | `−2 from −1` | **exposed** |
| `technology.ai_capability` | `+2` | rising | moderate | 2d | `+2 from +1` | exposed |
| `geopolitics.global` | `−1` | stable | low | 1d | — | indirect |

### Material deltas (5)

| # | Dimension | Change | Materiality | Narrative |
| --- | --- | --- | --- | --- |
| D1 | `geography.tr.fx` | `−1 → −2` | 0.81 | `turkey-fx-pressure` |
| D2 | `crypto.leverage` | `+1 → +2` | 0.74 | `crypto-leverage-buildup` |
| D3 | `macro.liquidity` | `0 → +1` | 0.62 | `usd-liquidity-expansion` |
| D4 | `technology.ai_capability` | `+1 → +2` | 0.58 | `ai-agent-capability-acceleration` |
| D5 | `macro.usd` | `+1 → 0` | 0.44 | `usd-liquidity-expansion` |

## 2. Personal state — as of 2026-08-28

Base currency USD · base Istanbul · **portfolio feed 9 days stale**

| | |
| --- | --- |
| Liquid net worth | `184,200 USD` · **9d stale** |
| Allocation | crypto 55% · cash 31% · liquid traditional 14% |
| Currency exposure | USD 62% · TRY 21% · EUR 17% |
| Concentration | largest single asset 38% of liquid |
| Monthly burn | `4,900 USD` · current |
| Runway | `14.2 months` · derived, inherits stale |
| Income | modelling (TRY, mobility-dependent) · contract dev (EUR, remote) · Atlas (none yet) |

**Geography**

| Country | Role | Status | Deadline |
| --- | --- | --- | --- |
| Turkey | `current_base` | residence permit | **expires 2026-11-12 — 76 days** |
| Italy | `candidate` | none | — |
| Georgia | `fallback` | visa-free | — |
| Germany | `work_market` | none | — |

**Objectives** (all `owner`-authored, `active`)

| # | Title | Direction | Horizon | Priority |
| --- | --- | --- | --- | --- |
| O1 | Maintain ≥12 months liquid runway | `maintain` | short | 1 |
| O2 | Establish an EU base by 2028 | `attain` | long | 2 |
| O3 | Avoid dependence on a single country | `avoid` | medium | 3 |
| O4 | Make Atlas a working daily system | `attain` | medium | 4 |

**Preferences:** O1 > O2 (strong) · O3 > O4 (weak)

**Atlas-proposed, awaiting acceptance:** *"You appear to be optimising for geographic
optionality — three decisions since June preserved mobility at a measurable cost. Make it
explicit?"* — `authored_by = atlas_proposed`, `accepted_at = null`, **inert**.

**Policies**

| Policy | Result |
| --- | --- |
| Liquid runway ≥ 12 months | `PASS` (14.2, from stale input) |
| Crypto ≤ 60% of liquid | `WARN` (55%, approaching) |
| Residency deadline alert ≥ 90 days | `BREACH` (76 days) |
| Single-country dependency ≤ threshold | `UNKNOWN_DATA` (income attribution incomplete) |

## 3. Impacts (5)

| # | Domain | Dir | Attention | Conf | Evidence class | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| I1 | `residency` | adverse | **`ACTION`** | high | `DIRECT_RULE` | Permit expires inside your 90-day policy window |
| I2 | `currency` | adverse | `REVIEW` | moderate | `DIRECT_RULE` | TRY weakness is compressing local purchasing power |
| I3 | `portfolio` | adverse | `REVIEW` | moderate | `DIRECT_CALCULATED` | Elevated leverage raises drawdown risk on a 55% crypto position |
| I4 | `startup` | adverse | `VERIFY` | low | `INFERRED_CAUSAL` | Faster AI capability may compress Atlas's differentiation window |
| I5 | `portfolio` | **favourable** | `REVIEW` | moderate | `INFERRED_CAUSAL` | Improving liquidity and a softer dollar modestly improve risk/reward |

I5 is the **opportunity case**: favourable direction with `objective_refs = [O1]` — it
appears in the same ranked list with a direction marker, never in a separate section.

### I1 — the `ACTION`, in full

```
domain              residency
direction           adverse
attention_class     ACTION           qualifying rule: deadline_within_policy_window
confidence          high (0.88)      evidence: DIRECT_RULE
components          severity high · exposure high · urgency high · irreversibility moderate
objectives          O2 EU base by 2028 · O3 avoid single-country dependence
priority            0.79

causal chain
  permit valid_until 2026-11-12   [rule]
  → 76 days remain                [calculated]
  → policy window is 90 days      [rule]
  → renewal lead time 30–45 days  [rule, unverified]
  → decision window is ~30 days   [calculated]

invalidated by      a confirmed renewal appointment
related scenarios   none
candidate           PREPARE — begin renewal documentation, review in 7 days
```

### I4 — the `VERIFY` case

Low confidence, `INFERRED_CAUSAL`, one weak source. It is `VERIFY` rather than `REVIEW`
precisely because it is potentially material and poorly evidenced — under a naive
confidence-weighted ranking it would have been buried (ADR-0008).

## 4. Scenarios — 3–6 months, `DEGRADED`

`integrity_status = DEGRADED` · `unknown_mass = 15%` · reason: *TRY inflation driver could
not be evaluated — sources conflict*

| Scenario | Prob | Prev | Moved | Thesis |
| --- | --- | --- | --- | --- |
| Soft landing | 45% | 40% | ▲ | Liquidity improves gradually without a growth shock |
| Reflation | 20% | 20% | — | Growth and inflation both re-accelerate |
| Recession | 20% | 25% | ▼ | Tightening bites with a lag |
| *not assessed* | 15% | 15% | — | — |

Soft-landing drivers: `+ easing financial conditions` (strengthening) · `+ improving risk
appetite` (stable) · `− geopolitical uncertainty` (strengthening).
Invalidated by: a funding-stress print, or CPI above 4%.
Personal implication: moderately favourable for crypto exposure → I5.

**The 15% is never redistributed.** It renders as a hatched segment labelled *not assessed*.

## 5. Data conditions

| Kind | Subject | Detail | Blocks |
| --- | --- | --- | --- |
| `STALE` | Portfolio feed | 9 days since `observed_at`; SLA 24h | Runway, concentration, I3 confidence |
| `CONFLICTING` | TR inflation, Aug print | Source A 61.8%, Source B 58.4% | TRY driver, scenario integrity |
| `UNVERIFIED` | Permit renewal lead time | 30–45 days asserted, not confirmed | I1 decision window |
| `UNKNOWN_DATA` | Single-country policy | Income attribution incomplete | Policy result |
| `DEGRADED` | Scenario set 3–6 months | 15% unassessed | Scenario-derived conclusions |

## 6. Forecasts

**Resolved** — *"Will TRY/USD exceed 45 before 1 August 2026?"*
Owner 0.70 (2026-06-02) · Atlas 0.55 (2026-06-02) · outcome **true** · **owner closer**.

**Open** — *"Will the owner hold a valid Turkish residence permit on 1 January 2027?"*
Resolve by 2027-01-01 · Atlas 0.72 (2026-08-28) · owner not yet predicted.

The resolved case is deliberately one the owner won: the calibration surface must be able
to say *the owner was better here*, or it is not calibration.

## 7. Decisions

| # | Date | Question | Type | Status | Outcome |
| --- | --- | --- | --- | --- | --- |
| DC1 | 2026-06-02 | Reduce crypto ahead of expected TRY weakness? | `NO_ACTION` | resolved | **right call, bad luck** — premise correct, TRY fell further than modelled |
| DC2 | 2026-07-14 | Commit to Milan as candidate base? | `WAIT` | open | review 2026-09-15 |
| DC3 | 2026-08-11 | Accept a 6-week modelling contract in Istanbul? | `REVIEW_LOCATION` | resolved | **worked** — accepted; preserved runway without lengthening permit exposure |
| DC4 | 2026-08-28 | Begin permit renewal now? | `PREPARE` | candidate | — |

DC1 is the important fixture: it exercises the retrospective cell that most products cannot
express — a good decision with a bad outcome.

## 8. Today, assembled

```
Signal      "One change materially affects your residency timeline."
            3 things matter · 1 needs attention
Changes     WORLD  Turkey FX pressure intensified      −1 → −2
            YOU    Residence permit: 76 days remain    entered policy window
            IMPACT Local purchasing power deteriorating  REVIEW
            2 more ▾
Impacts     I1 ACTION · I3 REVIEW · I4 VERIFY        (I2, I5 below fold)
Atlas view  Turkish FX weakness now compounds with a permit deadline you had
            planned to handle later. Neither alone would be urgent; together they
            shorten the window in which you can choose calmly. Your crypto
            exposure is unchanged and within policy, but the position figures are
            nine days old, so treat the portfolio conclusions as provisional.
Candidates  PREPARE renewal documentation · NO_ACTION on crypto allocation
Scenarios   included — soft landing moved 40% → 45%
Invalidator a confirmed renewal appointment would remove the ACTION
Unknowns    4 conditions (§5)
Watching    US liquidity · BTC funding > 0.05% · permit appointment
Coverage    7 sources · 6 current, 1 stale · 63 items reviewed · 5 material
```

## 9. The quiet-day variant — Tuesday 2 September

Same owner, five days later. No material deltas; the permit countdown continues; the
portfolio feed has been refreshed.

```
Signal      "Nothing materially changed. No action required."   0 things matter
Watching    US liquidity stable 6 days · BTC leverage elevated, no threshold crossed
            Turkey residency 71 days, appointment pending · AI capability no new evidence
Coverage    7 sources · all current · 41 items reviewed · 0 material
```

Every other section is **absent**, not empty. This variant must be built alongside the
main one — a design system validated only against a busy day will produce a product that
looks broken when it is working correctly.
