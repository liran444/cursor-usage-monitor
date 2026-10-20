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

## CI and publishing

`.github/workflows/release-build.yml` builds all three installers on tag push `v*` or manual dispatch.

On **tag push** (`v*`):

1. Windows, macOS, and Linux jobs upload build artifacts.
2. The `release` job creates a **GitHub Release** for that tag and attaches all three installers plus `LICENSE` and `THIRD_PARTY_NOTICES.md`.

**Release checklist**

1. Bump `project.version` in `pyproject.toml`.
2. Commit, tag `v{version}` (e.g. `v0.1.9`), push the tag.
3. Wait for the workflow; installers appear under **Releases** on GitHub.

Manual **workflow_dispatch** still builds artifacts but does **not** create a GitHub Release (no tag ref).

## Qt and binary distribution

This app uses PySide6 (Qt) under LGPL. Installers bundle Qt and other libraries — see [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and [Qt licensing](https://www.qt.io/licensing/).
