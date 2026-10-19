#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SHARE="${HOME}/.local/share/cursor-usage"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"

if [[ -n "${CURSOR_USAGE_VERSION:-}" ]]; then
  VERSION="$CURSOR_USAGE_VERSION"
elif [[ "$SCRIPT_DIR" == "${INSTALL_SHARE}/"* && "$SCRIPT_DIR" != "${INSTALL_SHARE}/current" ]]; then
  VERSION="$(basename "$SCRIPT_DIR")"
elif [[ -L "${INSTALL_SHARE}/current" ]]; then
  VERSION="$(basename "$(readlink "${INSTALL_SHARE}/current")")"
else
  echo "Could not determine installed version. Run this script from the install directory, or set CURSOR_USAGE_VERSION." >&2
  exit 1
fi

INSTALL_ROOT="${INSTALL_SHARE}/${VERSION}"

rm -f "$BIN_DIR/cursor-usage"
rm -f "$DESKTOP_DIR/cursor-usage.desktop"
rm -f "${HOME}/.local/share/icons/hicolor/256x256/apps/cursor-usage.png"
rm -rf "$INSTALL_ROOT"
rm -f "${INSTALL_SHARE}/current"
echo "Cursor Usage removed (system packages were not uninstalled)."
