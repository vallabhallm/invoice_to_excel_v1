# Continuous Delivery (CD) for Invoice Processor

This directory contains all the necessary scripts and configurations for building cross-platform distributions of the Invoice Processor application.

## 📁 Directory Structure

```
cd/
├── scripts/           # Build and distribution scripts
│   ├── build_macos.sh     # macOS DMG build script
│   ├── build_windows.sh   # Windows EXE build script
│   ├── build_all.sh       # Build for all platforms
│   └── common.sh          # Common build functions
├── config/            # Build configuration files
│   ├── macos.spec         # PyInstaller spec for macOS
│   ├── windows.spec       # PyInstaller spec for Windows
│   └── app_config.py      # Application configuration
├── assets/            # Distribution assets
│   ├── icons/             # Application icons
│   ├── macos/             # macOS-specific assets
│   └── windows/           # Windows-specific assets
├── dist/              # Output distributions (gitignored)
└── build/             # Build artifacts (gitignored)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Poetry installed
- Platform-specific tools:
  - **macOS**: Xcode Command Line Tools, `create-dmg`
  - **Windows**: Visual Studio Build Tools or equivalent

### Build All Platforms
```bash
cd cd/
./scripts/build_all.sh
```

### Build Specific Platform
```bash
# macOS DMG
./scripts/build_macos.sh

# Windows EXE
./scripts/build_windows.sh
```

## 📦 Distribution Outputs

- **macOS**: `dist/InvoiceProcessor-{version}.dmg`
- **Windows**: `dist/InvoiceProcessor-{version}-setup.exe`

## 🔧 Configuration

Build configurations are stored in the `config/` directory and can be customized for different deployment scenarios.

## 📋 Build Process

1. **Environment Setup**: Installs dependencies and PyInstaller
2. **Asset Preparation**: Copies icons and platform-specific assets
3. **PyInstaller Build**: Creates standalone executables
4. **Package Creation**: Generates DMG (macOS) or installer (Windows)
5. **Verification**: Tests the built distributions

## 🐛 Troubleshooting

Common issues and solutions are documented in each platform-specific script.