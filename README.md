# Atlas

> A persistent, evidence-backed personal intelligence system that maintains a
> time-aware model of the world and the owner, calculates the interaction between them,
> and turns material changes into explainable scenarios, risks and decisions —
> **without autonomously executing them**.

`World State × Personal State → Impact → Scenarios → Decisions → Memory`

**Status: Queue 01 complete — domain types and PostgreSQL persistence foundation.**
The first schema revision, repositories and sensitivity contracts are exercised against
PostgreSQL 16 in CI. Queue 02 (the source-adapter contract) is next; no feature engines
exist yet. See `docs/BUILD_QUEUE.md`.

## What Atlas is not

Not a trading bot, robo-adviser, execution agent, news summariser, OpenBB/Bloomberg
replacement, crypto dashboard, general second brain, or a chat history pretending to be
a database. Atlas V1 is **read-only** with respect to money, brokers, wallets and
external systems (ADR-0003).

## Quick start

```bash
make bootstrap     # uv venv (Python 3.12) + editable install + .env
make check         # lint, format check, typecheck, tests
make api           # http://127.0.0.1:8000/health
make worker        # one worker readiness run
make db-up         # Postgres 16 + pgvector on :5432
make migrate       # apply the latest Alembic revision
make db-test-up    # isolated Postgres 16 test database on :5433
```

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+. Docker is needed only for
the database.

## Layout

```
apps/api/          FastAPI surface            packages/atlas/domain/     stdlib-only types and rules
apps/worker/       scheduler and daily cycle  packages/atlas/<engines>/  ingestion → … → decisions
apps/web/          dashboard (Queue 16)       docs/                      architecture, ADRs, engines
apps/telegram/     alerts (Queue 15)          tests/                     unit, integration, replay, golden, evals
```

Dependencies flow one way only:

```
apps/*  ->  packages/atlas/<engines>  ->  packages/atlas/domain  ->  stdlib
```

`packages/atlas/domain` imports the standard library and nothing else. This is checked
by `tests/unit/test_architecture_boundaries.py` and by a CI job that installs **pytest
alone** and imports the domain package.

## Documentation

| Document | Purpose |
| --- | --- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and the Architecture Constitution (A01–A12) |
| [adr/](docs/adr/) | Binding architecture decisions |
| [reviews/](docs/reviews/) | Architecture reviews — what was considered, and what was rejected |
| [DATA_MODEL.md](docs/DATA_MODEL.md) | Entity vocabulary and temporal conventions |
| [BUILD_QUEUE.md](docs/BUILD_QUEUE.md) | What is built, what is next, acceptance criteria |
| [PROGRAM.md](docs/PROGRAM.md) | Long-horizon programme: quality model, learning loop, phases, hardware, local models, skills, rhythm |
| [SOURCE_POLICY.md](docs/SOURCE_POLICY.md) | Source reliability classes and dedupe |
| [WORLD_STATE.md](docs/WORLD_STATE.md) · [PERSONAL_STATE.md](docs/PERSONAL_STATE.md) · [IMPACT_ENGINE.md](docs/IMPACT_ENGINE.md) · [SCENARIO_ENGINE.md](docs/SCENARIO_ENGINE.md) · [DECISION_JOURNAL.md](docs/DECISION_JOURNAL.md) | Engine contracts |
| [SECURITY.md](docs/SECURITY.md) | Prohibitions, credentials, data handling |
| [DATA_TIERS.md](docs/DATA_TIERS.md) | Sensitivity tiers L0–L3 and which model may see what |
| [EVALS.md](docs/EVALS.md) | Test suites and model evaluations |
| [CLAUDE.md](CLAUDE.md) · [AGENTS.md](AGENTS.md) | Coding-agent execution contract |

## This repository is public; the system it describes is not

Atlas is a single-owner private system. **This repository is public so the
architecture can be reviewed**, and that sets a hard boundary on what may ever be
committed here:

| Belongs here | Never here |
| --- | --- |
| Architecture, ADRs, engine contracts | Personal state of any kind |
| Engine code and deterministic operators | Real balances, positions, account or wallet identifiers |
| Synthetic fixtures | Fixtures derived from real personal data |
| Configuration **names** (`.env.example`) | Configuration **values**, credentials, tokens |
| Owner-genericity in the domain model | Residency documents, addresses, health, relationships |

Personal state lives only in the owner's private deployment — the database and its
backups — never in version control. This is enforced by ADR-0002 (canonical state is
the database, not the repository) and by `docs/SECURITY.md`.

If Atlas ever needs to hold something that cannot be public, it goes in a private
deployment or a private repository — not into this one with a later `git filter-repo`.
History is not retractable once pushed.

## Licence

Unlicensed — no rights granted. Third-party attribution is tracked in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
