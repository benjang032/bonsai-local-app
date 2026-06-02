from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import MODELS, OUTPUTS_DIR, require_model_dir, resolve_model_key, validate_size


@dataclass(frozen=True)
class GenerationResult:
    model: str
    prompt: str
    seed: int
    width: int
    height: int
    steps: int
    setup_seconds: float
    generation_seconds: float
    wall_seconds: float
    output_path: str
    output_url: str
    metadata_path: str


class BonsaiRuntime:
    def __init__(self, model_key: str):
        self.model_key = resolve_model_key(model_key)
        self.spec = MODELS[self.model_key]
        self._pipeline = None
        self._lock = threading.Lock()

    def _load_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline, 0.0

        model_dir = require_model_dir(self.model_key)
        if os.getenv("BONSAI_ALLOW_NETWORK") != "1":
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
        started = time.perf_counter()
        from backend.pipeline import FluxPipeline, PipelineConfig

        self._pipeline = FluxPipeline(
            PipelineConfig(
                backend=self.spec.backend_id,
                baked_model_path=str(model_dir),
                baked_binary_model_path=str(model_dir),
                te_4bit=True,
                evict_text_encoder=True,
            )
        )
        return self._pipeline, time.perf_counter() - started

    def generate(
        self,
        *,
        prompt: str,
        width: int = 512,
        height: int = 512,
        steps: int = 4,
        seed: int | None = None,
        output: Path | None = None,
        open_image: bool = False,
    ) -> GenerationResult:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        width, height = validate_size(width, height)
        if steps < 2 or steps > 12:
            raise ValueError("Steps must be between 2 and 12. Bonsai is tuned for 4.")
        if seed is None:
            seed = secrets.randbits(31)

        wall_started = time.perf_counter()
        with self._lock:
            pipeline, setup_seconds = self._load_pipeline()
            generation_started = time.perf_counter()
            png_bytes = pipeline.generate_png(
                prompt=prompt,
                seed=seed,
                steps=steps,
                width=width,
                height=height,
            )
            generation_seconds = time.perf_counter() - generation_started

        if output is None:
            output = default_output_path(self.model_key, seed)
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(png_bytes)

        wall_seconds = time.perf_counter() - wall_started
        result = GenerationResult(
            model=self.model_key,
            prompt=prompt,
            seed=seed,
            width=width,
            height=height,
            steps=steps,
            setup_seconds=round(setup_seconds, 3),
            generation_seconds=round(generation_seconds, 3),
            wall_seconds=round(wall_seconds, 3),
            output_path=str(output),
            output_url=output_url(output),
            metadata_path="",
        )
        metadata_path = append_metadata(result)
        result = GenerationResult(**{**asdict(result), "metadata_path": str(metadata_path)})

        if open_image and sys.platform == "darwin":
            subprocess.run(["open", str(output)], check=False)

        return result


def default_output_path(model_key: str, seed: int) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUTS_DIR / model_key / f"image_{stamp}_seed{seed}.png"


def output_url(output: Path) -> str:
    try:
        relative = output.resolve().relative_to(OUTPUTS_DIR.resolve())
    except ValueError:
        return ""
    return "/outputs/" + str(relative).replace("\\", "/")


def append_metadata(result: GenerationResult) -> Path:
    meta_dir = OUTPUTS_DIR / result.model
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / "generations.json"
    record = asdict(result)
    record["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record.pop("metadata_path", None)

    if meta_path.exists():
        try:
            records = json.loads(meta_path.read_text())
            if not isinstance(records, list):
                records = []
        except json.JSONDecodeError:
            records = []
    else:
        records = []
    records.append(record)
    meta_path.write_text(json.dumps(records, indent=2) + "\n")
    return meta_path
