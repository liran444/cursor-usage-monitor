# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).resolve().parent.parent

a = Analysis(
    [str(root / "cursor_usage" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "README-USER.txt"), "."), (str(root / "LICENSE"), ".")],
    hiddenimports=["pystray._win32", "keyring.backends"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cursor-usage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CursorUsageMonitor",
)
