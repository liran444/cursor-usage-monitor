#!/usr/bin/env bash
# Build makeself .run installer from dist/cursor-usage/
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VERSION="$(python3 "$REPO_ROOT/scripts/build/read_version.py")"
STAGING="$REPO_ROOT/build/linux-installer-staging"
RELEASE="$REPO_ROOT/release"
DIST="$REPO_ROOT/dist/cursor-usage"

if [[ ! -d "$DIST" ]]; then
  echo "Run scripts/build/build.sh first." >&2
  exit 1
fi

if ! command -v makeself >/dev/null 2>&1; then
  echo "makeself not found. Install makeself package." >&2
  exit 1
fi

rm -rf "$STAGING"
mkdir -p "$STAGING/payload"
cp -a "$DIST/." "$STAGING/payload/"
cp "$REPO_ROOT/scripts/install/linux/install_gui.sh" "$STAGING/"
cp "$REPO_ROOT/scripts/install/linux/install_core.sh" "$STAGING/"
cp "$REPO_ROOT/scripts/install/linux/uninstall.sh" "$STAGING/"
cp "$REPO_ROOT/scripts/install/linux/install_cleanup.sh" "$STAGING/"
cp -a "$REPO_ROOT/scripts/install/linux/packages" "$STAGING/"
cp "$REPO_ROOT/README-USER.txt" "$STAGING/" 2>/dev/null || true
chmod +x "$STAGING/install_cleanup.sh"

mkdir -p "$RELEASE"
OUT="$RELEASE/CursorUsageSetup-${VERSION}-linux-x86_64.run"

# Do not use --notemp: it leaves linux-installer-staging in the user's cwd (e.g. Downloads).
makeself --nox11 --cleanup ./install_cleanup.sh "$STAGING" "$OUT" "Cursor Usage Setup" ./install_gui.sh
chmod +x "$OUT"
echo "Created $OUT"
