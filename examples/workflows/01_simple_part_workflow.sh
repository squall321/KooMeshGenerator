#!/bin/bash
# Simple Part Meshing Workflow
#
# This script demonstrates a basic workflow for converting a single STEP file
# to an LS-DYNA mesh with quality checking and visualization.

set -e  # Exit on error

# Configuration
INPUT_STEP="part.step"
OUTPUT_MESH="part.k"
MESH_SIZE=2.0
QUALITY_REPORT="quality_report.html"
MESH_SCREENSHOT="mesh_preview.png"

echo "==================================="
echo "Simple Part Meshing Workflow"
echo "==================================="
echo ""

# Step 1: Analyze geometry
echo "[1/5] Analyzing geometry..."
koomesh geometry info "$INPUT_STEP"
echo ""

# Step 2: Generate mesh
echo "[2/5] Generating mesh (mesh size: ${MESH_SIZE})..."
koomesh generate "$INPUT_STEP" \
  --mesh-size "$MESH_SIZE" \
  --output "$OUTPUT_MESH" \
  --hex-priority
echo ""

# Step 3: Check quality
echo "[3/5] Checking mesh quality..."
koomesh quality check "$OUTPUT_MESH" \
  --report html \
  --output "$QUALITY_REPORT"
echo ""

# Step 4: Visualize mesh
echo "[4/5] Creating visualization..."
koomesh visualize "$OUTPUT_MESH" \
  --screenshot "$MESH_SCREENSHOT"
echo ""

# Step 5: Summary
echo "[5/5] Workflow complete!"
echo ""
echo "Output files:"
echo "  - Mesh: $OUTPUT_MESH"
echo "  - Quality Report: $QUALITY_REPORT"
echo "  - Screenshot: $MESH_SCREENSHOT"
echo ""
echo "Next steps:"
echo "  - Open $QUALITY_REPORT in a web browser"
echo "  - Review quality metrics"
echo "  - If quality is acceptable, use $OUTPUT_MESH in simulation"
echo ""
