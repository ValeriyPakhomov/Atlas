# Testing and Evaluation Strategy

Two different things live here. **Tests** are deterministic and gate every merge.
**Evals** measure model-dependent quality, are allowed to be noisy, and run on demand.

## Test suites

| Suite | Path | Gates CI | Purpose |
| --- | --- | --- | --- |
| Unit | `tests/unit/` | yes | pure domain functions, boundaries, determinism guards |
| Integration | `tests/integration/` | yes | repositories, migrations, adapters against fixtures |
| Replay | `tests/replay/` | yes | historical replay determinism |
| Golden | `tests/golden/` | yes | known event clusters → expected events/narratives |
| Evals | `tests/evals/` | no (`-m evals`) | model-quality measurement |

## What each suite must prove

**Unit.** Portfolio arithmetic, policy evaluation, scoring, state deltas and scenario
normalisation. Queue 08 requires full coverage of critical arithmetic branches.

**Contract.** Every source adapter satisfies the same `SourceAdapter` contract against
fixtures, so a new adapter cannot invent its own semantics.

**Idempotency.** Ingest the same batch twice; event and narrative counts must not
double (A08).

**Point-in-time.** A historical replay must never use information published after
`as_of`. This is the test that catches leakage, and it is the reason time is injected
rather than read (A02, A07).

**Missing data.** An owned asset without a price must produce an explicit incomplete
state — never a guessed price, never a silent zero (A06).

**Golden research set.** 20–50 known historical event clusters with expected event and
narrative assignments, including duplicate reporting that must merge into one event.

**World State evals.** Proposed dimension changes compared against human-reviewed
fixtures.

**Impact evals.** Fixture scenarios with known exposure: BTC shock; TRY shock with local
expense exposure; rate shock with bonds and cash; AI capability jump with startup and
career effects; migration rule change with geography plans.

**Scenario calibration.** Brier scores tracked for scenarios with objectively
resolvable outcomes.

## Brief quality bar (Queue 14)

The daily brief passes only if:

- no unsupported factual claims;
- no repeated old news without a new delta;
- top items correspond to the highest impact and materiality;
- citations and source links are present;
- "no action" is an allowed and well-formed output;
- fact, inference and speculation are clearly distinguished.

## Architecture guards (active now)

- `tests/unit/test_architecture_boundaries.py` — the domain dependency rule.
- `tests/unit/test_determinism_guards.py` — no direct wall-clock reads in library code.
- `tests/unit/test_read_only_guarantee.py` — execution cannot be enabled.
- The `boundaries` CI job — domain imports with pytest alone and no runtime dependencies.

## Commands

```bash
make test                    # unit + integration + replay + golden
uv run pytest -m evals       # model evaluations, on demand
uv run pytest tests/unit     # fast loop
```
