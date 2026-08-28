# Atlas

> A persistent, evidence-backed personal intelligence system that maintains a
> time-aware model of the world and the owner, calculates the interaction between them,
> and turns material changes into explainable scenarios, risks and decisions —
> **without autonomously executing them**.

`World State × Personal State → Impact → Scenarios → Decisions → Memory`

**Status: Queue 00 complete — repository and architecture freeze.** The application
boots, the test suite runs, and the architecture boundaries are enforced in CI. No
feature engines exist yet; see `docs/BUILD_QUEUE.md`.

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
| [DATA_MODEL.md](docs/DATA_MODEL.md) | Entity vocabulary and temporal conventions |
| [BUILD_QUEUE.md](docs/BUILD_QUEUE.md) | What is built, what is next, acceptance criteria |
| [SOURCE_POLICY.md](docs/SOURCE_POLICY.md) | Source reliability classes and dedupe |
| [WORLD_STATE.md](docs/WORLD_STATE.md) · [PERSONAL_STATE.md](docs/PERSONAL_STATE.md) · [IMPACT_ENGINE.md](docs/IMPACT_ENGINE.md) · [SCENARIO_ENGINE.md](docs/SCENARIO_ENGINE.md) · [DECISION_JOURNAL.md](docs/DECISION_JOURNAL.md) | Engine contracts |
| [SECURITY.md](docs/SECURITY.md) | Prohibitions, credentials, data handling |
| [EVALS.md](docs/EVALS.md) | Test suites and model evaluations |
| [CLAUDE.md](CLAUDE.md) · [AGENTS.md](AGENTS.md) | Coding-agent execution contract |

## Licence

Private and unlicensed. Third-party attribution is tracked in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
