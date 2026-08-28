# ADR-0001 — Single Atlas monorepo with an enforced dependency rule

- Status: Accepted
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Atlas spans an API, a worker, a dashboard, a Telegram surface and roughly sixteen
library modules that share one domain model. Splitting these across repositories at
this stage would force cross-repo version coordination before the domain model has
stabilised, and the blueprint's central risk is not deployment topology but **domain
drift** — engine code quietly acquiring framework, network or provider dependencies
until replay and offline testing become impossible.

The blueprint (§5) specifies `packages/<module>` and `apps/<service>` with the rule
that `packages/domain` may not import FastAPI, LangGraph, LLM clients, OpenBB, Mem0
or web-framework code.

## Decision

One repository, `atlas`, laid out as:

- `packages/atlas/<module>/` — libraries, importable as `atlas.<module>`.
- `apps/<service>/<package>/` — deployable units (`atlas_api`, `atlas_worker`).
- `docs/`, `migrations/`, `scripts/`, `tests/`, `fixtures/` at the root.

Packaging is a **single Python distribution** (`atlas`, hatchling, Python 3.12+) that
ships all three import packages. Dependencies flow in exactly one direction:

```
apps/*  ->  packages/atlas/<engines>  ->  packages/atlas/domain  ->  stdlib
```

`packages/atlas/domain` may import the standard library and nothing else. In
particular it may not import Pydantic, `atlas.config`, or any I/O library; domain
types are stdlib dataclasses, and Pydantic is used at API and persistence boundaries
only.

### Deviation from Blueprint §5

The blueprint's tree implies `packages/domain` importable as `domain`. Atlas uses
`packages/atlas/domain` importable as `atlas.domain` instead. Reason: top-level import
names such as `domain`, `events`, `policies` and `memory` are generic enough to collide
with third-party distributions, and a shared `atlas.` prefix makes the boundary visible
at every import site. The module names, ownership and dependency rule are unchanged.

## Consequences

- One version, one CI pipeline, one test suite; atomic cross-module refactors.
- The repository will get large. Accepted for a single-owner system; extraction into
  separate distributions stays possible because the dependency direction is enforced.
- Every module directory exists from Queue 00 with a docstring naming its queue item,
  so ownership is settled before feature code lands.

## Enforcement

Not prose — CI:

- `tests/unit/test_architecture_boundaries.py` AST-scans every file under
  `packages/atlas/domain` for a denylist of framework, network, ORM, LLM and
  provider imports, and asserts that no library package imports `atlas_api` or
  `atlas_worker`.
- The `boundaries` CI job installs **pytest only** — no runtime dependencies — and
  imports `atlas.domain`. If domain ever acquires a third-party import, the job fails
  on the import itself rather than on an assertion.

## Alternatives considered

- **Polyrepo per service.** Rejected: coordination cost before the domain model is
  stable, with no benefit while there is one deployer.
- **uv workspace with a distribution per package.** Rejected for Queue 00: sixteen
  `pyproject.toml` files to express a rule that one CI job already enforces. Revisit
  if a package genuinely needs independent release cadence.
