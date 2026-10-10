# Uninstall

## All platforms

```bash
cursor-usage token clear
```

Remove autostart (see OS below). Delete install directory if you copied a release bundle.

## Linux

Remove `~/.config/autostart/cursor-usage-tray.desktop`.

Optional: remove `~/.local/share/cursor-usage` and `~/.config/cursor-usage` (includes `session.token` if keyring fallback was used).

## macOS

```bash
launchctl unload ~/Library/LaunchAgents/com.cursor.usage.tray.plist
rm ~/Library/LaunchAgents/com.cursor.usage.tray.plist
```

## Windows

Remove shortcut from `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Cursor Usage Monitor.lnk`.

Remove `%LOCALAPPDATA%\CursorUsageMonitor` if present.

Optional: remove `%LOCALAPPDATA%\cursor-usage-monitor\cursor-usage\Config\session.token` if present.
