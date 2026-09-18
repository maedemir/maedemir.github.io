#!/usr/bin/env bash
# Nightly ingest. Install with the crontab in deploy/crontab.example.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
python -m spatial_omics_litdb.cli ingest --preprint-days 3
