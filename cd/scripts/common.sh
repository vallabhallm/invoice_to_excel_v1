#!/bin/bash
# Common functions for build scripts

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get project root directory
get_project_root() {
    # Use a cross-platform approach that works on both macOS and Windows
    local current_dir="$(pwd)"
    
    # If we're in the cd directory or its subdirectories, go up to find project root
    if [[ "$current_dir" == */cd* ]]; then
        # Extract everything before /cd
        local project_root="${current_dir%%/cd*}"
        echo "$project_root"
    else
        # Fallback: traverse up from script location
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
        local project_root="$(cd "$script_dir/../.." && pwd)"
        echo "$project_root"
    fi
}

# Get CD directory
get_cd_dir() {
    echo "$(get_project_root)/cd"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_python() {
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python version: $python_version"
    
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
        log_error "Python 3.9+ is required"
        exit 1
    fi
}

check_poetry() {
    if ! command_exists poetry; then
        log_error "Poetry is required but not installed"
        log_info "Install with: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    log_info "Poetry found: $(poetry --version)"
}

# Setup build environment
setup_build_env() {
    local project_root
    project_root=$(get_project_root)
    
    log_info "Setting up build environment..."
    
    cd "$project_root"
    
    # Install dependencies if needed
    if [[ ! -d ".venv" ]]; then
        log_info "Installing dependencies with Poetry..."
        poetry install --only main
    fi
    
    # Install PyInstaller and build dependencies
    log_info "Installing build dependencies..."
    poetry add --group=dev pyinstaller
    
    # Platform-specific dependencies
    case "$(uname -s)" in
        Darwin*)
            if ! command_exists create-dmg; then
                log_warning "create-dmg not found. Install with: brew install create-dmg"
            fi
            ;;
        MINGW*|CYGWIN*|MSYS*)
            log_info "Windows build environment detected"
            # Additional Windows-specific setup could go here
            ;;
    esac
}

# Clean build artifacts
clean_build() {
    local cd_dir
    cd_dir=$(get_cd_dir)
    
    log_info "Cleaning build artifacts..."
    
    # Create directories if they don't exist
    mkdir -p "$cd_dir/build"
    mkdir -p "$cd_dir/dist"
    
    # Clean the directories
    rm -rf "$cd_dir/build/"*
    rm -rf "$cd_dir/dist/"*
    
    # Clean PyInstaller cache
    find "$cd_dir" -name "*.pyc" -delete 2>/dev/null || true
    find "$cd_dir" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Build artifacts cleaned"
}

# Get application version
get_app_version() {
    local project_root
    project_root=$(get_project_root)
    
    cd "$project_root"
    poetry version -s
}

# Create default app icon if it doesn't exist
create_default_icon() {
    local icon_dir="$1"
    local icon_name="$2"
    local icon_path="$icon_dir/$icon_name"
    
    if [[ ! -f "$icon_path" ]]; then
        log_warning "Icon not found at $icon_path, creating default icon"
        
        mkdir -p "$icon_dir"
        
        # Create a simple colored square as default icon
        # This requires ImageMagick or similar tool
        if command_exists convert; then
            convert -size 512x512 xc:'#2E86AB' \
                    -fill white -gravity center \
                    -pointsize 72 -annotate +0+0 'IP' \
                    "$icon_path"
            log_info "Created default icon at $icon_path"
        else
            log_warning "ImageMagick not found. Please provide custom icon at $icon_path"
            # Create empty file to prevent build errors
            touch "$icon_path"
        fi
    fi
}

# Validate built executable
validate_executable() {
    local executable_path="$1"
    
    if [[ ! -f "$executable_path" ]]; then
        log_error "Executable not found at $executable_path"
        return 1
    fi
    
    log_info "Validating executable: $executable_path"
    
    # Check file size (should be reasonable for a packaged app)
    local file_size
    file_size=$(stat -f%z "$executable_path" 2>/dev/null || stat -c%s "$executable_path" 2>/dev/null)
    local size_mb=$((file_size / 1024 / 1024))
    
    log_info "Executable size: ${size_mb}MB"
    
    if [[ $size_mb -lt 10 ]]; then
        log_warning "Executable seems unusually small (${size_mb}MB)"
    elif [[ $size_mb -gt 500 ]]; then
        log_warning "Executable seems unusually large (${size_mb}MB)"
    fi
    
    # Check if executable is valid
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if file "$executable_path" | grep -q "Mach-O"; then
            log_success "Valid macOS executable"
            return 0
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        if file "$executable_path" | grep -q "PE32"; then
            log_success "Valid Windows executable"
            return 0
        fi
    fi
    
    log_error "Executable validation failed"
    return 1
}

# Print build summary
print_build_summary() {
    local platform="$1"
    local output_file="$2"
    local start_time="$3"
    local end_time="$4"
    
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo
    log_success "Build completed successfully!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Platform:     $platform"
    echo "Output:       $output_file"
    echo "Build time:   ${minutes}m ${seconds}s"
    echo "App version:  $(get_app_version)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
}