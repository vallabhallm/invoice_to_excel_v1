#!/bin/bash
# macOS DMG build script for Invoice Processor

set -e

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Build configuration
PLATFORM="macOS"
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
    
    # Check macOS-specific requirements
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script must be run on macOS"
        exit 1
    fi
    
    # Setup environment
    setup_build_env
    clean_build
    
    cd "$project_root"
    
    # Create icon directories and default icons
    local icon_dir="$cd_dir/assets/icons"
    create_default_icon "$icon_dir" "app.icns"
    
    # Activate poetry environment and build
    log_info "Building macOS application with PyInstaller..."
    
    poetry run pyinstaller \
        --distpath "$cd_dir/build/macos" \
        --workpath "$cd_dir/build/temp" \
        --clean \
        --noconfirm \
        "$cd_dir/config/macos.spec"
    
    local app_bundle="$cd_dir/build/macos/$APP_NAME.app"
    
    if [[ ! -d "$app_bundle" ]]; then
        log_error "App bundle not created at $app_bundle"
        exit 1
    fi
    
    log_success "App bundle created: $app_bundle"
    
    # Validate the app bundle
    log_info "Validating app bundle..."
    if [[ ! -f "$app_bundle/Contents/MacOS/$APP_NAME" ]]; then
        log_error "App executable not found in bundle"
        exit 1
    fi
    
    validate_executable "$app_bundle/Contents/MacOS/$APP_NAME"
    
    # Create DMG
    create_dmg "$app_bundle" "$cd_dir"
    
    local end_time
    end_time=$(date +%s)
    
    local dmg_file
    dmg_file=$(find "$cd_dir/dist" -name "*.dmg" -type f | head -1)
    
    print_build_summary "$PLATFORM" "$dmg_file" "$start_time" "$end_time"
}

create_dmg() {
    local app_bundle="$1"
    local cd_dir="$2"
    local version
    version=$(get_app_version)
    
    log_info "Creating DMG installer..."
    
    local dmg_name="$APP_NAME-$version-macOS"
    local dmg_path="$cd_dir/dist/$dmg_name.dmg"
    
    # Ensure dist directory exists
    mkdir -p "$cd_dir/dist"
    
    # Remove existing DMG
    rm -f "$dmg_path"
    
    if command_exists create-dmg; then
        # Use create-dmg for professional-looking DMG
        log_info "Using create-dmg for DMG creation..."
        
        create-dmg \
            --volname "$APP_NAME $version" \
            --volicon "$cd_dir/assets/icons/app.icns" \
            --window-pos 200 120 \
            --window-size 800 400 \
            --icon-size 100 \
            --icon "$APP_NAME.app" 200 190 \
            --hide-extension "$APP_NAME.app" \
            --app-drop-link 600 185 \
            --disk-image-size 500 \
            "$dmg_path" \
            "$app_bundle" || {
                log_warning "create-dmg failed, falling back to hdiutil"
                create_dmg_hdiutil "$app_bundle" "$dmg_path"
            }
    else
        log_info "create-dmg not found, using hdiutil..."
        create_dmg_hdiutil "$app_bundle" "$dmg_path"
    fi
    
    if [[ -f "$dmg_path" ]]; then
        log_success "DMG created: $dmg_path"
        
        # Get DMG size
        local dmg_size
        dmg_size=$(du -h "$dmg_path" | cut -f1)
        log_info "DMG size: $dmg_size"
        
        # Verify DMG
        log_info "Verifying DMG..."
        if hdiutil verify "$dmg_path" >/dev/null 2>&1; then
            log_success "DMG verification passed"
        else
            log_warning "DMG verification failed"
        fi
    else
        log_error "Failed to create DMG"
        exit 1
    fi
}

create_dmg_hdiutil() {
    local app_bundle="$1"
    local dmg_path="$2"
    
    # Create temporary directory for DMG contents
    local temp_dmg_dir
    temp_dmg_dir=$(mktemp -d)
    
    # Copy app bundle to temp directory
    cp -R "$app_bundle" "$temp_dmg_dir/"
    
    # Create symbolic link to Applications
    ln -s /Applications "$temp_dmg_dir/Applications"
    
    # Create DMG
    hdiutil create \
        -volname "$APP_NAME $(get_app_version)" \
        -srcfolder "$temp_dmg_dir" \
        -ov \
        -format UDZO \
        "$dmg_path"
    
    # Cleanup
    rm -rf "$temp_dmg_dir"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi