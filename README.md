# Bonsai Local MCP

Local Bonsai Image 4B generator for Apple Silicon Macs, exposed as an MCP server that agents can call. The iOS app and Swift/Xcode project have been removed.

The default model is `prism-ml/bonsai-image-binary-4B-mlx-1bit`, matching the old app's smaller binary path. The quality-oriented ternary model is also supported.

## Example Output

Generated locally through the MCP tool:

![Realistic puppy generated locally with Bonsai MCP](docs/assets/puppy-realistic.png)

## Setup

```sh
./setup.sh
./scripts/download_model.sh binary
```

Setup creates `.venv/`, clones the local MLX runtime dependencies into `vendor/`, and installs the Python package. Model files are downloaded into `models/`.

## Run As MCP

Stdio is the default path for local agents because the client owns the process lifecycle:

```sh
./scripts/mcp.sh
```

Tools exposed:

- `list_bonsai_models`: lists supported local Bonsai model variants.
- `get_bonsai_status`: reports local output and model availability.
- `generate_bonsai_image`: generates a PNG locally, saves it under `outputs/<model>/`, and returns metadata plus optional MCP image content.
- `read_bonsai_image`: returns a previously generated local PNG as MCP image content.

Codex config example:

```toml
[mcp_servers.bonsai_local]
command = "/Users/benjang/Documents/Code/bonsai-model/scripts/mcp.sh"
args = []
startup_timeout_sec = 120
```

Generic MCP client config:

```json
{
  "mcpServers": {
    "bonsai-local": {
      "command": "/Users/benjang/Documents/Code/bonsai-model/scripts/mcp.sh",
      "args": []
    }
  }
}
```

For clients that support streamable HTTP and can reach this machine:

```sh
HOST=127.0.0.1 PORT=8765 ./scripts/mcp_http.sh
```

The HTTP MCP endpoint is `http://127.0.0.1:8765/mcp`.

## Generate From The CLI

```sh
./scripts/generate.sh \
  --prompt "A bonsai tree in a quiet ceramic studio, soft morning light" \
  --size 512x512 \
  --seed 42 \
  --open
```

Outputs are written to `outputs/<model>/`.

## Optional Browser Demo

```sh
./scripts/serve.sh
```

Open `http://127.0.0.1:7860`. The server keeps the loaded pipeline warm between generations.

## Models

```sh
./scripts/download_model.sh binary
./scripts/download_model.sh ternary
```

Supported keys:

- `binary`, `binary-mlx`: `prism-ml/bonsai-image-binary-4B-mlx-1bit`
- `ternary`, `ternary-mlx`: `prism-ml/bonsai-image-ternary-4B-mlx-2bit`

Recommended generation settings are 4 steps, guidance-free prompting, and image dimensions that are multiples of 32. The minimum supported step count is 2. Start with `512x512` for quick previews.

## Requirements

- Apple Silicon Mac.
- Python 3.11 or newer. `setup.sh` uses `uv` and will create a Python 3.11 virtualenv.
- Xcode with the Metal toolchain available through `xcrun metal`.

The first generation loads several GB of local weights and may compile MLX kernels. Later generations at the same shape are faster.

Generation defaults to `HF_HUB_OFFLINE=1` after model download, so calls run from local files. Set `BONSAI_ALLOW_NETWORK=1` if you intentionally want upstream network checks.
