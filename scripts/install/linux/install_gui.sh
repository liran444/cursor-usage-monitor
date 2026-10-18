#!/usr/bin/env bash
# Graphical Linux installer entry (makeself .run).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD_DIR="$SCRIPT_DIR/payload"
# shellcheck source=install_core.sh
source "$SCRIPT_DIR/install_core.sh"

gui_question() {
  local title="$1"
  local text="$2"
  if command -v zenity >/dev/null 2>&1; then
    zenity --question --title="$title" --text="$text" --width=420
    return $?
  fi
  if command -v kdialog >/dev/null 2>&1; then
    kdialog --title "$title" --yesno "$text"
    return $?
  fi
  if command -v yad >/dev/null 2>&1; then
    yad --title "$title" --text "$text" --button=Yes:0 --button=No:1
    return $?
  fi
  read -r -p "$text [y/N] " ans
  [[ "$ans" =~ ^[Yy] ]]
}

gui_info() {
  local title="$1"
  local text="$2"
  if command -v zenity >/dev/null 2>&1; then
    zenity --info --title="$title" --text="$text" --width=420
    return 0
  fi
  echo "$text"
}

ensure_dialog_tool() {
  if command -v zenity >/dev/null 2>&1 || command -v kdialog >/dev/null 2>&1 || command -v yad >/dev/null 2>&1; then
    return 0
  fi
  if gui_question "Cursor Usage" "Install zenity for installer dialogs?"; then
    cursor_usage_install_prerequisites_for_meta zenity || true
  fi
}

cursor_usage_install_prerequisites_for_meta() {
  local pm
  pm="$(detect_pm)"
  case "$pm" in
    apt) sudo apt-get update -qq && sudo apt-get install -y zenity ;;
    dnf) sudo dnf install -y zenity ;;
    pacman) sudo pacman -S --noconfirm zenity ;;
    zypper) sudo zypper install -y zenity ;;
  esac
}

main() {
  ensure_dialog_tool || true

  if ! gui_question "Cursor Usage Setup" "Install Cursor Usage to your user account (~/.local)?"; then
    exit 0
  fi

  local pm
  pm="$(detect_pm)"
  if [[ "$pm" != unknown ]]; then
    mapfile -t missing < <(missing_packages_for_pm "$pm" || true)
    if ((${#missing[@]} > 0)); then
      local list
      list="$(printf '%s\n' "${missing[@]}")"
      if gui_question "System libraries" "Install missing libraries required for the tray and secure storage?\n\n$list"; then
        cursor_usage_install_prerequisites
      fi
    fi
  fi

  cursor_usage_install_app "$PAYLOAD_DIR"
  gui_info "Cursor Usage" "Installation complete. Start “Cursor Usage” from your applications menu or run: cursor-usage"

  if gui_question "Cursor Usage" "Launch Cursor Usage now?"; then
    cursor_usage_launch_installed_app
  fi
}

main "$@"
