#!/usr/bin/env bash
set -euo pipefail

VERSION="${CURSOR_USAGE_VERSION:-}"
if [[ -z "$VERSION" && -L "${HOME}/.local/share/cursor-usage/current" ]]; then
  VERSION="$(basename "$(readlink "${HOME}/.local/share/cursor-usage/current")")"
fi
if [[ -z "$VERSION" ]]; then
  VERSION="0.1.0"
fi

INSTALL_ROOT="${HOME}/.local/share/cursor-usage/${VERSION}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"

rm -f "$BIN_DIR/cursor-usage" "$BIN_DIR/cursor-usage-cli"
rm -f "$DESKTOP_DIR/cursor-usage.desktop"
rm -rf "$INSTALL_ROOT"
rm -f "${HOME}/.local/share/cursor-usage/current"
echo "Cursor Usage removed (system packages were not uninstalled)."
