# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for macOS distribution
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
    # Fallback if import fails - use relative path resolution
    ROOT_DIR = Path(__file__).parent.parent.parent if '__file__' in globals() else Path.cwd().parent.parent
    SRC_DIR = ROOT_DIR / "src"
    APP_NAME = "InvoiceProcessor"
    APP_VERSION = "1.0.0"
    APP_COPYRIGHT = "© 2024 Invoice Processor Team"
    MACOS_SETTINGS = {
        "bundle_identifier": "com.invoiceprocessor.app",
        "icon": str(ROOT_DIR / "cd" / "assets" / "icons" / "app.icns"),
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
    codesign_identity=MACOS_SETTINGS.get("codesign_identity"),
    entitlements_file=None,
    icon=MACOS_SETTINGS["icon"] if os.path.exists(MACOS_SETTINGS["icon"]) else None,
)

app = BUNDLE(
    exe,
    name=f'{APP_NAME}.app',
    icon=MACOS_SETTINGS["icon"] if os.path.exists(MACOS_SETTINGS["icon"]) else None,
    bundle_identifier=MACOS_SETTINGS["bundle_identifier"],
    version=APP_VERSION,
    info_plist={
        'CFBundleDisplayName': APP_NAME,
        'CFBundleName': APP_NAME,
        'CFBundleVersion': APP_VERSION,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleExecutable': APP_NAME,
        'CFBundleIdentifier': MACOS_SETTINGS["bundle_identifier"],
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14.0',
        'NSHumanReadableCopyright': APP_COPYRIGHT,
        'NSPrincipalClass': 'NSApplication',
        'NSRequiresAquaSystemAppearance': False,
    },
)