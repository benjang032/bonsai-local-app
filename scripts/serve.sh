#!/bin/sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/scripts/common.sh"
ensure_venv "$ROOT"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-7860}"

echo "Starting Bonsai Local Demo at http://$HOST:$PORT"
exec "$ROOT/.venv/bin/uvicorn" bonsai_demo.server:app --host "$HOST" --port "$PORT"
