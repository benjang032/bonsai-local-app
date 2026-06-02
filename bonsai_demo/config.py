from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
OUTPUTS_DIR = ROOT_DIR / "outputs"


@dataclass(frozen=True)
class ModelSpec:
    key: str
    aliases: tuple[str, ...]
    display_name: str
    repo_id: str
    backend_id: str
    local_dir_name: str

    @property
    def local_dir(self) -> Path:
        return MODELS_DIR / self.local_dir_name


MODELS: dict[str, ModelSpec] = {
    "binary-mlx": ModelSpec(
        key="binary-mlx",
        aliases=("binary",),
        display_name="Binary MLX 1-bit",
        repo_id="prism-ml/bonsai-image-binary-4B-mlx-1bit",
        backend_id="bonsai-binary-mlx",
        local_dir_name="bonsai-image-4B-binary-mlx",
    ),
    "ternary-mlx": ModelSpec(
        key="ternary-mlx",
        aliases=("ternary",),
        display_name="Ternary MLX 2-bit",
        repo_id="prism-ml/bonsai-image-ternary-4B-mlx-2bit",
        backend_id="bonsai-ternary-mlx",
        local_dir_name="bonsai-image-4B-ternary-mlx",
    ),
}

DEFAULT_MODEL_KEY = "binary-mlx"


def resolve_model_key(value: str | None) -> str:
    if not value:
        return DEFAULT_MODEL_KEY
    normalized = value.strip().lower()
    if normalized in MODELS:
        return normalized
    for key, spec in MODELS.items():
        if normalized in spec.aliases:
            return key
    choices = ", ".join(sorted(list(MODELS) + [a for spec in MODELS.values() for a in spec.aliases]))
    raise ValueError(f"Unknown model {value!r}. Expected one of: {choices}")


def model_choices() -> list[str]:
    return sorted(list(MODELS) + [alias for spec in MODELS.values() for alias in spec.aliases])


def parse_size(value: str) -> tuple[int, int]:
    normalized = value.lower().replace("x", "x")
    try:
        width_s, height_s = normalized.split("x", 1)
        width = int(width_s)
        height = int(height_s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--size must be WIDTHxHEIGHT, for example 512x512") from exc
    return validate_size(width, height)


def validate_size(width: int, height: int) -> tuple[int, int]:
    for label, dim in (("width", width), ("height", height)):
        if dim < 256 or dim > 2048:
            raise ValueError(f"{label} must be between 256 and 2048")
        if dim % 32 != 0:
            raise ValueError(f"{label} must be a multiple of 32")
    return width, height


def require_model_dir(model_key: str) -> Path:
    spec = MODELS[resolve_model_key(model_key)]
    model_dir = spec.local_dir
    transformer_dir = model_dir / "transformer-packed-mflux"
    if not transformer_dir.exists():
        raise FileNotFoundError(
            "Local model is not downloaded or is incomplete: "
            f"{model_dir}. Run: ./scripts/download_model.sh {spec.aliases[0]}"
        )
    return model_dir
