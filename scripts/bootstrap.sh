#!/usr/bin/env bash
# Create the local Atlas dev environment. Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

# uv sync creates .venv and installs from uv.lock, matching CI exactly.
uv sync --extra dev

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "created .env from .env.example"
fi

echo "bootstrap complete — run: make check"
