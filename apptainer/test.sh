#!/bin/bash
#
# Quick test script for KooMesh Apptainer container
#

set -e

IMAGE="./koomesh.sif"

if [ ! -f "$IMAGE" ]; then
    echo "Error: Container image not found: $IMAGE"
    echo "Please build first: ./apptainer/build.sh"
    exit 1
fi

echo "Testing KooMesh Apptainer Container"
echo "===================================="
echo

# Test 1: Basic imports
echo "[1/5] Testing Python imports..."
apptainer exec "$IMAGE" python3 -c "
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.config import KooMeshConfig
from koomesh.meshing.mesh_data import create_structured_box_mesh
print('  ✓ Imports OK')
"

# Test 2: Mesh generation
echo "[2/5] Testing mesh generation..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
mesh = create_structured_box_mesh(10, 10, 10, 2, 2, 2)
assert mesh.num_nodes() == 27
assert mesh.num_elements() == 8
print(f'  ✓ Mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements')
EOF

# Test 3: Quality check
echo "[3/5] Testing quality checker..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.meshing.quality_checker import QualityChecker
mesh = create_structured_box_mesh(10, 10, 10, 2, 2, 2)
checker = QualityChecker()
report = checker.check_mesh(mesh)
print(f'  ✓ Quality: Jacobian={report.jacobian["min"]:.2f}, Bad={report.num_bad_elements}')
EOF

# Test 4: LS-DYNA export
echo "[4/5] Testing LS-DYNA export..."
apptainer exec "$IMAGE" python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/KooMeshGenerator')
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.export.lsdyna_writer import LSDynaWriter
from koomesh.io.hierarchy_parser import HierarchyNode
mesh = create_structured_box_mesh(10, 10, 10, 2, 2, 2)
root = HierarchyNode(name='Test', level=0)
with LSDynaWriter('/tmp/test.k') as writer:
    writer.write_complete_model([mesh], [], root)
import os
size = os.path.getsize('/tmp/test.k')
print(f'  ✓ Export: {size/1024:.1f} KB')
EOF

# Test 5: Unit tests
echo "[5/5] Running unit tests..."
apptainer exec "$IMAGE" python3 -m pytest /opt/KooMeshGenerator/tests/unit/ -q --tb=no

echo
echo "===================================="
echo "✓ All tests passed!"
echo "===================================="
