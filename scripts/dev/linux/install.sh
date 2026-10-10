#!/usr/bin/env bash
# Developer setup: editable install in .venv (Linux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DEV_OS="linux"
DEV_PYTHON_HINT="Install python3 (3.10+), then re-run:"

cd "$ROOT"
# shellcheck source=../_common.sh
source "$SCRIPT_DIR/../_common.sh"

dev_check_python

if python3 -m venv .venv >/dev/null 2>&1; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
  dev_install_editable
  echo ""
  echo "Done. Dev environment installed."
  dev_enter_shell
  exit 0
fi

rm -rf .venv 2>/dev/null || true

echo "Note: python3-venv is not available. Installing for current user instead." >&2
echo "  For an isolated venv: sudo apt install python3-venv   # or python3.14-venv" >&2
echo "" >&2

if python3 -m pip install -U pip --break-system-packages 2>/dev/null; then
  python3 -m pip install -e ".[dev]" --break-system-packages
elif python3 -m pip install -U pip --user 2>/dev/null; then
  python3 -m pip install -e ".[dev]" --user
else
  python3 -m pip install -U pip
  python3 -m pip install -e ".[dev]"
fi

echo ""
echo "Done. Run: cursor-usage tray"
if ! command -v cursor-usage >/dev/null 2>&1; then
  echo "If cursor-usage is not on PATH, add ~/.local/bin to PATH or run: python3 -m cursor_usage tray" >&2
fi
echo "Verify: ./scripts/dev/linux/verify.sh"
