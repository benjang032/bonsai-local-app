from __future__ import annotations

import asyncio
import base64
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent

from .config import DEFAULT_MODEL_KEY, MODELS, OUTPUTS_DIR, resolve_model_key
from .runtime import BonsaiRuntime


mcp = FastMCP(
    "Bonsai Local Image Generator",
    instructions=(
        "Generate Bonsai Image 4B images locally on this Mac. "
        "Use generate_bonsai_image for image generation and list_bonsai_models "
        "to inspect available local model choices."
    ),
)

_runtimes: dict[str, BonsaiRuntime] = {}


def _runtime_for(model: str) -> BonsaiRuntime:
    key = resolve_model_key(model)
    if key not in _runtimes:
        _runtimes[key] = BonsaiRuntime(key)
    return _runtimes[key]


def _file_uri(path: str) -> str:
    return Path(path).resolve().as_uri()


def _metadata_text(result: dict[str, Any]) -> str:
    lines = [
        "Generated Bonsai image locally.",
        f"model: {result['model']}",
        f"prompt: {result['prompt']}",
        f"seed: {result['seed']}",
        f"size: {result['width']}x{result['height']}",
        f"steps: {result['steps']}",
        f"output_path: {result['output_path']}",
        f"file_uri: {result['file_uri']}",
        f"wall_seconds: {result['wall_seconds']}",
    ]
    return "\n".join(lines)


@mcp.tool()
def list_bonsai_models() -> dict[str, Any]:
    """List the Bonsai model variants this local MCP can generate with."""
    return {
        "default_model": DEFAULT_MODEL_KEY,
        "models": [
            {
                "key": key,
                "aliases": list(spec.aliases),
                "display_name": spec.display_name,
                "repo_id": spec.repo_id,
                "local_dir": str(spec.local_dir),
                "downloaded": (spec.local_dir / "transformer-packed-mflux").exists(),
            }
            for key, spec in MODELS.items()
        ],
    }


@mcp.tool()
def get_bonsai_status() -> dict[str, Any]:
    """Return local runtime status, output directory, and model availability."""
    return {
        "outputs_dir": str(OUTPUTS_DIR.resolve()),
        "loaded_models": sorted(_runtimes),
        "models": {
            key: {
                "downloaded": (spec.local_dir / "transformer-packed-mflux").exists(),
                "local_dir": str(spec.local_dir),
            }
            for key, spec in MODELS.items()
        },
    }


@mcp.tool()
async def generate_bonsai_image(
    prompt: str,
    model: str = DEFAULT_MODEL_KEY,
    width: int = 512,
    height: int = 512,
    steps: int = 4,
    seed: int | None = None,
    return_image: bool = True,
    ctx: Context | None = None,
) -> CallToolResult:
    """Generate a Bonsai Image 4B PNG locally and return its path plus image content.

    Dimensions must be multiples of 32 between 256 and 2048. Use 4 steps for
    normal generation; 2 steps is the minimum smoke-test setting. The image is
    always saved under outputs/<model>/ and can optionally be embedded in the
    MCP response with return_image=true.
    """
    if ctx is not None:
        await ctx.info(f"Generating Bonsai image with model={model}, size={width}x{height}, steps={steps}")

    runtime = _runtime_for(model)
    result = await asyncio.to_thread(
        partial(
            runtime.generate,
            prompt=prompt,
            width=width,
            height=height,
            steps=steps,
            seed=seed,
        )
    )
    payload = asdict(result)
    payload["file_uri"] = _file_uri(result.output_path)

    content: list[TextContent | ImageContent] = [
        TextContent(type="text", text=_metadata_text(payload))
    ]

    if return_image:
        image_bytes = Path(result.output_path).read_bytes()
        content.append(
            ImageContent(
                type="image",
                data=base64.b64encode(image_bytes).decode("ascii"),
                mimeType="image/png",
            )
        )

    return CallToolResult(content=content, structuredContent=payload)


@mcp.tool()
def read_bonsai_image(path: str) -> CallToolResult:
    """Return a previously generated local PNG as MCP image content."""
    resolved = Path(path).expanduser().resolve()
    output_root = OUTPUTS_DIR.resolve()
    try:
        resolved.relative_to(output_root)
    except ValueError as exc:
        raise ValueError(f"Image must be under {output_root}") from exc
    if resolved.suffix.lower() != ".png":
        raise ValueError("Only PNG outputs are supported")
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))

    image_bytes = resolved.read_bytes()
    return CallToolResult(
        content=[
            TextContent(type="text", text=f"Loaded Bonsai image: {resolved}\nfile_uri: {resolved.as_uri()}"),
            ImageContent(
                type="image",
                data=base64.b64encode(image_bytes).decode("ascii"),
                mimeType="image/png",
            ),
        ],
        structuredContent={
            "output_path": str(resolved),
            "file_uri": resolved.as_uri(),
            "bytes": len(image_bytes),
        },
    )


def main(transport: Literal["stdio", "streamable-http"] = "stdio") -> None:
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
