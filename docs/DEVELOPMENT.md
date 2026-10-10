# Development

**Requirements:** Python 3.10+, and a graphical session for tray testing (Linux/macOS/Windows).

## Setup

From the repo root, run the script for your OS:

| OS | Command |
|----|---------|
| **Linux** | `./scripts/install-dev-linux.sh` |
| **macOS** | `./scripts/install-dev-macos.sh` |
| **Windows** | `.\scripts\Install-Dev.ps1` |

Each script creates a `.venv`, activates it, runs `pip install -e ".[dev]"`, then opens an interactive dev shell with the venv active.

**Skip the auto-shell** (e.g. CI):

- Windows: `.\scripts\Install-Dev.ps1 -NoShell`
- Linux/macOS: `INSTALL_DEV_NO_SHELL=1 ./scripts/install-dev-<os>.sh`

**Re-activate later:**

- Windows: `. .\scripts\enter-dev.ps1`
- Linux/macOS: `source ./scripts/enter-dev.sh`

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

## Data paths

Cache and config use `platformdirs`, for example on Linux:

- `~/.local/share/cursor-usage/`
- `~/.config/cursor-usage/`

API field reference: [usage-summary-fields.md](usage-summary-fields.md).
