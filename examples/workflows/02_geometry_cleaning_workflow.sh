#!/bin/bash
# Geometry Cleaning Workflow
#
# This script demonstrates how to clean problematic geometry before meshing.
# Useful for real-world CAD files with issues like gaps, overlaps, etc.

set -e

# Configuration
INPUT_STEP="input.step"
CLEANED_STEP="cleaned.step"
OUTPUT_MESH="mesh.k"
MESH_SIZE=2.0

echo "==================================="
echo "Geometry Cleaning Workflow"
echo "==================================="
echo ""

# Step 1: Analyze original geometry
echo "[1/6] Analyzing original geometry..."
koomesh geometry info "$INPUT_STEP" --verbose
echo ""

# Step 2: Clean geometry
echo "[2/6] Cleaning geometry..."
koomesh geometry clean "$INPUT_STEP" \
  --output "$CLEANED_STEP" \
  --heal-surfaces \
  --fill-gaps 0.1 \
  --remove-small-features 0.5
echo ""

# Step 3: Compare before and after
echo "[3/6] Comparing original vs cleaned..."
koomesh geometry compare "$INPUT_STEP" "$CLEANED_STEP"
echo ""

# Step 4: Analyze cleaned geometry
echo "[4/6] Analyzing cleaned geometry..."
koomesh geometry info "$CLEANED_STEP"
echo ""

# Step 5: Generate mesh from cleaned geometry
echo "[5/6] Generating mesh from cleaned geometry..."
koomesh generate "$CLEANED_STEP" \
  --mesh-size "$MESH_SIZE" \
  --output "$OUTPUT_MESH"
echo ""

# Step 6: Quality check
echo "[6/6] Checking mesh quality..."
koomesh quality check "$OUTPUT_MESH" --report html -o quality_report.html
echo ""

echo "Workflow complete!"
echo ""
echo "Files created:"
echo "  - Cleaned geometry: $CLEANED_STEP"
echo "  - Mesh: $OUTPUT_MESH"
echo "  - Quality report: quality_report.html"
echo ""
