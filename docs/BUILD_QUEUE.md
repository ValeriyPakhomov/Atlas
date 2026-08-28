# Build Queue

> Reframed by [the 2026-08 cognitive-expansion review](reviews/2026-08-cognitive-expansion.md)
> and reconciled before persistence: Queue 01 has one exact scope below; 15/17/18 are
> reframed; everything else is unchanged.
>
> This document covers *what to build next*. For the long-horizon programme — where
> quality comes from, how the system learns, phase gates, hardware and local-model
> migration — see [PROGRAM.md](PROGRAM.md).

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
| 15 | Alerts — Atlas owns semantics, channels are replaceable | Pending |
| 16 | Dashboard V1 | Pending |
| 17 | Read-only MCP server + API integration surface | Pending |
| 18 | Semantic memory — comparative checkpoint, then choose | Pending |
| 19 | Quant Lab (Qlib evaluation) | Pending |

## Queue 00 — Repository and architecture freeze ✅

**Delivered:** repo skeleton; `CLAUDE.md`; `docs/ARCHITECTURE.md`; ADRs 0001–0005;
CI baseline; lint/typecheck/test commands; boundary and determinism guards;
`THIRD_PARTY_NOTICES.md`.

**Acceptance met:**
- empty app boots locally (`make api` → `/health` 200; `make worker` → ready);
- unit-test suite runs (`make test`);
- architecture boundaries documented **and enforced in CI**.

## ADR gates

Architectural decisions must be accepted before the queue item whose schema or chokepoint
they control.

| ADR | Question it settles | Blocks |
| --- | --- | --- |
| [0010](adr/0010-data-tiers-and-model-routing.md) — **Accepted** | Sensitivity classification, privacy projection and model routing | **Queue 01** tier infrastructure and every LLM call |
| [0011](adr/0011-goals-are-owner-authored-state.md) — **Accepted** | Canonical owner intent and temporal authority | **Queue 01** Objective/Preference schema |
| [0007](adr/0007-deterministic-idempotency.md) | Whether embeddings may decide deduplication | **Queue 03** |
| [0006](adr/0006-dimensions-as-data.md) | Whether dimension keys are data or a hard-coded enum | **Queue 06** |
| [0008](adr/0008-impact-priority-and-attention.md) | How impacts are ranked, and where confidence enters | **Queue 09** |
| [0009](adr/0009-probability-integrity.md) | What an unassessable scenario does to a probability set | **Queue 10** |

Queue 01 may begin only after ADR-0010 and ADR-0011 are Accepted, the managed PostgreSQL
provider is recorded, and `DATA_MODEL.md` / `BUILD_QUEUE.md` are mutually consistent.
Those prerequisites are now met: production uses **Neon PostgreSQL 16 in AWS Frankfurt
(`eu-central-1`)**; development and tests use local Docker PostgreSQL 16. This is an
operational provider choice, not a Neon dependency in the domain.

## Queue 01 — Domain types + persistence foundation (next)

Implement only:

- common IDs, time, provenance and sensitivity primitives;
- `Source`, `RawItem`, `Evidence`, `Event`, `Narrative`, `RunRecord`;
- `Objective`, `Preference`;
- `ForecastQuestion`, `ForecastPrediction`, `ForecastResolution`;
- sensitivity-tier infrastructure required for persisted fields and mixed-content values;
- SQLAlchemy persistence, repositories, Alembic and PostgreSQL test infrastructure.

Do **not** implement empty future tables or engines: World/Personal State, Portfolio,
Impact, Scenario, Policy, Decision, semantic memory, MCP, UI or execution. Their vocabulary
may be documented in `DATA_MODEL.md`; their persistence lands with their queue item.

**Acceptance:**

- migrations apply from zero and the supported downgrade/upgrade path is clean;
- tests run against PostgreSQL 16 — no SQLite fallback;
- the domain package has no ORM, FastAPI, network or LLM dependency;
- persistence round trips and foreign-key/integrity behaviour are tested;
- Objective/Preference authoritative selection applies acceptance, active status and
  temporal validity at arbitrary `as_of`; unaccepted Atlas proposals are inert;
- active ordinal preference cycles are rejected;
- Forecast probabilities are bounded, resolution criteria are mandatory, resolutions have
  provenance and historical predictions are immutable append-only rows;
- effective-tier inheritance and mixed/free-text fail-high behaviour are tested;
- privacy-projection receipts are represented and validated without implementing any
  domain-specific projection;
- every persisted column declares schema maximum/default tiers and every relevant value
  follows the effective-tier contract;
- Queue 00 tests remain green.

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
- **15** — a qualifying rule or evidence is required before `ACTION`;
  duplicate alerts suppressed; delivery channels are replaceable adapters with no alert
  semantics of their own; uses `ACTION | VERIFY | REVIEW | BACKGROUND | SUPPRESS`, not a
  separate severity enum.
- **16** — the dashboard reads the backend with no business logic in the frontend;
  "What changed?" is the primary home experience.
- **17** — several clients (ChatGPT, Claude, Odysseus, web, Telegram) answer from live
  Atlas state simultaneously without direct DB access; tool responses carry provenance IDs;
  **removal test** (ADR-0012): with every external client disconnected, the daily cycle and
  a replay produce byte-identical results.
- **18** — a written comparison of candidates (pgvector-native, Mem0, Letta/MemFS, Lethe,
  and whatever is mature at that time) precedes any implementation choice. Selection
  criteria include formal supersession semantics: current / outdated / superseded /
  temporary / preference / changed preference / lesson / disproven lesson. Whichever is
  chosen, memory enriches reasoning and can never mutate canonical state outside an
  explicit validated workflow.
- **19** — evaluate Qlib only after V1 operates reliably.

## Beyond V1 — sequenced, not scheduled

Deliberately off the numbered queue so the V1 slice is not diluted (review §E):
opportunity scan engine; Option/Counterfactual engine; causal-graph extraction from
accumulated impacts; replanning trigger as a Watch over an externally held plan; and the
**Execution Gateway** — a separate system requiring an ADR that supersedes ADR-0003.

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
