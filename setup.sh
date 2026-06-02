#!/bin/sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
. "$ROOT/scripts/common.sh"

VENV_DIR="$ROOT/.venv"
VENV_PY="$VENV_DIR/bin/python"

echo ""
echo "Bonsai Local Demo setup"
echo ""

OS="$(uname -s)"
ARCH="$(uname -m)"
step "Checking platform: $OS $ARCH"
if [ "$OS" != "Darwin" ] || [ "$ARCH" != "arm64" ]; then
    err "This demo currently targets Apple Silicon Macs through MLX."
    exit 1
fi

step "Checking Xcode and Metal toolchain"
if ! xcode-select -p >/dev/null 2>&1; then
    err "Xcode Command Line Tools are not installed. Run: xcode-select --install"
    exit 1
fi
if ! xcrun metal --version >/dev/null 2>&1; then
    err "The Metal compiler is not available. Install full Xcode and the Metal Toolchain, then rerun setup."
    exit 1
fi
info "Metal toolchain available"

step "Checking uv"
if ! command -v uv >/dev/null 2>&1; then
    tmp="$(mktemp)"
    download "https://astral.sh/uv/install.sh" "$tmp"
    sh "$tmp" </dev/null
    rm -f "$tmp"
    [ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v uv >/dev/null 2>&1; then
    err "uv is not available. Install it from https://docs.astral.sh/uv/ and rerun setup."
    exit 1
fi
info "$(uv --version)"

step "Creating Python virtualenv"
if [ ! -x "$VENV_PY" ]; then
    uv venv "$VENV_DIR" --python 3.11
fi
info "Virtualenv ready at $VENV_DIR"

VENDOR_DIR="$ROOT/vendor"
mkdir -p "$VENDOR_DIR"

clone_vendor() {
    name="$1"
    url="$2"
    target="$VENDOR_DIR/$name"
    if [ -d "$target/.git" ]; then
        info "vendor/$name already present"
    else
        step "Cloning vendor/$name"
        git clone "$url" "$target"
    fi
}

clone_vendor image-studio https://github.com/PrismML-Eng/image-studio.git
clone_vendor mflux-prism https://github.com/PrismML-Eng/mflux-prism.git

studio_pyproject="$VENDOR_DIR/image-studio/pyproject.toml"
if [ -f "$studio_pyproject" ] && grep -q '^mflux = { git = ' "$studio_pyproject"; then
    step "Patching image-studio to use local mflux-prism"
    sed -i.bak 's|^mflux = { git = .*$|mflux = { path = "../mflux-prism", editable = true }|' "$studio_pyproject"
    rm -f "$studio_pyproject.bak"
fi

step "Installing Python dependencies"
uv sync

chmod +x "$ROOT"/scripts/*.sh

echo ""
info "Setup complete"
echo ""
echo "Next:"
echo "  ./scripts/download_model.sh binary"
echo "  ./scripts/generate.sh --prompt \"A bonsai tree in a quiet ceramic studio\" --size 512x512 --open"
echo "  ./scripts/serve.sh"
