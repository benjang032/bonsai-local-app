from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bonsai_demo.config import DEFAULT_MODEL_KEY, model_choices, parse_size, resolve_model_key
from bonsai_demo.runtime import BonsaiRuntime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one image locally with Bonsai Image 4B.")
    parser.add_argument("-p", "--prompt", required=True, help="Text prompt.")
    parser.add_argument(
        "-m",
        "--model",
        choices=model_choices(),
        default=DEFAULT_MODEL_KEY,
        help=f"Model to use. Default: {DEFAULT_MODEL_KEY}.",
    )
    parser.add_argument("--size", type=parse_size, default=(512, 512), help="Image size, for example 512x512.")
    parser.add_argument("--steps", type=int, default=4, help="Inference steps, 2-12. Bonsai is tuned for 4.")
    parser.add_argument("--seed", type=int, default=None, help="Integer seed. Random if omitted.")
    parser.add_argument("--output", type=Path, default=None, help="Output PNG path.")
    parser.add_argument("--open", action="store_true", help="Open the image after saving on macOS.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    width, height = args.size
    model_key = resolve_model_key(args.model)
    result = BonsaiRuntime(model_key).generate(
        prompt=args.prompt,
        width=width,
        height=height,
        steps=args.steps,
        seed=args.seed,
        output=args.output,
        open_image=args.open,
    )

    print("")
    print(f"model:      {result.model}")
    print(f"prompt:     {result.prompt}")
    print(f"seed:       {result.seed}")
    print(f"size:       {result.width}x{result.height}")
    print(f"setup:      {result.setup_seconds:.2f}s")
    print(f"generation: {result.generation_seconds:.2f}s")
    print(f"wall:       {result.wall_seconds:.2f}s")
    print(f"output:     {result.output_path}")
    print(f"metadata:   {result.metadata_path}")


if __name__ == "__main__":
    main()
