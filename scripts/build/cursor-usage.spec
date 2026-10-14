# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: one-folder dist, single windowed app (tray + widget).

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

SPECPATH = Path(SPECPATH)
REPO_ROOT = SPECPATH.parents[1]
SRC = REPO_ROOT / "src"

block_cipher = None

datas = []
binaries = []
hiddenimports = [
    "certifi",
    "httpx",
    "httpcore",
    "h11",
    "anyio",
    "sniffio",
    "idna",
    "keyring",
    "keyring.backends",
    "keyring.backends.Windows",
    "keyring.backends.macOS",
    "keyring.backends.SecretService",
    "keyring.backends.fail",
    "keyring.backends.chainer",
    "browser_cookie3",
    "rookiepy",
    "qt_material_icons",
    "pyperclip",
    "platformdirs",
    "cursor_usage_app",
]

for pkg in ("qt_material_icons", "certifi", "keyring"):
    try:
        _d, _b, _h = collect_all(pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        pass

hiddenimports += collect_submodules("keyring.backends")

pathex = [str(SRC)]

a = Analysis(
    [str(SPECPATH / "tray_entry.py")],
    pathex=pathex,
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(SPECPATH / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_app = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="cursor-usage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe_app,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="cursor-usage",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Cursor Usage.app",
        icon=None,
        bundle_identifier="com.lirandekamhi.cursor-usage",
        info_plist={
            "CFBundleName": "Cursor Usage",
            "CFBundleDisplayName": "Cursor Usage",
            "NSHighResolutionCapable": True,
            "LSUIElement": True,
        },
    )
