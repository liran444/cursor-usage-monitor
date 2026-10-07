#!/usr/bin/env bash
# Install from PyInstaller one-folder bundle in dist/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="${1:-$ROOT/dist/CursorUsageMonitor}"
if [[ ! -d "$BUNDLE" ]]; then
  echo "Bundle not found: $BUNDLE" >&2
  echo "Build first — see README.md (Developer — build)" >&2
  exit 1
fi
INSTALL_DIR="${HOME}/.local/opt/cursor-usage-monitor"
mkdir -p "$INSTALL_DIR"
cp -a "$BUNDLE/"* "$INSTALL_DIR/"
BIN="${HOME}/.local/bin/cursor-usage"
mkdir -p "${HOME}/.local/bin"
ln -sf "$INSTALL_DIR/cursor-usage" "$BIN"
AUTOSTART="${HOME}/.config/autostart"
mkdir -p "$AUTOSTART"
cat > "$AUTOSTART/cursor-usage-tray.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Cursor Usage Monitor
Exec=${BIN} tray
X-GNOME-Autostart-enabled=true
EOF
echo "Installed to $INSTALL_DIR and autostart desktop entry."
