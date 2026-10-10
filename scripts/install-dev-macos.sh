#!/usr/bin/env bash
# Developer setup: editable install in .venv (macOS)
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
pip install -e ".[dev]"

echo ""
echo "Done. Dev environment installed."
enter_dev_shell
