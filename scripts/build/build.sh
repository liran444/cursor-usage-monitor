#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m pip install -e ".[build]" -q
"$PYTHON" -m PyInstaller --noconfirm --clean "$(dirname "$0")/cursor-usage.spec"
echo "Build output: $REPO_ROOT/dist/cursor-usage"
