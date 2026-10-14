# Install Cursor Usage Monitor

Download **one installer** for your operating system. You do not need to install Python or Qt.

| OS | Installer file | What to do |
|----|----------------|------------|
| **Windows** | `CursorUsageSetup-{version}-x64.exe` | Double-click, follow the wizard. Confirm if prompted to install the Microsoft Visual C++ runtime. |
| **macOS** | `CursorUsage-{version}-macos-{arch}.pkg` | Double-click, follow **Installer.app**. If macOS blocks the app, right-click the app in Applications → **Open** once. |
| **Linux** | `CursorUsageSetup-{version}-linux-x86_64.run` | Mark as executable if needed, then double-click or run `./CursorUsageSetup-....run`. Confirm when asked to install system libraries. |

Installers are built from tagged releases or CI artifacts (see [DEVELOPMENT.md](DEVELOPMENT.md)).

## After install

- **Windows:** Start Menu → **Cursor Usage** (`cursor-usage.exe` in `Program Files\Cursor Usage\`).
- **macOS:** Applications → **Cursor Usage** (menu bar tray).
- **Linux:** Applications menu → **Cursor Usage**, or `cursor-usage` on PATH (`~/.local/bin`).

## Authentication

See [AUTH.md](AUTH.md) for session token import and manual setup.

## Uninstall

See [UNINSTALL.md](UNINSTALL.md).

## Platform notes

See [platforms.md](platforms.md) for tray behavior, notifications, Wayland, and permissions.
