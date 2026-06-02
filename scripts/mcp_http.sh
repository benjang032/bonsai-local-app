#!/bin/sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/scripts/common.sh"
ensure_venv "$ROOT"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"

export HOST PORT
exec "$ROOT/.venv/bin/python" - <<'PY'
import os

from bonsai_demo.mcp_server import mcp

host = os.environ["HOST"]
port = int(os.environ["PORT"])
mcp.settings.host = host
mcp.settings.port = port
mcp.run(transport="streamable-http")
PY
