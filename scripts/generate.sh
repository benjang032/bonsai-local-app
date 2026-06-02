#!/bin/sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/scripts/common.sh"
ensure_venv "$ROOT"

exec "$ROOT/.venv/bin/python" "$ROOT/scripts/generate.py" "$@"
