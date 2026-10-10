# Cursor Usage Monitor

Cross-platform system tray app for Cursor **personal included usage** and **team pool** (dashboard `usage-summary` API). Unofficial; not affiliated with Cursor.

## Documentation

| | |
|---|---|
| **End users** | [User guide](README-USER.txt) · [Install](docs/INSTALL.md) · [Uninstall](docs/UNINSTALL.md) |
| **Developers** | [Development](docs/DEVELOPMENT.md) · [Build](docs/BUILD.md) |
| **Reference** | [Platform notes](docs/platforms.md) · [Auth](docs/AUTH.md) · [API fields](docs/usage-summary-fields.md) |

## Quick start

**Using a release (no Python needed):** download for your OS → [Install](docs/INSTALL.md) → set your session token → tray runs at login.

**Working on the repo:** run `.\scripts\dev\windows\install.ps1` (or Linux/macOS equivalent) → [Development setup](docs/DEVELOPMENT.md) → `cursor-usage tray` or `pytest`.

**Shipping a release:** [Build](docs/BUILD.md) on each target OS.
