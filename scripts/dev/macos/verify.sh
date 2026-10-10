#!/usr/bin/env bash
# Post-install smoke checks for macOS dev environment.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

fail() {
  echo "FAIL  $1" >&2
  exit 1
}

[[ -x "${ROOT}/.venv/bin/python" ]] || fail "Missing .venv. Run ./scripts/dev/macos/install.sh first."

version="$("${ROOT}/.venv/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python3 -c "import sys; v='${version}'.split('.'); sys.exit(0 if (int(v[0]), int(v[1])) >= (3, 10) else 1)" \
  || fail "Python 3.10+ required in .venv (found ${version})."
echo "OK  Python ${version} in .venv"

"${ROOT}/.venv/bin/cursor-usage" --help >/dev/null || fail "cursor-usage --help"
echo "OK  cursor-usage --help"

"${ROOT}/.venv/bin/python" -m pytest || fail "pytest"
echo "OK  pytest"

echo ""
echo "All checks passed."
