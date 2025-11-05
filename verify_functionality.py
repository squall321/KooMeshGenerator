#!/usr/bin/env python3
"""
Functional Verification Script
===============================

This script verifies the basic functionality of KooMesh components
without requiring PythonOCC or GMSH.

Tests:
1. Configuration system
2. Mesh data structures
3. Contact management
4. Quality checking
5. LS-DYNA export
6. Pipeline components (without actual meshing)
"""

import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

print("=" * 70)
print("KOOMESH FUNCTIONAL VERIFICATION")
print("=" * 70)
print()

test_results = []

# Test 1: Configuration
print("[1/8] Testing configuration system...")
try:
    from koomesh.config import KooMeshConfig

    config = KooMeshConfig()
    assert config.mesh.default_size == 1.0
    assert config.mesh.hex_priority == True
    assert config.contact.enabled == True

    # Test configuration modification
    config.mesh.default_size = 2.0
    assert config.mesh.default_size == 2.0

    # Test validation
    assert config.validate() == True

    print("  ✓ Configuration system working")
    test_results.append(("Configuration", True, None))
except Exception as e:
    print(f"  ✗ Configuration failed: {e}")
    test_results.append(("Configuration", False, str(e)))

# Test 2: Mesh Data Structures
print("[2/8] Testing mesh data structures...")
try:
    from koomesh.meshing.mesh_data import (
        Node, Element, ElementType, MeshData,
        create_structured_box_mesh
    )

    # Create nodes
    node1 = Node(1, 0.0, 0.0, 0.0)
    node2 = Node(2, 1.0, 0.0, 0.0)
    assert node1.coordinates() == (0.0, 0.0, 0.0)

    # Create element
    elem = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])
    assert elem.num_nodes() == 8

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)
    mesh.add_node(node1)
    mesh.add_node(node2)
    assert mesh.num_nodes() == 2

    # Create structured box mesh
    box_mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)
    assert box_mesh.num_nodes() == 27  # (2+1)^3
    assert box_mesh.num_elements() == 8  # 2^3

    print("  ✓ Mesh data structures working")
    test_results.append(("Mesh Data", True, None))
except Exception as e:
    print(f"  ✗ Mesh data failed: {e}")
    test_results.append(("Mesh Data", False, str(e)))

# Test 3: Contact Management
print("[3/8] Testing contact management...")
try:
    from koomesh.contact.contact_data import (
        ContactManager, ContactPair, ContactSurface, ContactType
    )

    manager = ContactManager()

    # Create contact surfaces
    surface1 = ContactSurface(part_id=1, part_name="Part1", node_ids=[1, 2, 3, 4])
    surface2 = ContactSurface(part_id=2, part_name="Part2", node_ids=[5, 6, 7, 8])

    # Create contact pair
    contact = ContactPair(
        master_surface=surface1,
        slave_surface=surface2,
        contact_type=ContactType.TIED
    )

    # Add to manager
    contact_id = manager.add_contact(contact)
    assert contact_id == 1
    assert manager.num_contacts() == 1

    # Get contact
    retrieved = manager.get_contact(contact_id)
    assert retrieved.contact_type == ContactType.TIED

    print("  ✓ Contact management working")
    test_results.append(("Contact Management", True, None))
except Exception as e:
    print(f"  ✗ Contact management failed: {e}")
    test_results.append(("Contact Management", False, str(e)))

# Test 4: Quality Checking
print("[4/8] Testing quality checking...")
try:
    from koomesh.meshing.quality_checker import QualityChecker
    from koomesh.meshing.mesh_data import create_structured_box_mesh

    checker = QualityChecker(
        min_jacobian=0.1,
        max_aspect_ratio=10.0,
        max_skewness=0.8
    )

    # Create test mesh
    mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)

    # Check quality
    report = checker.check_mesh(mesh)

    assert report.num_elements == 8
    assert report.min_jacobian is not None
    assert report.avg_jacobian is not None

    # Regular hex mesh should have good quality
    assert report.min_jacobian > 0.5

    print(f"  ✓ Quality checking working (min_jacobian={report.min_jacobian:.3f})")
    test_results.append(("Quality Checking", True, None))
except Exception as e:
    print(f"  ✗ Quality checking failed: {e}")
    test_results.append(("Quality Checking", False, str(e)))

# Test 5: LS-DYNA Export
print("[5/8] Testing LS-DYNA export...")
try:
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.meshing.mesh_data import create_structured_box_mesh
    from koomesh.contact.contact_data import ContactManager

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_output.k"

        # Create test mesh
        mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)

        # Write LS-DYNA file
        with LSDynaWriter(str(output_file)) as writer:
            writer.write_header("Test Model")
            writer.write_nodes(mesh)
            writer.write_elements(mesh, part_id=1)

        # Verify file was created and has content
        assert output_file.exists()
        content = output_file.read_text()

        assert '*KEYWORD' in content
        assert '*NODE' in content
        assert '*ELEMENT_SOLID' in content
        assert '*END' in content

        # Check node count
        node_lines = [l for l in content.split('\n') if l.strip() and not l.startswith('*')]

        print(f"  ✓ LS-DYNA export working (file size: {len(content)} bytes)")
        test_results.append(("LS-DYNA Export", True, None))
except Exception as e:
    print(f"  ✗ LS-DYNA export failed: {e}")
    test_results.append(("LS-DYNA Export", False, str(e)))

# Test 6: Hierarchy Parser (without STEP)
print("[6/8] Testing hierarchy parser...")
try:
    from koomesh.io.hierarchy_parser import HierarchyNode

    # Create hierarchy tree
    root = HierarchyNode(name="Assembly", level=0)

    child1 = HierarchyNode(name="Part1", parent=root, level=1)
    child2 = HierarchyNode(name="Part2", parent=root, level=1)

    root.children = [child1, child2]

    # Test hierarchy operations
    assert root.num_children() == 2
    assert root.is_root() == True
    assert child1.is_leaf() == True

    # Test descendant finding
    descendants = root.get_all_descendants()
    assert len(descendants) == 2

    print("  ✓ Hierarchy parser working")
    test_results.append(("Hierarchy Parser", True, None))
except Exception as e:
    print(f"  ✗ Hierarchy parser failed: {e}")
    test_results.append(("Hierarchy Parser", False, str(e)))

# Test 7: Logger
print("[7/8] Testing logger...")
try:
    from koomesh.utils.logger import setup_logger, LogTimer
    import logging

    logger = setup_logger('test_logger', level='INFO')
    assert logger is not None
    assert isinstance(logger, logging.Logger)

    # Test log timer
    with LogTimer(logger, "Test operation"):
        import time
        time.sleep(0.01)

    print("  ✓ Logger working")
    test_results.append(("Logger", True, None))
except Exception as e:
    print(f"  ✗ Logger failed: {e}")
    test_results.append(("Logger", False, str(e)))

# Test 8: Pipeline Components (basic)
print("[8/8] Testing pipeline components...")
try:
    from koomesh.core.pipeline import (
        PipelineStage, PipelineProgress, PipelineResult
    )
    from koomesh.core.batch_processor import BatchJob, BatchResult

    # Test pipeline stages
    assert PipelineStage.INITIALIZATION.value == "initialization"
    assert PipelineStage.COMPLETED.value == "completed"

    # Test pipeline progress
    progress = PipelineProgress(
        stage=PipelineStage.MESH_GENERATION,
        progress=50.0,
        message="Testing"
    )
    assert progress.progress == 50.0
    assert progress.elapsed_seconds >= 0

    # Test pipeline result
    result = PipelineResult(success=True)
    assert result.success == True
    assert len(result.meshes) == 0

    # Test batch job
    job = BatchJob(
        input_file=Path("test.step"),
        output_file=Path("test.k"),
        mesh_size=1.0
    )
    assert job.status == 'pending'

    # Test batch result
    batch_result = BatchResult(total_jobs=10, completed=8, failed=2)
    assert batch_result.success_rate == 80.0

    print("  ✓ Pipeline components working")
    test_results.append(("Pipeline Components", True, None))
except Exception as e:
    print(f"  ✗ Pipeline components failed: {e}")
    test_results.append(("Pipeline Components", False, str(e)))

# Summary
print()
print("=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

passed = sum(1 for _, success, _ in test_results if success)
failed = sum(1 for _, success, _ in test_results if not success)

for name, success, error in test_results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status:8} {name}")
    if error:
        print(f"         Error: {error}")

print()
print(f"Results: {passed}/{len(test_results)} tests passed")

if failed > 0:
    print()
    print("Some tests failed. Please review errors above.")
    sys.exit(1)
else:
    print()
    print("✓ All functional tests passed!")
    print("The core KooMesh functionality is working correctly.")
    sys.exit(0)
