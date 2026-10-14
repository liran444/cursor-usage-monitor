# Uninstall

## Windows

1. **Settings → Apps → Installed apps** (or Control Panel → Programs).
2. Select **Cursor Usage** → Uninstall.

This removes the program folder under `Program Files\Cursor Usage\`. Your settings and cache remain under `%APPDATA%` and `%LOCALAPPDATA%` (platformdirs paths for `cursor-usage-app`). Use **Set token → Clear** in the app before uninstall if you want to remove the stored session.

## macOS

1. Quit Cursor Usage from the tray menu.
2. Delete **Cursor Usage** from `/Applications`.
3. Optional: `pkgutil --forget com.lirandekamhi.cursor-usage` if you used the `.pkg` installer.

Config and cache live in `~/Library/Application Support/cursor-usage-app/` and `~/Library/Caches/cursor-usage-app/`.

## Linux

Run the uninstall script from the installed version:

```bash
~/.local/share/cursor-usage/current/uninstall.sh
```

Or remove `~/.local/share/cursor-usage/`, `~/.local/bin/cursor-usage`, and `~/.local/share/applications/cursor-usage.desktop` manually.

System packages installed during setup (e.g. `zenity`, tray libraries) are **not** removed automatically.
