# Build

Build **on each target OS** (or CI matrix). Requires dev setup first (`pip install -e ".[dev]"` — includes PyInstaller). See [DEVELOPMENT.md](DEVELOPMENT.md).

## Linux x86_64

```bash
./scripts/build-release-linux.sh
# or:
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_linux.spec
```

Output: `dist/CursorUsageMonitor/` with `cursor-usage` binary, `README-USER.txt`, and `LICENSE` bundled.

## Windows

```bash
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_win.spec
```

Output: `dist/CursorUsageMonitor/` — ship with `Install-User.ps1` for recipients.

## macOS

```bash
pyinstaller --noconfirm packaging/pyinstaller/cursor_usage_mac.spec
```

Output: `dist/Cursor Usage Monitor.app` — ship with `install-user-macos.sh` for recipients.

## Checksums (optional)

```bash
cd dist && sha256sum CursorUsageMonitor/cursor-usage >> SHA256SUMS.txt
```

## Spec files

`packaging/pyinstaller/cursor_usage_{linux,win,mac}.spec` — one-folder layout; entry `cursor-usage` with subcommands `tray`, `fetch`, `token`.

## Shipping

Ship release archives with [README-USER.txt](../README-USER.txt) and [LICENSE](../LICENSE). Recipients install via [INSTALL.md](INSTALL.md), not pip.
