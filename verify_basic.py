#!/usr/bin/env python3
"""
Basic Functional Verification
==============================

Simple verification that all modules can be imported and basic functionality works.
"""

import sys
sys.path.insert(0, '.')

print("=" * 70)
print("KOOMESH BASIC VERIFICATION")
print("=" * 70)
print()

# Test 1: All imports
print("[1/3] Testing all module imports...")
try:
    from koomesh.config import KooMeshConfig
    from koomesh.utils.logger import setup_logger
    from koomesh.io.step_reader import STEPReader
    from koomesh.io.hierarchy_parser import HierarchyParser, HierarchyNode
    from koomesh.geometry.shape_classifier import ShapeClassifier, MeshType
    from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType, create_structured_box_mesh
    from koomesh.meshing.hex_mesher import HexMesher
    from koomesh.meshing.tet_mesher import TetMesher
    from koomesh.meshing.quality_checker import QualityChecker
    from koomesh.contact.contact_data import ContactManager, ContactPair
    from koomesh.contact.contact_detector import ContactDetector
    from koomesh.contact.hierarchy_rules import HierarchyRules
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.core.pipeline import MeshPipeline, PipelineStage
    from koomesh.core.batch_processor import BatchProcessor, BatchJob

    print("  ✓ All 15 modules imported successfully")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Basic functionality
print("[2/3] Testing basic functionality...")
try:
    # Config
    config = KooMeshConfig()
    assert config.mesh.default_size == 1.0

    # Mesh creation
    mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)
    assert mesh.num_nodes() == 27
    assert mesh.num_elements() == 8

    # Contact management
    manager = ContactManager()
    assert manager.num_contacts() == 0

    # Hierarchy
    root = HierarchyNode(name="Root", level=0)
    assert root.is_root() == True
    assert root.num_children() == 0

    print("  ✓ Basic functionality working")
except Exception as e:
    print(f"  ✗ Functionality test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: LS-DYNA export
print("[3/3] Testing LS-DYNA export...")
try:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test.k"

        mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)

        with LSDynaWriter(str(output_file)) as writer:
            writer.write_header()
            writer.write_nodes(mesh)
            writer.write_elements(mesh, part_id=1)

        assert output_file.exists()
        content = output_file.read_text()
        assert '*KEYWORD' in content
        assert '*NODE' in content

    print("  ✓ LS-DYNA export working")
except Exception as e:
    print(f"  ✗ Export test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)
print()
print("Summary:")
print("  - All modules import successfully")
print("  - Basic data structures working")
print("  - Mesh generation working")
print("  - LS-DYNA export working")
print()
print("The KooMesh core system is functional!")
