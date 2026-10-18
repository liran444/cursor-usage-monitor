#!/usr/bin/env bash
# Core install logic (payload copy + optional system packages).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_DIR="$SCRIPT_DIR/packages"
VERSION="${CURSOR_USAGE_VERSION:-0.1.0}"
INSTALL_ROOT="${HOME}/.local/share/cursor-usage/${VERSION}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
APP_ID="cursor-usage.desktop"
DRY_RUN="${CURSOR_USAGE_INSTALL_DRY_RUN:-0}"

detect_pm() {
  if command -v apt-get >/dev/null 2>&1; then
    echo apt
  elif command -v dnf >/dev/null 2>&1; then
    echo dnf
  elif command -v pacman >/dev/null 2>&1; then
    echo pacman
  elif command -v zypper >/dev/null 2>&1; then
    echo zypper
  else
    echo unknown
  fi
}

missing_packages_for_pm() {
  local pm="$1"
  local list_file="$PACKAGES_DIR/${pm}.txt"
  local missing=()
  if [[ ! -f "$list_file" ]]; then
    return 0
  fi
  while IFS= read -r pkg || [[ -n "$pkg" ]]; do
    [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
    case "$pm" in
      apt)
        dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
        ;;
      dnf | zypper)
        rpm -q "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
        ;;
      pacman)
        pacman -Qi "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
        ;;
    esac
  done < "$list_file"
  if ((${#missing[@]} > 0)); then
    printf '%s\n' "${missing[@]}"
  fi
}

cursor_usage_install_prerequisites() {
  local pm
  pm="$(detect_pm)"
  if [[ "$pm" == unknown ]]; then
    echo "No supported package manager found." >&2
    return 1
  fi
  mapfile -t missing < <(missing_packages_for_pm "$pm" || true)
  if ((${#missing[@]} == 0)); then
    return 0
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] prerequisites: ${missing[*]}"
    return 0
  fi
  case "$pm" in
    apt)
      sudo apt-get update -qq
      sudo apt-get install -y "${missing[@]}"
      ;;
    dnf)
      sudo dnf install -y "${missing[@]}"
      ;;
    pacman)
      sudo pacman -S --noconfirm "${missing[@]}"
      ;;
    zypper)
      sudo zypper install -y "${missing[@]}"
      ;;
  esac
}

cursor_usage_install_app() {
  local payload_dir="$1"
  if [[ ! -d "$payload_dir" ]]; then
    echo "Payload not found: $payload_dir" >&2
    return 1
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] would install app from $payload_dir to $INSTALL_ROOT"
    return 0
  fi
  mkdir -p "$INSTALL_ROOT" "$BIN_DIR" "$DESKTOP_DIR"
  rm -rf "${INSTALL_ROOT:?}/"*
  cp -a "$payload_dir/." "$INSTALL_ROOT/"

  ln -sf "${INSTALL_ROOT}/cursor-usage" "$BIN_DIR/cursor-usage"

  cp "$SCRIPT_DIR/uninstall.sh" "$INSTALL_ROOT/uninstall.sh"
  chmod +x "$INSTALL_ROOT/uninstall.sh"

  icon_name="preferences-system"
  if [[ -f "${INSTALL_ROOT}/assets/app-icon.png" ]]; then
    icon_name="${INSTALL_ROOT}/assets/app-icon.png"
  fi

  cat > "$DESKTOP_DIR/$APP_ID" <<EOF
[Desktop Entry]
Type=Application
Name=Cursor Usage
Comment=Cursor usage monitor tray
Exec=${INSTALL_ROOT}/cursor-usage
Icon=${icon_name}
Terminal=false
Categories=Utility;
StartupNotify=false
EOF

  ln -sfn "$INSTALL_ROOT" "${HOME}/.local/share/cursor-usage/current"
  echo "Installed to $INSTALL_ROOT"
}

cursor_usage_launch_installed_app() {
  local app="${HOME}/.local/share/cursor-usage/current/cursor-usage"
  if [[ ! -x "$app" ]]; then
    echo "Could not find installed app: $app" >&2
    return 1
  fi
  # Detach from the installing shell so the terminal stays usable (no Qt/GIO stderr spam).
  if command -v setsid >/dev/null 2>&1; then
    setsid -f -- "$app" </dev/null >/dev/null 2>&1 &
  else
    nohup "$app" </dev/null >/dev/null 2>&1 &
    disown -h >/dev/null 2>&1 || disown >/dev/null 2>&1 || true
  fi
}
