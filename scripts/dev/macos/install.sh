#!/usr/bin/env bash
# Developer setup: editable install in .venv (macOS)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DEV_OS="macos"
DEV_PYTHON_HINT='Install Python 3.10+ (e.g. brew install python@3.12), then re-run:'

cd "$ROOT"
# shellcheck source=../_common.sh
source "$SCRIPT_DIR/../_common.sh"

dev_check_python
dev_install_venv
