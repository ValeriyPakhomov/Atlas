# Source Catalogue

What Atlas reads, why each entry is allowed to exist, and what each one is permitted to
do. Reliability classes and the adapter contract live in
[`SOURCE_POLICY.md`](SOURCE_POLICY.md); this document is the concrete list.

The machine-readable version is `atlas.ingestion.registry`, and it is the authority — if
this file and that module disagree, the module is right and this file is a bug.

---

## The rule that organises everything

> **Series move state. News moves attention.**

A measured series is a number with a publisher, a vintage and a revision history. It can
change a world-state dimension deterministically, and the change is reproducible by anyone
holding the same data.

Reporting is an account of something, written by someone, with an angle. It supplies
evidence, entities, narrative and materiality — it never supplies a score. If reporting
could move a dimension on its own, "the state of the economy" would quietly become *the
mood of the press about* the economy: a real quantity, but not the one we are measuring,
and one that peaks exactly when everyone already knows.

`SourceSpec.may_move_state` is derived from kind and class, not declared, so no catalogue
entry can opt into being both.

---

## The backbone: open official data

All of this is genuinely open, and its terms permit exactly this use.

| Key | Publisher | Gives | Access |
| --- | --- | --- | --- |
| `fred` | St. Louis Fed | Rates, liquidity, USD, inflation, credit spreads | free key |
| `ecb_data` | European Central Bank | Euro-area rates, balance sheet, FX | open |
| `eurostat` | European Commission | HICP, EU growth and labour | open |
| `worldbank` | World Bank | Slow country context | open |
| `imf` | IMF | Forecasts, cross-country comparison | open |
| `us_treasury_fiscal` | US Treasury | Yield curve, issuance | open |
| `eia` | US EIA | Energy stocks and production | free key |

Plus scheduled official publications, which are class A and event-driven rather than
sampled: `federal_reserve_press`, `ecb_press`, `sec_edgar`.

## The other half: reporting and coverage

| Key | Role | Class | May move state |
| --- | --- | --- | --- |
| `guardian_open` | Quality reporting with a real open API | B | **no** |
| `gdelt` | Is this story spreading, and where | C | **no** |

Two, not six, and on purpose. Adding a fifth outlet does not add a fifth independent view
of the world; it adds a fifth retelling of the same wire copy. Atlas already treats that
correctly — identical content deduplicates globally, so syndication cannot masquerade as
corroboration — but the honest statement is that **breadth of outlets is not breadth of
evidence**. Breadth comes from adding a *different kind* of source: a filing, a statistical
release, a regulator, a counterparty.

The catalogue grows when a gap is demonstrated, not on principle. Every entry is a
permanent maintenance obligation.

---

## Assessing state from series

A world-state dimension is scored on the −3..+3 scale defined in
[`WORLD_STATE.md`](WORLD_STATE.md). Dimension keys are rows, not code (ADR-0006), so the
mapping below is a **starting configuration**, not a schema.

| Dimension | Series | Reading |
| --- | --- | --- |
| `macro.rates` | `DFF`, `DGS2`, `DGS10`, `T10Y2Y` | Level vs trailing window; curve slope as its own signal |
| `macro.liquidity` | `WALCL`, `RRPONTSYD`, `WTREGEN` | Net change in reserves, not any single level |
| `macro.usd` | `DTWEXBGS`, `DEXUSEU` | Trailing z-score of the broad index |
| `macro.inflation` | `CPIAUCSL`, `PCEPILFE`, Eurostat HICP | Year-on-year, plus the change in the rate of change |
| `macro.growth` | `GDPC1`, `UNRATE`, `ICSA` | Claims lead; GDP confirms late |
| `markets.risk_appetite` | `BAMLH0A0HYM2`, `VIXCLS` | Credit spread is the honest one; VIX is fast and noisy |
| `energy.oil` | `DCOILWTICO`, `DCOILBRENTEU`, EIA stocks | Level plus inventory direction |

Three rules make the scoring deterministic and honest:

1. **A level is not a state.** State is where a level sits against its own history — a
   trailing standardised score over a declared window — together with its direction.
   "10-year at 4.3%" is not information; "4.3%, the top decile of three years, and rising"
   is.
2. **A revision is a new observation, not an overwrite.** Statistical agencies revise.
   Atlas stores vintages, so a replay of March uses what was actually knowable in March
   (A02, A07). A backtest that silently uses revised data is a backtest that lies.
3. **A stale series degrades the dimension rather than holding its last value.** The
   `Measured` type carries that gap to the brief, which renders `STALE` instead of a
   plausible number (A06).

## What news does instead

Reporting enters the same pipeline, is deduplicated the same way, and passes the exposure
gate the same way. What it produces is an `Event` and, through corroboration, a
`Narrative` — the *why* attached to a move the series already showed. The two meet at the
Atlas Score, where a dimension's ordinal is multiplied by the owner's exposure to it, and
each point is carried by a `Contribution` row the interface renders directly.

Order of arrival matters and is usually the opposite of what it feels like: the series
moves, then the reporting explains it. When reporting arrives first, that is a question to
research, not a state change.

## Before an adapter is written

Every entry is `NEEDS_CHECK` until someone contacts the live service and records what they
found. Feed availability and terms change, and an adapter written against an unverified
entry is a bug waiting for a deploy. `SourceRegistry.ready_for_adapters()` is empty by
construction until then.

Checks required per source: the endpoint answers; the terms permit private,
non-redistributed use; the rate limit and any required `User-Agent` are recorded; the
freshness SLA is measured rather than assumed; and no credential is committed anywhere
outside the environment.
