#!/bin/bash
# Batch Processing Workflow
#
# This script demonstrates how to process multiple STEP files efficiently
# using batch processing with parallel execution.

set -e

# Configuration
INPUT_DIR="cad_files"
OUTPUT_DIR="meshes"
MESH_SIZE=2.0
PARALLEL_JOBS=4

echo "==================================="
echo "Batch Processing Workflow"
echo "==================================="
echo ""

# Step 1: Create output directory
echo "[1/5] Setting up directories..."
mkdir -p "$OUTPUT_DIR"
echo ""

# Step 2: Preview batch operation (dry run)
echo "[2/5] Previewing batch operation..."
koomesh batch-convert "${INPUT_DIR}/*.step" \
  --output-dir "$OUTPUT_DIR" \
  --mesh-size "$MESH_SIZE" \
  --dry-run
echo ""

# Confirm before proceeding
read -p "Proceed with batch conversion? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

# Step 3: Execute batch conversion
echo "[3/5] Converting all STEP files (parallel: $PARALLEL_JOBS jobs)..."
koomesh batch-convert "${INPUT_DIR}/*.step" \
  --output-dir "$OUTPUT_DIR" \
  --mesh-size "$MESH_SIZE" \
  --element-type tet4 \
  --parallel \
  --jobs "$PARALLEL_JOBS"
echo ""

# Step 4: Check quality of all generated meshes
echo "[4/5] Checking quality of all meshes..."
for mesh in "$OUTPUT_DIR"/*.k; do
    if [ -f "$mesh" ]; then
        echo "Checking: $(basename $mesh)"
        koomesh quality check "$mesh" --report json -o "${mesh%.k}_quality.json"
    fi
done
echo ""

# Step 5: Generate summary
echo "[5/5] Generating summary..."
mesh_count=$(ls -1 "$OUTPUT_DIR"/*.k 2>/dev/null | wc -l)
echo ""
echo "Batch processing complete!"
echo ""
echo "Summary:"
echo "  - Total meshes generated: $mesh_count"
echo "  - Output directory: $OUTPUT_DIR"
echo "  - Mesh size used: $MESH_SIZE"
echo "  - Element type: tet4"
echo ""
echo "Quality reports available: ${OUTPUT_DIR}/*_quality.json"
echo ""
