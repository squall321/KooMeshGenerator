"""
LS-DYNA Compatibility Checker Demo
===================================

This example demonstrates the LS-DYNA compatibility checking features
added in [012]:

1. Valid mesh compatibility check
2. Invalid mesh detection and reporting
3. ID range validation
4. Node count validation
5. ID renumbering functionality
6. Custom compatibility criteria
7. Detailed compatibility reports

The checker validates:
- Node ID ranges (1 to 99,999,999)
- Element ID ranges (1 to 99,999,999)
- Element node counts (matching element type)
- Undefined node references
- Coordinate ranges
"""

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.lsdyna_compatibility import (
    LSDynaCompatibilityChecker,
    MAX_NODE_ID,
    MAX_ELEMENT_ID
)


def create_valid_mesh():
    """Create a valid mesh for demonstration"""
    print("\nCreating valid mesh...")
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 3x3x3 grid of hexahedral elements
    for ix in range(3):
        for iy in range(3):
            for iz in range(3):
                coords = [
                    [ix, iy, iz],
                    [ix+1, iy, iz],
                    [ix+1, iy+1, iz],
                    [ix, iy+1, iz],
                    [ix, iy, iz+1],
                    [ix+1, iy, iz+1],
                    [ix+1, iy+1, iz+1],
                    [ix, iy+1, iz+1],
                ]
                node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
                mesh.add_element(node_ids)

    print(f"  Created mesh with {mesh.num_nodes()} nodes and {mesh.num_elements()} elements")
    return mesh


def create_invalid_mesh():
    """Create a mesh with various compatibility issues"""
    print("\nCreating mesh with compatibility issues...")
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add some valid nodes
    mesh.add_node(0.0, 0.0, 0.0)
    mesh.add_node(1.0, 0.0, 0.0)

    # Issue 1: Node ID below minimum (0)
    mesh.nodes[0] = Node(0, 2.0, 0.0, 0.0)

    # Issue 2: Node ID above maximum
    if MAX_NODE_ID < 1000000000:  # Safety check
        mesh.nodes[MAX_NODE_ID + 1] = Node(MAX_NODE_ID + 1, 3.0, 0.0, 0.0)

    # Issue 3: Element with undefined nodes
    elem = Element.__new__(Element)
    elem.id = 1
    elem.type = ElementType.HEX8
    elem.nodes = [999, 1000, 1001, 1002, 1003, 1004, 1005, 1006]  # Non-existent
    elem.metadata = {}
    mesh.elements[1] = elem

    print(f"  Created mesh with {mesh.num_nodes()} nodes and {mesh.num_elements()} elements")
    print(f"  (Contains multiple compatibility issues)")
    return mesh


def demo_valid_mesh_check():
    """Demonstrate checking a valid mesh"""
    print("\n" + "="*70)
    print("Demo 1: Valid Mesh Compatibility Check")
    print("="*70)

    mesh = create_valid_mesh()
    checker = LSDynaCompatibilityChecker()

    print("\nPerforming compatibility check...")
    report = checker.check_mesh(mesh)

    print(report.summary())

    if report.is_valid():
        print("\n✓ Mesh is compatible with LS-DYNA format")
    else:
        print("\n✗ Mesh has compatibility issues")


def demo_invalid_mesh_detection():
    """Demonstrate detection of invalid mesh"""
    print("\n" + "="*70)
    print("Demo 2: Invalid Mesh Detection")
    print("="*70)

    mesh = create_invalid_mesh()
    checker = LSDynaCompatibilityChecker()

    print("\nPerforming compatibility check...")
    report = checker.check_mesh(mesh)

    print(report.summary())

    if not report.is_valid():
        print(f"\n✗ Found {report.num_errors} compatibility errors")
        print("\nDetailed Issues:")
        print("-" * 70)
        for i, issue in enumerate(report.issues[:5], 1):
            print(f"\n{i}. [{issue.category.upper()}] {issue.severity.upper()}")
            print(f"   {issue.message}")
            if issue.details:
                print(f"   Details: {issue.details}")


def demo_id_range_validation():
    """Demonstrate ID range validation"""
    print("\n" + "="*70)
    print("Demo 3: ID Range Validation")
    print("="*70)

    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes with extreme IDs
    print("\nTesting Node ID ranges...")

    # Valid IDs
    mesh.add_node(0.0, 0.0, 0.0)  # Gets ID 1
    print(f"  Valid node ID: 1")

    # Invalid ID (manually added)
    mesh.nodes[0] = Node(0, 1.0, 0.0, 0.0)
    print(f"  Invalid node ID: 0 (below minimum of 1)")

    checker = LSDynaCompatibilityChecker()
    report = checker.check_mesh(mesh)

    print(f"\nValidation Results:")
    print(f"  Errors: {report.num_errors}")
    print(f"  Warnings: {report.num_warnings}")

    for issue in report.issues:
        if 'node' in issue.category.lower():
            print(f"  - {issue.message}")


def demo_id_renumbering():
    """Demonstrate ID renumbering functionality"""
    print("\n" + "="*70)
    print("Demo 4: ID Renumbering")
    print("="*70)

    mesh = create_valid_mesh()

    print(f"\nOriginal ID ranges:")
    print(f"  Node IDs: {min(mesh.nodes.keys())} - {max(mesh.nodes.keys())}")
    print(f"  Element IDs: {min(mesh.elements.keys())} - {max(mesh.elements.keys())}")

    checker = LSDynaCompatibilityChecker()

    # Renumber nodes starting from 100
    print(f"\nRenumbering nodes starting from 100...")
    node_mapping = checker.fix_node_ids(mesh, start_id=100)
    print(f"  Remapped {len(node_mapping)} nodes")
    print(f"  New node ID range: {min(mesh.nodes.keys())} - {max(mesh.nodes.keys())}")

    # Renumber elements starting from 1000
    print(f"\nRenumbering elements starting from 1000...")
    elem_mapping = checker.fix_element_ids(mesh, start_id=1000)
    print(f"  Remapped {len(elem_mapping)} elements")
    print(f"  New element ID range: {min(mesh.elements.keys())} - {max(mesh.elements.keys())}")

    # Verify compatibility
    report = checker.check_mesh(mesh)
    print(f"\nCompatibility after renumbering:")
    print(f"  Status: {'✓ COMPATIBLE' if report.is_valid() else '✗ INCOMPATIBLE'}")
    print(f"  Errors: {report.num_errors}")


def demo_custom_criteria():
    """Demonstrate custom compatibility criteria"""
    print("\n" + "="*70)
    print("Demo 5: Custom Compatibility Criteria")
    print("="*70)

    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes with moderately high IDs
    for i in range(10):
        mesh.add_node(float(i), 0.0, 0.0)

    # Renumber to have high IDs
    checker = LSDynaCompatibilityChecker()
    checker.fix_node_ids(mesh, start_id=50000000)

    print(f"\nMesh node ID range: {min(mesh.nodes.keys())} - {max(mesh.nodes.keys())}")

    # Check with default criteria (max 99,999,999)
    print("\nDefault Criteria (max_node_id = 99,999,999):")
    default_checker = LSDynaCompatibilityChecker()
    default_report = default_checker.check_mesh(mesh)
    print(f"  Compatible: {'✓ Yes' if default_report.is_valid() else '✗ No'}")
    print(f"  Errors: {default_report.num_errors}")

    # Check with strict criteria (max 10,000,000)
    print("\nStrict Criteria (max_node_id = 10,000,000):")
    strict_checker = LSDynaCompatibilityChecker(
        max_node_id=10000000,
        max_element_id=10000000,
        strict_mode=True
    )
    strict_report = strict_checker.check_mesh(mesh)
    print(f"  Compatible: {'✓ Yes' if strict_report.is_valid() else '✗ No'}")
    print(f"  Errors: {strict_report.num_errors}")

    if strict_report.num_errors > 0:
        print(f"\n  Issues detected:")
        for issue in strict_report.issues[:3]:
            print(f"    - {issue.message}")


def demo_element_type_validation():
    """Demonstrate element type validation"""
    print("\n" + "="*70)
    print("Demo 6: Element Type Validation")
    print("="*70)

    print("\nSupported element types in LS-DYNA:")
    supported_types = [
        ("TET4", "4-node tetrahedral", 4),
        ("TET10", "10-node tetrahedral", 10),
        ("HEX8", "8-node hexahedral", 8),
        ("HEX20", "20-node hexahedral", 20),
        ("HEX27", "27-node hexahedral", 27),
        ("PRISM6", "6-node prism/wedge", 6),
        ("PYRAMID5", "5-node pyramid", 5),
    ]

    for code, name, node_count in supported_types:
        print(f"  {code:10s} - {name:25s} ({node_count} nodes)")

    print("\nValidating element node counts...")

    # Create a valid HEX8 mesh
    mesh = MeshData(element_type=ElementType.HEX8)
    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]
    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
    mesh.add_element(node_ids)

    checker = LSDynaCompatibilityChecker()
    report = checker.check_mesh(mesh)

    print(f"\nHEX8 element with {len(node_ids)} nodes:")
    print(f"  Compatible: {'✓ Yes' if report.is_valid() else '✗ No'}")


def demo_coordinate_validation():
    """Demonstrate coordinate range validation"""
    print("\n" + "="*70)
    print("Demo 7: Coordinate Range Validation")
    print("="*70)

    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes with various coordinate magnitudes
    test_coords = [
        (0.0, 0.0, 0.0, "Normal"),
        (1000.0, 1000.0, 1000.0, "Large"),
        (1e10, 1e10, 1e10, "Very Large"),
        (1e20, 0.0, 0.0, "Extreme (may cause warning)"),
    ]

    print("\nTesting coordinate ranges:")
    for x, y, z, label in test_coords:
        mesh.add_node(x, y, z)
        print(f"  {label:30s}: ({x:.2e}, {y:.2e}, {z:.2e})")

    checker = LSDynaCompatibilityChecker()
    report = checker.check_mesh(mesh)

    print(f"\nValidation Results:")
    print(f"  Errors: {report.num_errors}")
    print(f"  Warnings: {report.num_warnings}")

    if report.num_warnings > 0:
        print(f"\n  Coordinate warnings:")
        for issue in report.issues:
            if issue.category == 'coordinate_range':
                print(f"    - {issue.message}")


def main():
    """Run all demonstrations"""
    print("="*70)
    print("KooMeshGenerator: LS-DYNA Compatibility Checker Demo")
    print("="*70)
    print("\nThis demo showcases LS-DYNA compatibility checking features ([012]):")
    print("  • Node/Element ID validation")
    print("  • ID range checking")
    print("  • Element type validation")
    print("  • Node count verification")
    print("  • Coordinate range validation")
    print("  • ID renumbering")
    print("  • Custom compatibility criteria")

    # Run all demonstrations
    demo_valid_mesh_check()
    demo_invalid_mesh_detection()
    demo_id_range_validation()
    demo_id_renumbering()
    demo_custom_criteria()
    demo_element_type_validation()
    demo_coordinate_validation()

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Features:")
    print("  • Comprehensive validation against LS-DYNA constraints")
    print("  • Detailed error reporting with categories and severity")
    print("  • Automatic ID renumbering for compliance")
    print("  • Customizable ID range limits")
    print("  • Prevention of runtime errors in LS-DYNA solver")
    print("\nCommon Issues Detected:")
    print("  • Node/Element IDs out of range (1 to 99,999,999)")
    print("  • Duplicate IDs")
    print("  • Wrong node count per element type")
    print("  • Undefined node references")
    print("  • Extreme coordinate values")


if __name__ == '__main__':
    main()
