#!/bin/bash
#
# KooMesh Apptainer Build Script
# ================================
#
# This script builds the KooMesh Apptainer container image.
#
# Usage:
#   ./apptainer/build.sh
#
# Requirements:
#   - Apptainer/Singularity installed
#   - Sudo access (for building)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  KooMesh Apptainer Build Script"
echo "======================================"
echo

# Check if apptainer/singularity is installed
if command -v apptainer &> /dev/null; then
    CONTAINER_CMD="apptainer"
    echo -e "${GREEN}✓${NC} Found: apptainer"
elif command -v singularity &> /dev/null; then
    CONTAINER_CMD="singularity"
    echo -e "${GREEN}✓${NC} Found: singularity"
else
    echo -e "${RED}✗${NC} Error: Neither apptainer nor singularity found"
    echo
    echo "Please install Apptainer:"
    echo "  Ubuntu/Debian: apt-get install apptainer"
    echo "  RHEL/CentOS: yum install apptainer"
    echo "  Or see: https://apptainer.org/docs/admin/main/installation.html"
    exit 1
fi

# Get version
VERSION=$($CONTAINER_CMD --version)
echo "  Version: $VERSION"
echo

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEF_FILE="$PROJECT_ROOT/apptainer/koomesh.def"
OUTPUT_IMAGE="$PROJECT_ROOT/koomesh.sif"
BUILD_DIR="$PROJECT_ROOT/apptainer/build"

echo "Configuration:"
echo "  Project root: $PROJECT_ROOT"
echo "  Definition file: $DEF_FILE"
echo "  Output image: $OUTPUT_IMAGE"
echo

# Check if definition file exists
if [ ! -f "$DEF_FILE" ]; then
    echo -e "${RED}✗${NC} Definition file not found: $DEF_FILE"
    exit 1
fi

# Create temporary build directory
echo "Creating temporary build directory..."
mkdir -p "$BUILD_DIR"

# Copy source files to build directory
echo "Copying source files..."
cp -r "$PROJECT_ROOT/koomesh" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/tests" "$BUILD_DIR/"
[ -f "$PROJECT_ROOT/setup.py" ] && cp "$PROJECT_ROOT/setup.py" "$BUILD_DIR/"
[ -f "$PROJECT_ROOT/README.md" ] && cp "$PROJECT_ROOT/README.md" "$BUILD_DIR/"
[ -f "$PROJECT_ROOT/pyproject.toml" ] && cp "$PROJECT_ROOT/pyproject.toml" "$BUILD_DIR/"

# Create modified definition file with correct paths
echo "Preparing definition file..."
TEMP_DEF="$BUILD_DIR/koomesh_build.def"
cp "$DEF_FILE" "$TEMP_DEF"

# Add files section with correct paths
cat >> "$TEMP_DEF" << 'EOF'

# Files to copy (added by build script)
%files
    apptainer/build/koomesh /opt/KooMeshGenerator/koomesh
    apptainer/build/tests /opt/KooMeshGenerator/tests
EOF

# Check if we need sudo
NEED_SUDO=""
if [ "$EUID" -ne 0 ] && [ "$CONTAINER_CMD" = "apptainer" ]; then
    # Try building without sudo first
    echo "Attempting build without sudo..."
else
    NEED_SUDO="sudo"
fi

# Remove old image if exists
if [ -f "$OUTPUT_IMAGE" ]; then
    echo -e "${YELLOW}!${NC} Removing old image: $OUTPUT_IMAGE"
    rm -f "$OUTPUT_IMAGE"
fi

# Build the container
echo
echo "======================================"
echo "  Building Apptainer Image"
echo "======================================"
echo
echo "This may take 10-20 minutes..."
echo

if $NEED_SUDO $CONTAINER_CMD build "$OUTPUT_IMAGE" "$TEMP_DEF"; then
    echo
    echo "======================================"
    echo -e "  ${GREEN}✓ Build Successful!${NC}"
    echo "======================================"
    echo
    echo "Image created: $OUTPUT_IMAGE"

    # Show image info
    IMAGE_SIZE=$(du -h "$OUTPUT_IMAGE" | cut -f1)
    echo "Image size: $IMAGE_SIZE"

    # Cleanup
    echo
    echo "Cleaning up temporary files..."
    rm -rf "$BUILD_DIR"

    echo
    echo "Usage examples:"
    echo "  # Run tests"
    echo "  $CONTAINER_CMD run $OUTPUT_IMAGE python3 -m pytest tests/"
    echo
    echo "  # Generate mesh"
    echo "  $CONTAINER_CMD run $OUTPUT_IMAGE generate model.step -s 2.0"
    echo
    echo "  # Interactive shell"
    echo "  $CONTAINER_CMD shell $OUTPUT_IMAGE"
    echo

else
    echo
    echo "======================================"
    echo -e "  ${RED}✗ Build Failed${NC}"
    echo "======================================"
    echo
    echo "If you got a permission error, try:"
    echo "  sudo ./apptainer/build.sh"
    echo

    # Cleanup
    rm -rf "$BUILD_DIR"

    exit 1
fi
