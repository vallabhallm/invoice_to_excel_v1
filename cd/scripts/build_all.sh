#!/bin/bash
# Build script for all platforms - Invoice Processor

set -e

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

main() {
    local start_time
    start_time=$(date +%s)
    
    log_info "Starting multi-platform build for Invoice Processor"
    
    local project_root cd_dir
    project_root=$(get_project_root)
    cd_dir=$(get_cd_dir)
    
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🏗️  Invoice Processor - Multi-Platform Build"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Project: $(basename "$project_root")"
    echo "Version: $(get_app_version)"
    echo "Date:    $(date)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    # Check prerequisites once
    check_python
    check_poetry
    
    # Detect current platform
    local current_platform
    case "$(uname -s)" in
        Darwin*)  current_platform="macOS" ;;
        Linux*)   current_platform="Linux" ;;
        MINGW*|CYGWIN*|MSYS*) current_platform="Windows" ;;
        *)        current_platform="Unknown" ;;
    esac
    
    log_info "Current platform: $current_platform"
    
    # Build for current platform
    case "$current_platform" in
        "macOS")
            build_macos
            ;;
        "Windows")
            build_windows
            ;;
        "Linux")
            log_warning "Linux builds not yet implemented"
            log_info "You can run the Windows build script in WSL or Wine"
            ;;
        *)
            log_error "Unsupported platform: $current_platform"
            exit 1
            ;;
    esac
    
    # Cross-platform builds (if tools available)
    if [[ "$current_platform" == "macOS" ]]; then
        log_info "Checking for cross-platform build capabilities..."
        
        # Check if we can build Windows on macOS (using Wine)
        if command_exists wine; then
            log_info "Wine detected - attempting Windows cross-build"
            build_windows_on_macos
        else
            log_info "Install Wine to enable Windows cross-builds on macOS"
        fi
    fi
    
    # Summary
    local end_time
    end_time=$(date +%s)
    
    echo
    print_final_summary "$start_time" "$end_time"
}

build_macos() {
    log_info "🍎 Building macOS DMG..."
    echo
    
    if ./scripts/build_macos.sh; then
        log_success "macOS build completed"
    else
        log_error "macOS build failed"
        return 1
    fi
    echo
}

build_windows() {
    log_info "🪟 Building Windows EXE..."
    echo
    
    if ./scripts/build_windows.sh; then
        log_success "Windows build completed"
    else
        log_error "Windows build failed"
        return 1
    fi
    echo
}

build_windows_on_macos() {
    log_info "🍎➡️🪟 Attempting Windows cross-build on macOS..."
    echo
    
    # This would require Wine and additional setup
    log_warning "Cross-platform Windows builds require additional Wine configuration"
    log_info "Consider using a Windows VM or GitHub Actions for Windows builds"
    echo
}

print_final_summary() {
    local start_time="$1"
    local end_time="$2"
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    local cd_dir
    cd_dir=$(get_cd_dir)
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_success "Multi-platform build completed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Total build time: ${minutes}m ${seconds}s"
    echo "App version:      $(get_app_version)"
    echo
    
    # List generated files
    if [[ -d "$cd_dir/dist" ]]; then
        log_info "Generated distributions:"
        find "$cd_dir/dist" -type f \( -name "*.dmg" -o -name "*.exe" -o -name "*.zip" \) -exec ls -lh {} \; | while read -r line; do
            echo "  📦 $line"
        done
    else
        log_warning "No distribution files found in $cd_dir/dist"
    fi
    
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Distributions ready for release!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "Next steps:"
    echo "1. Test the distributions on target platforms"
    echo "2. Upload to GitHub Releases"
    echo "3. Update documentation with download links"
    echo "4. Notify users of the new release"
    echo
}

# Help function
show_help() {
    cat << EOF
Invoice Processor Multi-Platform Build Script

USAGE:
    ./build_all.sh [OPTIONS]

OPTIONS:
    -h, --help     Show this help message
    --clean        Clean build artifacts before building
    --macos-only   Build only for macOS (if on macOS)
    --windows-only Build only for Windows (if on Windows/WSL)

EXAMPLES:
    ./build_all.sh                 # Build for current platform
    ./build_all.sh --clean         # Clean and build
    ./build_all.sh --macos-only    # macOS only

REQUIREMENTS:
    - Python 3.9+
    - Poetry
    - Platform-specific tools (see README.md)

For more information, see cd/README.md
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --clean)
            clean_build
            shift
            ;;
        --macos-only)
            if [[ "$(uname -s)" == "Darwin" ]]; then
                build_macos
                exit 0
            else
                log_error "macOS build can only run on macOS"
                exit 1
            fi
            ;;
        --windows-only)
            build_windows
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi