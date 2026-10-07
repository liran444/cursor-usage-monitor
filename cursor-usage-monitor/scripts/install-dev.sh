#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

install_editable() {
  pip install -U pip
  pip install -e ".[dev]"
}

if python3 -m venv .venv >/dev/null 2>&1; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
  install_editable
  echo "Installed in .venv. Run:"
  echo "  source ${ROOT}/.venv/bin/activate"
  echo "  cursor-usage tray"
  exit 0
fi

rm -rf .venv 2>/dev/null || true

echo "Note: python3-venv is not available (optional). Installing for current user instead." >&2
echo "  To use a venv later: sudo apt install python3-venv   # or python3.14-venv on your distro" >&2
echo "" >&2

if python3 -m pip install -U pip --break-system-packages 2>/dev/null; then
  python3 -m pip install -e ".[dev]" --break-system-packages
elif python3 -m pip install -U pip --user 2>/dev/null; then
  python3 -m pip install -e ".[dev]" --user
else
  python3 -m pip install -U pip
  python3 -m pip install -e ".[dev]"
fi

echo "Installed. Run: cursor-usage tray"
if ! command -v cursor-usage >/dev/null 2>&1; then
  echo "If cursor-usage is not on PATH, add ~/.local/bin to PATH or use: python3 -m cursor_usage tray" >&2
fi
