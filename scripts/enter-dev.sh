#!/usr/bin/env bash
# Activate the dev venv. Source to keep it in your current terminal:
#   source ./scripts/enter-dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTIVATE="${ROOT}/.venv/bin/activate"

if [[ ! -f "$ACTIVATE" ]]; then
  echo "No .venv found. Run the install script for your OS first." >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$ACTIVATE"
cd "$ROOT"

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  echo "Dev environment active in this shell."
  return 0 2>/dev/null || exit 0
fi

echo "Dev shell ready. Try: cursor-usage tray | pytest"
exec "${SHELL:-/bin/bash}" -i
