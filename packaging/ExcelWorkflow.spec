# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).resolve().parent
backend = root / "backend"

a = Analysis(
    [str(backend / "run.py")],
    pathex=[str(backend)],
    binaries=[],
datas=[(str(root / "frontend" / "dist"), "frontend/dist")],
    hiddenimports=["app.models", "app.routers", "app.services", "openpyxl", "webview.platforms.edgechromium"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ExcelWorkflow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
