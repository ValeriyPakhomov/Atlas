#!/usr/bin/env bash
# Full local gate: lint, format check, typecheck, tests. Mirrors CI exactly.
set -euo pipefail
cd "$(dirname "$0")/.."

run() { echo "==> $*"; "$@"; }

run uv run ruff check .
run uv run ruff format --check .
run uv run mypy packages apps tests
run uv run pytest
