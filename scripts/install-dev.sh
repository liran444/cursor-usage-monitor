#!/usr/bin/env bash
# Developer setup dispatcher (Linux / macOS). On Windows use scripts/Install-Dev.ps1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$(uname -s)" in
  Linux)
    exec "${SCRIPT_DIR}/install-dev-linux.sh" "$@"
    ;;
  Darwin)
    exec "${SCRIPT_DIR}/install-dev-macos.sh" "$@"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "On Windows, run from PowerShell:" >&2
    echo "  .\\scripts\\Install-Dev.ps1" >&2
    exit 1
    ;;
  *)
    echo "Unsupported OS. Use the script for your platform:" >&2
    echo "  Linux:   ./scripts/install-dev-linux.sh" >&2
    echo "  macOS:   ./scripts/install-dev-macos.sh" >&2
    echo "  Windows: .\\scripts\\Install-Dev.ps1" >&2
    exit 1
    ;;
esac
