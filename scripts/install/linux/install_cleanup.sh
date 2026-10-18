#!/usr/bin/env sh
# Makeself --cleanup hook: remove the extract directory left by --notemp builds.
# With default makeself settings (no --notemp), makeself removes $tmpdir itself;
# this script is a no-op when the directory is already gone.
set -eu

extract_dir="$(cd "$(dirname "$0")" && pwd)"
case "$(basename "$extract_dir")" in
  linux-installer-staging)
    ;;
  *)
    # Do not delete unknown directories.
    exit 0
    ;;
esac

if test ! -d "$extract_dir"; then
  exit 0
fi

# Leave the extract tree before removing it (cleanup runs from inside it).
cd "${USER_PWD:-/}" 2>/dev/null || cd /
rm -rf "$extract_dir"
