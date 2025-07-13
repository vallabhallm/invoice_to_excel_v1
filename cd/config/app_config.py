"""
Application configuration for distribution builds
"""

import os
from pathlib import Path

# Application metadata
APP_NAME = "InvoiceProcessor"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-Powered Invoice Processing Application"
APP_AUTHOR = "Invoice Processor Team"
APP_COPYRIGHT = "© 2024 Invoice Processor Team"
APP_IDENTIFIER = "com.invoiceprocessor.app"

# Build paths
ROOT_DIR = Path(__file__).parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
CD_DIR = ROOT_DIR / "cd"
ASSETS_DIR = CD_DIR / "assets"
DIST_DIR = CD_DIR / "dist"
BUILD_DIR = CD_DIR / "build"

# PyInstaller common settings
PYINSTALLER_COMMON = {
    "name": APP_NAME,
    "console": False,  # GUI application
    "onefile": True,   # Single executable
    "clean": True,     # Clean build
    "noconfirm": True, # No confirmation prompts
}

# Platform-specific settings
MACOS_SETTINGS = {
    "windowed": True,
    "icon": str(ASSETS_DIR / "icons" / "app.icns"),
    "bundle_identifier": APP_IDENTIFIER,
    "codesign_identity": None,  # Set to your developer identity for signing
}

WINDOWS_SETTINGS = {
    "windowed": True,
    "icon": str(ASSETS_DIR / "icons" / "app.ico"),
    "version_file": str(ASSETS_DIR / "windows" / "version_info.txt"),
}

# Dependencies that might need explicit inclusion
HIDDEN_IMPORTS = [
    "invoice_processor",
    "invoice_processor.extractors",
    "invoice_processor.models", 
    "invoice_processor.utils",
    "invoice_processor.workflows",
    "pydantic",
    "prefect",
    "typer",
    "rich",
    "openai",
    "anthropic",
    "pdf2image",
    "pytesseract",
    "PyPDF2",
    "pandas",
    "Pillow",
]

# Data files to include
DATA_FILES = [
    (str(SRC_DIR), "src"),
    (str(ROOT_DIR / "README.md"), "."),
    (str(ROOT_DIR / ".env.example"), "."),
]

# Exclude patterns
EXCLUDES = [
    "tests",
    "test_*",
    "*_test",
    "pytest",
    "coverage",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
]

def get_entry_point():
    """Get the main entry point for the application"""
    return str(SRC_DIR / "invoice_processor" / "main.py")

def get_version_string():
    """Get version string for file naming"""
    return f"v{APP_VERSION}"

def ensure_directories():
    """Ensure required directories exist"""
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    (ASSETS_DIR / "icons").mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "macos").mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "windows").mkdir(parents=True, exist_ok=True)