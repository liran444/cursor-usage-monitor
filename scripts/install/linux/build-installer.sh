#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
"$REPO_ROOT/scripts/build/build.sh"
"$REPO_ROOT/scripts/install/linux/make-installer.sh"
