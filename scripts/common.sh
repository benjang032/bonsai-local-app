#!/bin/sh

info() {
    printf '[OK] %s\n' "$*"
}

step() {
    printf '==> %s\n' "$*"
}

err() {
    printf '[ERR] %s\n' "$*" >&2
}

download() {
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf "$1" -o "$2"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$2" "$1"
    else
        err "Neither curl nor wget is installed."
        exit 1
    fi
}

ensure_venv() {
    demo_dir="$1"
    if [ -z "$VIRTUAL_ENV" ] && [ -f "$demo_dir/.venv/bin/activate" ]; then
        . "$demo_dir/.venv/bin/activate"
    fi
    if [ -z "$VIRTUAL_ENV" ]; then
        err "Python virtualenv not found. Run ./setup.sh first."
        exit 1
    fi
}
