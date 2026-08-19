# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).resolve().parent
backend = root / "backend"
scenario_samples = root / "sample_data" / "scenarios"
sys.path.insert(0, str(backend))

a = Analysis(
    [str(backend / "run.py")],
    pathex=[str(backend)],
    binaries=[],
    datas=[(str(root / "frontend" / "dist"), "frontend/dist"), (str(scenario_samples), "sample_data/scenarios")],
    hiddenimports=(
        collect_submodules("app")
        + collect_submodules("webview")
        + collect_submodules("uvicorn")
        + collect_submodules("openpyxl")
        + ["win32com.client"]
    ),
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
    upx=False,
    console=False,
)
