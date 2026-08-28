# Atlas Architecture

> Atlas is a persistent, evidence-backed personal intelligence system that maintains a
> time-aware model of the world and the owner, calculates the interaction between them,
> and turns material changes into explainable scenarios, risks and decisions **without
> autonomously executing them**.

Design equation: `World State × Personal State → Impact → Scenarios → Decisions → Memory`

This document is the standing description of how Atlas is built. Decisions that change
it require an ADR (`docs/adr/`).

## 1. What Atlas is and is not

Atlas is **not** an autonomous hedge fund, a robo-adviser, an execution bot, a news
summariser, an OpenBB/Bloomberg replacement, a crypto dashboard, a general second
brain, or a chat history pretending to be a database.

Atlas **is** four responsibilities:

1. Maintain a point-in-time representation of the external world.
2. Maintain a canonical representation of the owner's current personal state.
3. Calculate and explain the interactions between the two.
4. Track decisions, forecasts and outcomes so the system becomes **calibrated** rather
   than merely verbose.

The owner is modelled as a generic single-user profile. Owner specifics never appear
in core domain code, so a multi-user product stays possible later.

## 2. Architecture Constitution

Binding unless an ADR explicitly changes a rule.

| ID | Rule |
| --- | --- |
| A01 | Structured truth beats semantic memory. Postgres is authoritative. |
| A02 | Time is a first-class dimension: event, published, ingested, valid-from/to, observed, decision and evaluation times are distinct. History is appended, never overwritten. |
| A03 | Deterministic compute, LLM interpretation. Models never invent numerical truth. |
| A04 | LLMs never write critical truth directly. A validator approves schema, provenance and permission first. |
| A05 | Every conclusion needs provenance: source → raw item → event → narrative → state delta → impact → decision. |
| A06 | Fail loud on missing critical data. Mark incomplete; never substitute a guess. |
| A07 | Same engine for replay and live state. Only the clock and data source differ. |
| A08 | Idempotency is mandatory. Re-ingestion creates no duplicates. |
| A09 | Read-only before action. External execution stays disabled in V1. |
| A10 | Fewer agents, stronger contracts. No role-playing swarm. |
| A11 | "Do nothing" is a valid output. |
| A12 | Confidence is calibrated, not theatrical. No fake precision. |

## 3. System topology

```
EXTERNAL SOURCES  markets / macro / news / geopolitics / laws / AI / climate
        |
        v
   INGESTION  -->  RAW ITEM STORE  -->  NORMALIZE + DEDUP + LINK  -->  EVENT STORE
                                                                          |
                                                                          v
                                                                  NARRATIVE ENGINE
                                                                          |
                                                                          v
                                                                     WORLD STATE
                                                                          |
   STRUCTURED PERSONAL TRUTH  ------------------ x ---------------------- +
   assets / cash / geography / residency /                                |
   career / goals / policies / runway                                     v
                                                                    IMPACT ENGINE
                                                                          |
                                                                          v
                                                                  SCENARIO ENGINE
                                                                          |
                                                                          v
                                                               RISK + POLICY ENGINE
                                                                          |
                                                                          v
                                                                 DECISION JOURNAL
                                                                          |
                                              +---------------------------+--------------------+
                                              v                           v                    v
                                          Dashboard                   Chat / MCP            Alerts
```

## 4. Repository layout and the dependency rule

```
atlas/
├── apps/
│   ├── api/atlas_api/          FastAPI surface (health today; §23 endpoints per queue item)
│   ├── worker/atlas_worker/    scheduler, ingestion jobs, daily cycle (Queue 13)
│   ├── web/                    Next.js dashboard (Queue 16)
│   └── telegram/               alert surface (Queue 15)
├── packages/atlas/
│   ├── domain/                 dependency-light types and rules
│   ├── ingestion/ events/ narratives/
│   ├── world_state/ personal_state/ portfolio/ impact/ scenarios/ policies/ decisions/
│   ├── research/ memory/ providers/ alerts/ observability/
│   └── config.py               process settings (infrastructure, not domain)
├── docs/  migrations/  scripts/  tests/  fixtures/
```

**Dependency rule (ADR-0001).** Dependencies flow in one direction only:

```
apps/*  ->  packages/atlas/<engines>  ->  packages/atlas/domain  ->  stdlib
```

`packages/atlas/domain` may import the standard library and nothing else — no FastAPI,
Starlette, SQLAlchemy, Alembic, httpx/requests, Redis, **Pydantic**, `atlas.config`,
OpenAI/Anthropic SDKs, LangChain/LangGraph, OpenBB, Mem0 or Qlib. Domain types are
stdlib dataclasses; Pydantic is used at API and persistence boundaries.

This is enforced mechanically, not by review:

- `tests/unit/test_architecture_boundaries.py` AST-scans the domain package against a
  denylist and asserts no library package imports a deployable app.
- The `boundaries` CI job installs **pytest only**, with none of the project's runtime
  dependencies, then imports `atlas.domain`. A stray import fails the job outright.

## 5. Time, replay and the clock

No library code reads the wall clock. `atlas.domain.clock` defines a `Clock` protocol
with `SystemClock` (live) and `FixedClock` (replay, fixtures, tests). Every engine
takes an `as_of` derived from an injected clock, which is what makes A07 achievable:
a historical replay and a live cycle execute the *same* code path.

`tests/unit/test_determinism_guards.py` scans library sources for direct
`datetime.now` / `date.today` / `time.time` calls and fails the build on any hit
outside the clock module.

## 6. Deterministic / model split

| Deterministic code | LLMs |
| --- | --- |
| weights, exposure, concentration, runway | extraction, classification |
| mark-to-market, drawdown | entity resolution proposals |
| policy evaluation (`PASS`/`WARN`/`BREACH`/`UNKNOWN_DATA`) | causal synthesis and explanation |
| freshness, evidence counts, dedupe hashes | challenge and falsification |
| scenario mechanics, normalisation, clamping | brief prose from approved structures |
| impact priority arithmetic | narrative naming and summary |

An LLM may propose a structured mutation; a typed validator checks schema, bounds and
provenance before anything is stored (ADR-0004).

## 7. The daily heartbeat

`run_atlas_cycle(as_of)` (Queue 13) is the single entry point for both live operation
and replay:

```
ingest_due_sources -> materialize_events -> update_narratives
  -> build_world_state(previous, deltas) -> load_personal_state
  -> calculate_exposures -> calculate_impacts -> update_scenarios
  -> evaluate_policies -> derive_decision_candidates
  -> persist_run_record -> route_alerts
```

Every run has a `run_id`. The run record must make replay possible; a failed source
degrades the run and is recorded, but never corrupts state.

## 8. Agent graph (Queue 09+)

Restrained by A10: domain researchers (macro, crypto/markets, geo/policy, AI/tech,
fortress) → evidence synthesiser → scenario challenger → scenario judge → personal
impact agent → risk/policy validator (mostly deterministic) → brief writer. New agents
require a measured requirement the existing graph cannot meet.

Model routing uses three abstract classes — `FAST_MODEL` (extraction, classification),
`REASON_MODEL` (causal analysis, challenge, synthesis), `WRITE_MODEL` (final prose) —
kept provider-neutral. Where deterministic code can do the job, it wins outright.

## 8b. Data tiers and model routing

Every value Atlas handles carries a sensitivity tier (L0 public, L1 derived public, L2
personal structured, L3 sensitive personal), and the tier determines which model class may
receive it. Enforcement lives in `LLMProviderPort`, not in prompts, so a call site cannot
opt out. L3 never leaves the owner's perimeter, which is what makes the local-model work
in `PROGRAM.md` §8 a privacy requirement rather than a cost optimisation.

Specification: `docs/DATA_TIERS.md`. Decision: ADR-0010.

## 9. Technology baseline

Python 3.12+, FastAPI, Pydantic at boundaries, PostgreSQL 16 + pgvector, Alembic,
a simple worker and scheduler, a typed workflow graph for agents, Next.js + React +
TypeScript for the dashboard, Docker, GitHub Actions, OpenTelemetry-compatible
telemetry. No Kubernetes, Kafka or microservices in V1. New database or queue
technology requires an ADR.

## 9b. Build / Borrow / Adapt

**Build** — Atlas-specific intelligence, and only this: event model, World State, Personal
State, portfolio and risk math, Impact Engine, Scenario Engine, Policy Engine, Decision
Journal, outcome and calibration, goals and constraints, the opportunity view, and
counterfactual reasoning where justified.

**Borrow or adapt** — commodity infrastructure and patterns: financial data through
OpenBB and direct providers; orchestration patterns from TradingAgents; deterministic
finance patterns from FinRobot; run-cycle and risk concepts from AI Hedge Fund; quant
tooling from Qlib; research-loop patterns; an optional semantic-memory framework; generic
workspace, MCP and local-model concepts from Odysseus.

**Never fork wholesale** — OpenBB, TradingAgents, FinRobot, AI Hedge Fund, Odysseus, or
any generic agent workspace (ADR-0005, ADR-0012).

The test for any new capability: *is this Atlas-specific intelligence, or is it
infrastructure someone else already maintains?* Build the first; reach the second across a
boundary.

## 10. Deviations from Blueprint v1

Recorded rather than silently applied.

| Deviation | Reason |
| --- | --- |
| `packages/atlas/<module>` (import `atlas.<module>`) instead of `packages/<module>` | Avoids generic top-level import names; module set and dependency rule unchanged (ADR-0001). |
| Domain also forbids **Pydantic** | The blueprint bans frameworks generically; naming Pydantic makes the dataclass boundary unambiguous and testable. |
| No root `package.json` yet | The JS toolchain arrives with the dashboard in Queue 16. Shipping a lockfile and a CI job for an empty app costs maintenance and CI time for no signal. |
| `apps/web` and `apps/telegram` are placeholders | Same reason; directories exist so ownership is fixed. |
| Only `/health` and `/health/data` exist | A §23 endpoint returning a plausible empty shape before its engine exists would violate A06. Endpoints ship with the queue item that makes their state real. |
| `Settings.execution_enabled` is `Literal[False]` | Stronger than a default-off boolean: there is no code path that enables execution (ADR-0003). |

## 11. Reading order for a new contributor

1. This document, then `docs/adr/` in order.
2. `docs/DATA_MODEL.md` for the entity vocabulary.
3. `docs/BUILD_QUEUE.md` for what is built and what is next.
4. The engine document for the area you are touching.
5. `docs/SECURITY.md` and `docs/DATA_TIERS.md` before any credential, provider or
   personal-data work.
6. `docs/reviews/` for the reasoning behind decisions that are not obvious from the ADRs
   alone — in particular the [2026-08 cognitive-expansion review](reviews/2026-08-cognitive-expansion.md),
   which records what was **rejected** and why.
