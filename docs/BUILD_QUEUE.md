# Build Queue

One item at a time. Each requires tests and a documented acceptance result before the
next begins. Every item ends with the report block in `CLAUDE.md`.

If a queue item shows that the architecture is wrong, **stop and propose an ADR**.
Do not silently change the architecture.

| # | Item | Status |
| --- | --- | --- |
| 00 | Repository and architecture freeze | **Done** |
| 01 | Domain types + persistence foundation | Next |
| 02 | Source adapter contract | Pending |
| 03 | Event normalization and dedupe | Pending |
| 04 | OpenBB market adapter | Pending |
| 05 | Narrative Engine | Pending |
| 06 | World State V1 | Pending |
| 07 | Personal State V1 | Pending |
| 08 | Deterministic Portfolio Engine | Pending |
| 09 | Impact Engine V1 | Pending |
| 10 | Scenario Engine V1 | Pending |
| 11 | Policy Engine | Pending |
| 12 | Decision Journal + outcomes | Pending |
| 13 | Daily `run_atlas_cycle` | Pending |
| 14 | Daily Brief | Pending |
| 15 | Alerts | Pending |
| 16 | Dashboard V1 | Pending |
| 17 | MCP / chat interface | Pending |
| 18 | Semantic memory | Pending |
| 19 | Quant Lab (Qlib evaluation) | Pending |

## Queue 00 — Repository and architecture freeze ✅

**Delivered:** repo skeleton; `CLAUDE.md`; `docs/ARCHITECTURE.md`; ADRs 0001–0005;
CI baseline; lint/typecheck/test commands; boundary and determinism guards;
`THIRD_PARTY_NOTICES.md`.

**Acceptance met:**
- empty app boots locally (`make api` → `/health` 200; `make worker` → ready);
- unit-test suite runs (`make test`);
- architecture boundaries documented **and enforced in CI**.

## Queue 01 — Domain types + persistence foundation (next)

Implement core IDs, timestamp conventions, `Source`, `RawItem`, `Evidence`, `Event`,
`Narrative`, `RunRecord`, plus Alembic and repositories.

**Acceptance:** migrations apply from zero; the domain package has no network or
framework imports; CRUD/repository tests green.

## Remaining acceptance criteria

- **02** — the same fixture ingested twice produces no duplicates.
- **03** — golden fixtures merge duplicate reporting into a single event.
- **04** — deterministic normalized snapshots for a small fixture universe; a provider
  failure becomes a typed Atlas error; OpenBB types never leave the adapter.
- **05** — corroborating events strengthen a narrative; contradiction weakens it;
  repeated duplicates do not strengthen it.
- **06** — two historical fixture days replay; only material changes produce deltas;
  every delta has provenance. Start with 10–15 dimensions.
- **07** — the snapshot is reproducible from point-in-time records; stale semantic
  memory cannot alter it.
- **08** — full unit coverage of critical arithmetic branches; no LLM dependency.
- **09** — the BTC/TRY/rates/AI/migration fixture set produces expected impacts;
  inferred and calculated impacts are distinguishable.
- **10** — probabilities always valid; one low-quality source cannot cause an extreme
  jump; all changes replayable.
- **11** — `PASS`/`WARN`/`BREACH`/`UNKNOWN_DATA`; no LLM override path.
- **12** — a decision preserves the evidence and state used at decision time; a
  retrospective cannot mutate it.
- **13** — fixture replay is deterministic; a failed source does not corrupt state; the
  cycle produces an immutable `RunRecord`.
- **14** — no news dump; no repeated old event without a new delta; fact, inference and
  speculation separated.
- **15** — `CRITICAL` requires qualifying evidence or a rule; duplicate alerts suppressed.
- **16** — the dashboard reads the backend with no business logic in the frontend;
  "What changed?" is the primary home experience.
- **17** — an external model answers from live Atlas state without direct DB access;
  tool responses carry provenance IDs.
- **18** — memory enriches reasoning and can never mutate canonical state outside an
  explicit validated workflow.
- **19** — evaluate Qlib only after V1 operates reliably.

## First vertical slice

The first genuinely useful Atlas proves the whole loop on a deliberately tiny scope
(blueprint §36): MarketTwits/manual news, FRED macro, BTC/ETH/SOL, a USD proxy, a US
rates proxy, Turkey inflation/FX, an AI news source; the ten V1 world dimensions;
personal cash, crypto, liquid assets, burn, base and candidate geographies, income
categories, migration deadlines and policies. Output: world snapshot, deltas, portfolio
exposure, 3–5 impacts, a scenario set, a daily brief, and one policy warning or "no
action".

**If that slice does not create obvious daily value, do not expand the source count.**

## Non-goals for V1

Autonomous trading, broker execution, wallet signing, auto-rebalancing, multi-user
SaaS, billing, a native mobile app, hundreds of agents, local LLM infrastructure, a
complex ML regime engine, a Bloomberg replacement, real-estate valuation, a complete
global immigration database. Each requires an ADR to enter scope.
