#!/usr/bin/env bash
# Developer setup: editable install in .venv (Linux)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

enter_dev_shell() {
  if [[ -t 1 ]] && [[ -z "${INSTALL_DEV_NO_SHELL:-}" ]]; then
    echo "Opening dev shell with venv active..."
    exec "${SHELL:-/bin/bash}" -c "source '${ROOT}/.venv/bin/activate'; cd '${ROOT}'; exec ${SHELL:-/bin/bash} -i"
  fi

  echo ""
  echo "Activate later with:"
  echo "  source ./scripts/enter-dev.sh"
  echo ""
  echo "Then run: cursor-usage tray"
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 not found. Install python3 (3.10+), then re-run:" >&2
  echo "  ./scripts/install-dev-linux.sh" >&2
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "Python 3.10+ required." >&2
  python3 --version >&2 || true
  exit 1
fi

echo "Using $(python3 --version)"

install_editable() {
  python -m pip install -U pip
  pip install -e ".[dev]"
}

if python3 -m venv .venv >/dev/null 2>&1; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
  install_editable
  echo ""
  echo "Done. Dev environment installed."
  enter_dev_shell
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
echo "Tests: pytest"
