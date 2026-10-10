# Shared dev-install helpers for Linux and macOS.
# Sourced by scripts/dev/linux/install.sh and scripts/dev/macos/install.sh.

dev_print_activate_hint() {
  echo ""
  echo "Activate with:"
  echo "  source ${ROOT}/scripts/dev/${DEV_OS}/activate.sh"
  echo ""
  echo "Then run: cursor-usage tray"
  echo "Verify:   ./scripts/dev/${DEV_OS}/verify.sh"
}

dev_enter_shell() {
  if [[ -t 1 ]] && [[ -z "${INSTALL_DEV_NO_SHELL:-}" ]]; then
    echo "Opening dev shell with venv active..."
    exec "${SHELL:-/bin/bash}" -c "source '${ROOT}/.venv/bin/activate'; cd '${ROOT}'; exec ${SHELL:-/bin/bash} -i"
  fi
  dev_print_activate_hint
}

dev_check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 not found. ${DEV_PYTHON_HINT}" >&2
    echo "  ./scripts/dev/${DEV_OS}/install.sh" >&2
    exit 1
  fi

  if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    echo "Python 3.10+ required." >&2
    python3 --version >&2 || true
    exit 1
  fi

  echo "Using $(python3 --version)"
}

dev_install_editable() {
  python -m pip install -U pip
  pip install -e ".[dev]"
}

dev_install_venv() {
  echo "Creating .venv in $ROOT"
  python3 -m venv .venv
  # shellcheck source=/dev/null
  source .venv/bin/activate
  dev_install_editable
  echo ""
  echo "Done. Dev environment installed."
  dev_enter_shell
}
