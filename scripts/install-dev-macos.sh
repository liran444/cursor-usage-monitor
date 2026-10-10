#!/usr/bin/env bash
# Developer setup: editable install in .venv (macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 not found. Install Python 3.10+ (e.g. brew install python@3.12), then re-run:" >&2
  echo "  ./scripts/install-dev-macos.sh" >&2
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "Python 3.10+ required." >&2
  python3 --version >&2 || true
  exit 1
fi

echo "Using $(python3 --version)"
echo "Creating .venv in $ROOT"

python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"

echo ""
echo "Done. Activate and run:"
echo "  source ${ROOT}/.venv/bin/activate"
echo "  cursor-usage tray"
echo ""
echo "Tests: pytest"
