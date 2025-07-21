#!/bin/bash
# Windows EXE build script for Invoice Processor

set -e

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Build configuration
PLATFORM="Windows"
APP_NAME="InvoiceProcessor"

main() {
    local start_time
    start_time=$(date +%s)
    
    log_info "Starting $PLATFORM build for $APP_NAME"
    
    # Get directories
    local project_root cd_dir
    project_root=$(get_project_root)
    cd_dir=$(get_cd_dir)
    
    # Check prerequisites
    check_python
    check_poetry
    
    # Setup environment
    setup_build_env
    clean_build
    
    cd "$project_root"
    
    # Create icon directories and default icons
    local icon_dir="$cd_dir/assets/icons"
    local windows_dir="$cd_dir/assets/windows"
    
    create_default_icon "$icon_dir" "app.ico"
    create_version_info "$windows_dir"
    
    # Activate poetry environment and build
    log_info "Building Windows executable with PyInstaller..."
    
    # Check if Windows Python is available for native Windows builds
    local windows_python="/mnt/c/Users/jack/AppData/Local/Programs/Python/Python311/python.exe"
    
    if [[ -f "$windows_python" ]]; then
        log_info "Building native Windows executable using Windows Python..."
        
        # Build 64-bit Windows executable using native Windows Python
        mkdir -p "$cd_dir/build/windows_native"
        
        # Convert Linux paths to Windows paths
        local windows_distpath
        local windows_workpath  
        local windows_main_script
        windows_distpath=$(echo "$cd_dir/build/windows_native" | sed 's|/mnt/c|C:|')
        windows_workpath=$(echo "$cd_dir/build/temp_native" | sed 's|/mnt/c|C:|')
        windows_main_script=$(echo "$project_root/src/invoice_processor/main.py" | sed 's|/mnt/c|C:|')
        
        "$windows_python" -m PyInstaller \
            --onefile \
            --console \
            --name "${APP_NAME}_64bit" \
            --distpath "$windows_distpath" \
            --workpath "$windows_workpath" \
            --clean \
            --noconfirm \
            "$windows_main_script"
        
        if [[ -f "$cd_dir/build/windows_native/${APP_NAME}_64bit.exe" ]]; then
            # Copy to standard location for compatibility
            cp "$cd_dir/build/windows_native/${APP_NAME}_64bit.exe" "$cd_dir/build/windows/$APP_NAME.exe"
            log_success "64-bit Windows executable created: $cd_dir/build/windows_native/${APP_NAME}_64bit.exe"
        else
            log_error "64-bit Windows executable not created"
            return 1
        fi
        
    else
        log_warning "Windows Python not found. Building using WSL PyInstaller (Linux binary)..."
        
        # Use tmp directory to avoid WSL permission issues (creates Linux binary)
        local tmp_dist="/tmp/windows_build_$(date +%s)"
        local tmp_work="/tmp/windows_build_temp_$(date +%s)"
        
        poetry run pyinstaller \
            --distpath "$tmp_dist" \
            --workpath "$tmp_work" \
            --clean \
            --noconfirm \
            "$cd_dir/config/windows.spec"
        
        # Copy built executable to final location
        mkdir -p "$cd_dir/build/windows"
        if [[ -f "$tmp_dist/$APP_NAME" ]]; then
            # Copy and rename to .exe for Windows convention (though it's a Linux binary)
            cp "$tmp_dist/$APP_NAME" "$cd_dir/build/windows/$APP_NAME.exe"
            log_success "Executable copied to $cd_dir/build/windows/$APP_NAME.exe"
            log_warning "Note: This is a Linux binary, not a Windows executable"
        else
            log_error "Built executable not found in $tmp_dist"
            return 1
        fi
        
        # Cleanup temporary directories
        rm -rf "$tmp_dist" "$tmp_work" 2>/dev/null || true
    fi
    
    local exe_file="$cd_dir/build/windows/$APP_NAME.exe"
    
    if [[ ! -f "$exe_file" ]]; then
        log_error "Executable not created at $exe_file"
        exit 1
    fi
    
    log_success "Executable created: $exe_file"
    
    # Validate the executable
    validate_executable "$exe_file"
    
    # Create installer and distribution files
    create_installer "$exe_file" "$cd_dir"
    
    # Copy Windows native executable to dist if it exists
    if [[ -f "$cd_dir/build/windows_native/${APP_NAME}_64bit.exe" ]]; then
        local version
        version=$(get_app_version)
        cp "$cd_dir/build/windows_native/${APP_NAME}_64bit.exe" "$cd_dir/dist/${APP_NAME}-$version-windows_64bit.exe"
        log_success "64-bit distribution created: $cd_dir/dist/${APP_NAME}-$version-windows_64bit.exe"
    fi
    
    local end_time
    end_time=$(date +%s)
    
    local installer_file
    installer_file=$(find "$cd_dir/dist" -name "*setup.exe" -type f | head -1)
    
    print_build_summary "$PLATFORM" "${installer_file:-$exe_file}" "$start_time" "$end_time"
}

create_version_info() {
    local windows_dir="$1"
    local version_file="$windows_dir/version_info.txt"
    local version
    version=$(get_app_version)
    
    mkdir -p "$windows_dir"
    
    if [[ ! -f "$version_file" ]]; then
        log_info "Creating Windows version info file..."
        
        cat > "$version_file" << EOF
# UTF-8
# Version Information for Windows builds

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'Invoice Processor Team'),
            StringStruct(u'FileDescription', u'AI-Powered Invoice Processing Application'),
            StringStruct(u'FileVersion', u'$version'),
            StringStruct(u'InternalName', u'$APP_NAME'),
            StringStruct(u'LegalCopyright', u'© 2024 Invoice Processor Team'),
            StringStruct(u'OriginalFilename', u'$APP_NAME.exe'),
            StringStruct(u'ProductName', u'Invoice Processor'),
            StringStruct(u'ProductVersion', u'$version')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
EOF
        
        log_success "Version info created: $version_file"
    fi
}

create_installer() {
    local exe_file="$1"
    local cd_dir="$2"
    local version
    version=$(get_app_version)
    
    log_info "Creating Windows installer..."
    
    # First, just copy the executable to dist for simple distribution
    local dist_exe="$cd_dir/dist/$APP_NAME-$version-windows.exe"
    mkdir -p "$cd_dir/dist"
    cp "$exe_file" "$dist_exe"
    
    log_success "Standalone executable created: $dist_exe"
    
    # Try to create an installer using NSIS if available
    if command_exists makensis; then
        create_nsis_installer "$exe_file" "$cd_dir" "$version"
    else
        log_info "NSIS not found. Install NSIS to create Windows installer."
        log_info "Standalone executable available: $dist_exe"
    fi
}

create_nsis_installer() {
    local exe_file="$1"
    local cd_dir="$2"
    local version="$3"
    
    log_info "Creating NSIS installer script..."
    
    local nsis_script="$cd_dir/build/installer.nsi"
    local installer_name="$APP_NAME-$version-setup.exe"
    local installer_path="$cd_dir/dist/$installer_name"
    
    cat > "$nsis_script" << EOF
; Invoice Processor NSIS Installer Script
; Auto-generated by build script

!define APP_NAME "$APP_NAME"
!define APP_VERSION "$version"
!define APP_PUBLISHER "Invoice Processor Team"
!define APP_URL "https://github.com/vallabhallm/invoice_to_excel_v1"
!define APP_DESCRIPTION "AI-Powered Invoice Processing Application"

; Main installer attributes
Name "\${APP_NAME} \${APP_VERSION}"
OutFile "$installer_path"
InstallDir "\$PROGRAMFILES64\\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "InstallLocation"
RequestExecutionLevel admin

; Interface settings
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "$cd_dir/assets/icons/app.ico"
!define MUI_UNICON "$cd_dir/assets/icons/app.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "$cd_dir/../README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "\${APP_NAME}"
VIAddVersionKey "CompanyName" "\${APP_PUBLISHER}"
VIAddVersionKey "LegalCopyright" "© 2024 \${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "\${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "\${APP_VERSION}"

Section "Install"
    SetOutPath "\$INSTDIR"
    
    ; Install main executable
    File "$exe_file"
    
    ; Install additional files
    File "$cd_dir/../README.md"
    File "$cd_dir/../.env.example"
    
    ; Create uninstaller
    WriteUninstaller "\$INSTDIR\\Uninstall.exe"
    
    ; Create start menu entries
    CreateDirectory "\$SMPROGRAMS\\\${APP_NAME}"
    CreateShortCut "\$SMPROGRAMS\\\${APP_NAME}\\\${APP_NAME}.lnk" "\$INSTDIR\\\${APP_NAME}.exe"
    CreateShortCut "\$SMPROGRAMS\\\${APP_NAME}\\Uninstall.lnk" "\$INSTDIR\\Uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortCut "\$DESKTOP\\\${APP_NAME}.lnk" "\$INSTDIR\\\${APP_NAME}.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "DisplayName" "\${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "UninstallString" "\$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "InstallLocation" "\$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "DisplayIcon" "\$INSTDIR\\\${APP_NAME}.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "Publisher" "\${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "URLInfoAbout" "\${APP_URL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "DisplayVersion" "\${APP_VERSION}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    ; Remove files
    Delete "\$INSTDIR\\\${APP_NAME}.exe"
    Delete "\$INSTDIR\\README.md"
    Delete "\$INSTDIR\\.env.example"
    Delete "\$INSTDIR\\Uninstall.exe"
    
    ; Remove shortcuts
    Delete "\$SMPROGRAMS\\\${APP_NAME}\\\${APP_NAME}.lnk"
    Delete "\$SMPROGRAMS\\\${APP_NAME}\\Uninstall.lnk"
    Delete "\$DESKTOP\\\${APP_NAME}.lnk"
    RMDir "\$SMPROGRAMS\\\${APP_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\\${APP_NAME}"
    
    ; Remove installation directory
    RMDir "\$INSTDIR"
SectionEnd
EOF
    
    log_info "Building NSIS installer..."
    if makensis "$nsis_script"; then
        log_success "NSIS installer created: $installer_path"
    else
        log_warning "NSIS installer creation failed"
    fi
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi