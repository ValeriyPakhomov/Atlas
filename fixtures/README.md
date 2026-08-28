# Fixtures

Deterministic inputs for replay, golden and eval suites.

- **Synthetic personal state only.** Never real balances, account numbers, addresses or
  any PII (`docs/SECURITY.md`).
- Fixtures are point-in-time: each carries its own `as_of` and must never contain data
  published after it. Point-in-time leakage is the failure the replay suite exists to
  catch.
- Golden research fixtures (Queue 03/05) hold 20–50 known historical event clusters with
  expected event and narrative assignments, including duplicate reporting that must
  merge into a single event.
- Impact fixtures (Queue 09) cover BTC shock, TRY shock, rate shock, AI capability jump
  and migration rule change, each with known owner exposure.
