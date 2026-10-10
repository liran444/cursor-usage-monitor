#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
APP="${1:-$ROOT/packaging/pyinstaller/dist/Cursor Usage Monitor.app}"
PLIST="${HOME}/Library/LaunchAgents/com.cursor.usage.tray.plist"
if [[ ! -d "$APP" ]]; then
  echo "App not found: $APP" >&2
  exit 1
fi
DEST="${HOME}/Applications/Cursor Usage Monitor.app"
mkdir -p "${HOME}/Applications"
rm -rf "$DEST"
cp -a "$APP" "$DEST"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.cursor.usage.tray</string>
  <key>ProgramArguments</key>
  <array>
    <string>${DEST}/Contents/MacOS/cursor-usage</string>
    <string>tray</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Installed LaunchAgent for tray."
