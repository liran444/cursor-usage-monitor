# Install Cursor Usage Monitor

Download **one installer** for your operating system from the latest
**[GitHub Release](https://github.com/liran444/cursor-usage-monitor/releases)**.
Installers are free; you do not need to install Python or Qt.

| OS | Installer file | What to do |
|----|----------------|------------|
| **Windows** | `CursorUsageSetup-{version}-x64.exe` | Double-click, follow the wizard. Confirm if prompted to install the Microsoft Visual C++ runtime. |
| **macOS** | `CursorUsage-{version}-macos-{arch}.pkg` | Double-click, follow **Installer.app**. If macOS blocks the app, right-click the app in Applications → **Open** once. |
| **Linux** | `CursorUsageSetup-{version}-linux-x86_64.run` | Mark as executable if needed, then double-click or run `./CursorUsageSetup-....run`. Confirm when asked to install system libraries. |

Tagged pushes (`v*`) build installers in CI and publish them on GitHub Releases.
You can also download artifacts from the **Release build** workflow run (see [DEVELOPMENT.md](DEVELOPMENT.md)).

Legal docs: [PRIVACY.md](PRIVACY.md), [DISCLAIMER.md](DISCLAIMER.md), [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), and [LICENSE](../LICENSE). Windows installs include these files in the app folder; Linux `.run` bundles them in the installer archive; macOS users can read them on the GitHub Release or in the repository.

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
