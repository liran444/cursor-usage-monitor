# Platform notes

## Windows

- **Tray icon** shows total usage % (or error states `!` / `—`).
- **Notifications** may be suppressed by Focus Assist; the tray icon still updates.
- **Taskbar icon** uses the app ring icon (not `python.exe`) when running the installed tray build.
- **Browser import** reads cookies from installed Chromium/Firefox profiles for the current user.

## macOS

- **Menu bar tray** (`LSUIElement`); no Dock icon by default.
- **Unsigned pkg/app:** first launch may require **Right-click → Open** or allowing the app in **Privacy & Security**.
- **Browser import** may require **Full Disk Access** for the app (or Terminal during dev). See [AUTH.md](AUTH.md).
- Safari is not supported for automatic cookie import.

## Linux

- **Tray on Wayland** often needs AppIndicator / StatusNotifier support (GNOME may need `gnome-shell-extension-appindicator` or similar). The installer can offer to install suggested packages when you confirm.
- **`.run` installer:** browsers sometimes download without the execute bit. Use file properties → **Allow executing** or `chmod +x CursorUsageSetup-*.run`.
- **Keyring:** `libsecret` + `gnome-keyring` (or KDE Wallet) recommended; otherwise a file fallback is used under `~/.config/cursor-usage-app/`.

## Frozen vs development

| | Development | Installed |
|---|-------------|-----------|
| Windows | `cursor-usage tray` (Python / pip) | `cursor-usage.exe` (tray + widget only) |
| Linux | `cursor-usage tray` | `cursor-usage` on PATH |
| macOS | `cursor-usage tray` | **Cursor Usage.app** |

Released builds are GUI-only (tray and widget). Token and refresh are in the app UI. Developers can still use the `cursor-usage` CLI from a source install.

Config: `cursor-usage-app/settings.json` under the OS user config directory. Cache: `usage_cache.json` under user cache.
