#!/bin/bash
#
# Example: Complete workflow using Apptainer container
#

IMAGE="./koomesh.sif"

if [ ! -f "$IMAGE" ]; then
    echo "Error: Container not found. Build first:"
    echo "  ./apptainer/build.sh"
    exit 1
fi

echo "KooMesh Complete Workflow Example"
echo "=================================="
echo

# Step 1: Create STEP file using CadQuery
echo "[1/4] Creating STEP file..."
apptainer exec "$IMAGE" python3 << 'EOF'
import cadquery as cq
box = cq.Workplane('XY').box(100, 50, 20)
box.val().exportStep('/tmp/example_box.step')
print("  ✓ Created: /tmp/example_box.step")
EOF

# Step 2: Generate mesh programmatically
echo "[2/4] Generating mesh..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
mesh = create_structured_box_mesh(100, 50, 20, 5, 3, 2)
print(f"  ✓ Generated: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

# Save mesh info
with open('/tmp/mesh_info.txt', 'w') as f:
    f.write(f"Nodes: {mesh.num_nodes()}\n")
    f.write(f"Elements: {mesh.num_elements()}\n")
EOF

# Step 3: Quality check
echo "[3/4] Quality check..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.meshing.quality_checker import QualityChecker

mesh = create_structured_box_mesh(100, 50, 20, 5, 3, 2)
checker = QualityChecker()
report = checker.check_mesh(mesh)

print(f"  Jacobian: min={report.jacobian['min']:.2f}, max={report.jacobian['max']:.2f}")
print(f"  Aspect ratio: min={report.aspect_ratio['min']:.2f}, max={report.aspect_ratio['max']:.2f}")
print(f"  Bad elements: {report.num_bad_elements}/{mesh.num_elements()}")

if report.num_bad_elements == 0:
    print("  ✓ All elements passed!")
EOF

# Step 4: Export to LS-DYNA
echo "[4/4] Exporting to LS-DYNA..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.export.lsdyna_writer import LSDynaWriter
from koomesh.io.hierarchy_parser import HierarchyNode

mesh = create_structured_box_mesh(100, 50, 20, 5, 3, 2)
root = HierarchyNode(name='ExampleBox', level=0)

with LSDynaWriter('/tmp/example_output.k') as writer:
    writer.write_complete_model([mesh], [], root)

import os
size = os.path.getsize('/tmp/example_output.k')
print(f"  ✓ Created: /tmp/example_output.k ({size/1024:.1f} KB)")
EOF

echo
echo "=================================="
echo "✓ Complete workflow finished!"
echo "=================================="
echo
echo "Output files:"
echo "  /tmp/example_box.step     - STEP CAD file"
echo "  /tmp/example_output.k     - LS-DYNA keyword file"
echo
echo "Check output:"
echo "  head -20 /tmp/example_output.k"
