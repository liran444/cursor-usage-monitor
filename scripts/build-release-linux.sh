#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m PyInstaller --noconfirm packaging/pyinstaller/cursor_usage_linux.spec
(
  cd dist
  sha256sum CursorUsageMonitor/cursor-usage > SHA256SUMS.txt 2>/dev/null || true
)
echo "Built dist/CursorUsageMonitor — see docs/BUILD.md for Win/macOS builds on those hosts."
