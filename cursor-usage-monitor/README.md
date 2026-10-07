# Cursor Usage Monitor

Cross-platform system tray app for Cursor **personal included usage** and **team pool** (dashboard `usage-summary` API). Unofficial; not affiliated with Cursor.

For step-by-step end-user help (token, tray, uninstall), see [README-USER.txt](README-USER.txt) and [docs/platforms.md](docs/platforms.md).

---

## 1. End user install

You do **not** need Python or git. Download the release for your OS (zip or installer), then:

1. **Install**
   - **Linux:** Extract the tarball, run `./scripts/install-user.sh` (or point it at the extracted `CursorUsageMonitor` folder).
   - **Windows:** Extract the zip, run `scripts/Install-User.ps1`.
   - **macOS:** Run `scripts/install-user-macos.sh` with the `.app` from the release (copies to Applications and enables login autostart).

2. **Session token** (required once; again when it expires)
   - Sign in at [cursor.com/dashboard](https://cursor.com/dashboard).
   - DevTools → Application → Cookies → copy `WorkosCursorSessionToken`.
   - Run from the install folder (or PATH):  
     `cursor-usage token set`  
     then verify:  
     `cursor-usage token test`

3. **Run**
   - Tray should start at login after install. Or run: `cursor-usage tray`
   - Icon shows **personal included usage %**; click for details, refresh, and team pool.

More detail: [README-USER.txt](README-USER.txt).

---

## 2. Developer — development

**Requirements:** Python 3.10+, Linux/macOS/Windows with a graphical session for tray testing.

**Setup**

```bash
cd /var/www/html/cursor-usage-monitor
./scripts/install-dev.sh
```

Uses a `.venv` when `python3-venv` is installed; otherwise installs editable for your user (`~/.local/bin`). Optional: `sudo apt install python3-venv` (or `python3.14-venv`) then re-run for an isolated venv.

Manual equivalent:

**Commands**

| Command | Purpose |
|---------|---------|
| `cursor-usage token set` | Save session cookie to OS keyring |
| `cursor-usage token test` | Fetch once to verify auth |
| `cursor-usage token clear` | Remove token from keyring |
| `cursor-usage fetch` | Update `status.json` cache |
| `cursor-usage tray` | System tray / menu bar UI |
| `cursor-usage config show` | Show `pollMinutes`, warn threshold, etc. |
| `cursor-usage open-dashboard` | Open Cursor usage in browser |

**Tests**

```bash
pytest
```

Cache and config paths use `platformdirs` (e.g. Linux: `~/.local/share/cursor-usage/`, `~/.config/cursor-usage/`).

Docs: [docs/AUTH.md](docs/AUTH.md), [docs/usage-summary-fields.md](docs/usage-summary-fields.md).

---

## 3. Developer — build

Build **on each target OS** (or CI matrix). Requires `pip install -e ".[dev]"` (includes PyInstaller).

**Linux x86_64**

```bash
./scripts/build-release-linux.sh
# or:
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_linux.spec
```

Output: `dist/CursorUsageMonitor/` with `cursor-usage` binary, `README-USER.txt`, and `LICENSE` bundled.

**Windows**

```bash
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_win.spec
```

Output: `dist/CursorUsageMonitor/` (use `Install-User.ps1` after copying to recipients).

**macOS**

```bash
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_mac.spec
```

Output: `dist/Cursor Usage Monitor.app` (use `install-user-macos.sh`).

**Checksums (optional)**

```bash
cd dist && sha256sum CursorUsageMonitor/cursor-usage >> SHA256SUMS.txt
```

**Spec files:** `packaging/pyinstaller/cursor_usage_{linux,win,mac}.spec` — one-folder layout; entry `cursor-usage` with subcommands `tray`, `fetch`, `token`.

Ship release zips with [README-USER.txt](README-USER.txt) and [LICENSE](LICENSE). Recipients use **§ End user install** above, not pip.
