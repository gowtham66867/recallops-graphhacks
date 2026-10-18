#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null; then
  echo 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ first.' >&2
  exit 1
fi
uv venv --python 3.12 --allow-existing .venv
uv pip sync requirements.lock.txt
npm ci --prefix frontend
npm run build --prefix frontend
docker compose up -d --wait
echo 'RecallOps is opening at http://127.0.0.1:8000'
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
