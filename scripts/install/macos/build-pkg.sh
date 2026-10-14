#!/usr/bin/env bash
# Build macOS .pkg from PyInstaller Cursor Usage.app
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VERSION="$(python3 "$REPO_ROOT/scripts/build/read_version.py")"
RELEASE="$REPO_ROOT/release"
MACOS_DIR="$(cd "$(dirname "$0")" && pwd)"

APP_NAME="Cursor Usage.app"
APP_SRC="$REPO_ROOT/dist/$APP_NAME"
if [[ ! -d "$APP_SRC" ]]; then
  APP_SRC="$REPO_ROOT/dist/cursor-usage/$APP_NAME"
fi
if [[ ! -d "$APP_SRC" ]]; then
  echo "Build the macOS app bundle first (scripts/build/build.sh on macOS)." >&2
  exit 1
fi

ARCH="$(uname -m)"
STAGING="$REPO_ROOT/build/macos-pkg-staging"
COMPONENT="$REPO_ROOT/build/component.pkg"
PRODUCT="$RELEASE/CursorUsage-${VERSION}-macos-${ARCH}.pkg"

rm -rf "$STAGING"
mkdir -p "$STAGING/Applications"
cp -R "$APP_SRC" "$STAGING/Applications/"

chmod +x "$MACOS_DIR/scripts/postinstall"

pkgbuild \
  --root "$STAGING" \
  --identifier "com.lirandekamhi.cursor-usage" \
  --version "$VERSION" \
  --install-location "/" \
  --scripts "$MACOS_DIR/scripts" \
  "$COMPONENT"

mkdir -p "$RELEASE"
productbuild \
  --distribution "$MACOS_DIR/Distribution.xml" \
  --package-path "$REPO_ROOT/build" \
  --resources "$MACOS_DIR" \
  "$PRODUCT"

echo "Created $PRODUCT"
