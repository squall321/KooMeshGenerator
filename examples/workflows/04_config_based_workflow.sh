#!/bin/bash
# Configuration-Based Workflow
#
# This script demonstrates using YAML configuration files for repeatable,
# complex meshing workflows.

set -e

# Configuration
CONFIG_FILE="crash_analysis_config.yaml"
CONFIG_DIR="configs"

echo "==================================="
echo "Configuration-Based Workflow"
echo "==================================="
echo ""

# Step 1: Create config directory
echo "[1/6] Setting up configuration..."
mkdir -p "$CONFIG_DIR"
echo ""

# Step 2: Use template or create custom config
echo "[2/6] Creating configuration file..."
if [ ! -f "$CONFIG_DIR/$CONFIG_FILE" ]; then
    echo "Copying crash analysis template..."
    cp templates/crash_analysis.yaml "$CONFIG_DIR/$CONFIG_FILE"
    echo "Created: $CONFIG_DIR/$CONFIG_FILE"
    echo "Please edit this file with your specific settings."
    echo ""
    read -p "Press Enter to continue after editing..."
fi
echo ""

# Step 3: Validate configuration
echo "[3/6] Validating configuration..."
koomesh run "$CONFIG_DIR/$CONFIG_FILE" --validate-only
echo ""

# Step 4: Preview workflow (dry run)
echo "[4/6] Preview workflow (dry run)..."
koomesh run "$CONFIG_DIR/$CONFIG_FILE" --dry-run
echo ""

# Confirm before execution
read -p "Execute workflow? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

# Step 5: Execute workflow
echo "[5/6] Executing workflow..."
koomesh run "$CONFIG_DIR/$CONFIG_FILE" --verbose
echo ""

# Step 6: Summary
echo "[6/6] Workflow execution complete!"
echo ""
echo "Configuration used: $CONFIG_DIR/$CONFIG_FILE"
echo ""
echo "To run with different parameters, use overrides:"
echo "  koomesh run $CONFIG_DIR/$CONFIG_FILE --override meshing.mesh_size=1.5"
echo ""
echo "To modify workflow, edit: $CONFIG_DIR/$CONFIG_FILE"
echo ""
