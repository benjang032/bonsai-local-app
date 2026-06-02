#!/bin/sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/scripts/common.sh"
ensure_venv "$ROOT"

model="${1:-binary}"
case "$model" in
    binary|binary-mlx|ternary|ternary-mlx) ;;
    -h|--help)
        echo "Usage: $0 [binary|ternary|binary-mlx|ternary-mlx]"
        exit 0
        ;;
    *)
        err "Unknown model: $model"
        echo "Usage: $0 [binary|ternary|binary-mlx|ternary-mlx]"
        exit 1
        ;;
esac

if [ "${BONSAI_DISABLE_XET_HIGH_PERFORMANCE:-0}" != "1" ]; then
    export HF_XET_HIGH_PERFORMANCE=1
fi

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" BONSAI_MODEL="$model" "$ROOT/.venv/bin/python" - <<'PY'
import os
from huggingface_hub import snapshot_download
from bonsai_demo.config import MODELS, resolve_model_key

key = resolve_model_key(os.environ["BONSAI_MODEL"])
spec = MODELS[key]
spec.local_dir.mkdir(parents=True, exist_ok=True)
print(f"Downloading {spec.repo_id}")
print(f"Target: {spec.local_dir}")
snapshot_download(
    repo_id=spec.repo_id,
    local_dir=str(spec.local_dir),
    max_workers=16,
)
print("Done")
PY
