# Simple Windows PyInstaller spec
import os
from pathlib import Path

# Use Windows paths
block_cipher = None

root_dir = Path(r'C:\claude\text-to-excel\invoice_to_excel_v1')
src_dir = root_dir / 'src'
entry_point = src_dir / 'invoice_processor' / 'main.py'

a = Analysis(
    [str(entry_point)],
    pathex=[str(root_dir), str(src_dir)],
    binaries=[],
    datas=[(str(src_dir), 'src')],
    hiddenimports=[
        'invoice_processor',
        'invoice_processor.extractors',
        'invoice_processor.models', 
        'invoice_processor.utils',
        'invoice_processor.workflows',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests'],
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
    name='InvoiceProcessor_64bit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch='x86_64',
    icon=None,
)