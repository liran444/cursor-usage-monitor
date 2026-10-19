# Development

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

## Run locally

```bash
cursor-usage tray
cursor-usage widget
cursor-usage fetch
cursor-usage token test
```

Tray smoke (quit after 2s):

```bash
# Windows PowerShell
$env:CURSOR_USAGE_TRAY_SMOKE_MS=2000; cursor-usage tray
```

## Release build pipeline

1. **PyInstaller one-folder** — `scripts/build/build.ps1` (Windows) or `scripts/build/build.sh` (macOS/Linux).
2. **Platform installer** into `release/`:
   - Windows: `scripts/install/windows/build-installer.ps1` (requires [Inno Setup 6](https://jrsoftware.org/isinfo.php)).
   - Linux: `scripts/install/linux/build-installer.sh` (requires `makeself`).
   - macOS: `scripts/install/macos/build-installer.sh`.

**Version:** bump only `project.version` in `pyproject.toml`. Runtime (`__version__`), PyInstaller, and Windows/macOS/Linux release installers all resolve it via `cursor_usage_app._version` and `scripts/build/read_version.py`.

## Frozen smoke checklist

After building `dist/cursor-usage/` or installing from `release/`:

- [ ] `cursor-usage.exe` (or `dist/.../cursor-usage` on Linux) with `CURSOR_USAGE_TRAY_SMOKE_MS=2000` exits without traceback.
- [ ] Open widget from tray; gear icons (qt-material-icons) render.
- [ ] Windows: taskbar shows app icon, not Python.

## CI

`.github/workflows/release-build.yml` builds all three installers on tag push `v*` or manual dispatch.

## Qt license

This app uses PySide6 (Qt). Qt is available under LGPL. See [Qt licensing](https://www.qt.io/licensing/).
