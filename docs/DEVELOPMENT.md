# Development

**Requirements:** Python 3.10+, and a graphical session for tray testing (Linux/macOS/Windows).

Script index: [scripts/README.md](../scripts/README.md).

## Setup

From the repo root, run the install script for your OS:

| OS | Command |
|----|---------|
| **Windows** | `.\scripts\dev\windows\install.ps1` |
| **Linux** | `./scripts/dev/linux/install.sh` |
| **macOS** | `./scripts/dev/macos/install.sh` |

Each script creates a `.venv` and runs `pip install -e ".[dev]"`.

On Windows, if Python is missing, the script offers to install it via winget. If `python` opens the Microsoft Store, disable **App execution aliases** for `python.exe` and `python3.exe` (Settings → Apps → Advanced app settings).

**Skip interactive shell** (Linux/macOS only):

```bash
INSTALL_DEV_NO_SHELL=1 ./scripts/dev/linux/install.sh
```

**Re-activate later:**

| OS | Command |
|----|---------|
| **Windows** | `. .\scripts\dev\windows\activate.ps1` |
| **Linux** | `source ./scripts/dev/linux/activate.sh` |
| **macOS** | `source ./scripts/dev/macos/activate.sh` |

**Verify install:**

| OS | Command |
|----|---------|
| **Windows** | `.\scripts\dev\windows\verify.ps1` |
| **Linux** | `./scripts/dev/linux/verify.sh` |
| **macOS** | `./scripts/dev/macos/verify.sh` |

On Linux, if `python3-venv` is missing, the install falls back to a user install (`~/.local/bin`). For an isolated venv: `sudo apt install python3-venv` (or `python3.14-venv`), then re-run.

Platform notes: [platforms.md](platforms.md).

## Commands

| Command | Purpose |
|---------|---------|
| `cursor-usage token set` | Save session cookie to OS keyring |
| `cursor-usage token test` | Fetch once to verify auth |
| `cursor-usage token clear` | Remove token from keyring |
| `cursor-usage fetch` | Update `status.json` cache |
| `cursor-usage tray` | System tray / menu bar UI |
| `cursor-usage config show` | Show `pollMinutes`, warn threshold, etc. |
| `cursor-usage open-dashboard` | Open Cursor usage in browser |

Token setup: [AUTH.md](AUTH.md).

## Tests

```bash
pytest
```

Or run the verify script for your OS (see above).

## Data paths

Cache and config use `platformdirs`, for example on Linux:

- `~/.local/share/cursor-usage/`
- `~/.config/cursor-usage/`

API field reference: [usage-summary-fields.md](usage-summary-fields.md).
