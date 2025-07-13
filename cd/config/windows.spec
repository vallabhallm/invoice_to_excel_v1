# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Windows distribution
"""

import sys
import os
from pathlib import Path

# Add the config directory to Python path
import os
config_dir = Path(os.path.dirname(os.path.abspath(__name__)))
if str(config_dir) not in sys.path:
    sys.path.insert(0, str(config_dir))

# Import app configuration
try:
    from app_config import *
except ImportError:
    # Fallback if import fails
    ROOT_DIR = Path(__file__).parent.parent.parent if '__file__' in globals() else Path.cwd().parent.parent
    SRC_DIR = ROOT_DIR / "src"
    APP_NAME = "InvoiceProcessor"
    APP_VERSION = "1.0.0"
    WINDOWS_SETTINGS = {
        "icon": str(ROOT_DIR / "cd" / "assets" / "icons" / "app.ico"),
        "version_file": str(ROOT_DIR / "cd" / "assets" / "windows" / "version_info.txt"),
    }
    HIDDEN_IMPORTS = ["invoice_processor", "pydantic", "prefect", "typer", "rich"]
    DATA_FILES = [(str(SRC_DIR), "src")]
    EXCLUDES = ["tests", "pytest"]
    
    def get_entry_point():
        return str(SRC_DIR / "invoice_processor" / "main.py")
    
    def ensure_directories():
        pass

# Ensure directories exist
ensure_directories()

block_cipher = None

a = Analysis(
    [get_entry_point()],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=WINDOWS_SETTINGS["icon"] if os.path.exists(WINDOWS_SETTINGS["icon"]) else None,
    version=WINDOWS_SETTINGS.get("version_file") if os.path.exists(WINDOWS_SETTINGS.get("version_file", "")) else None,
    uac_admin=False,
    uac_uiaccess=False,
)