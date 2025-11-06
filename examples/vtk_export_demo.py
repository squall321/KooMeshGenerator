"""
VTK Export Demo
================

This demo shows how to export meshes to VTK formats for visualization.

VTK formats supported:
1. .vtu (VTK XML Unstructured Grid) - Modern XML-based format
2. .vtk (Legacy VTK format) - ASCII format for compatibility

Features demonstrated:
1. Basic HEX8 mesh export (XML format)
2. TET4 mesh export (Legacy format)
3. Mesh with scalar data (temperature field)
4. Mesh with vector data (displacement field)
5. Binary encoding (XML format)
6. Multi-field data export
7. All element types (HEX8, TET4, PRISM6, PYRAMID5)

VTK files can be opened with:
- ParaView (https://www.paraview.org/)
- VisIt (https://visit.llnl.gov/)
- Mayavi
- Any VTK-based visualization tool
"""

from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.vtk_writer import VTKWriter
import math


# Create output directory
output_dir = Path("vtk_export_examples")
output_dir.mkdir(exist_ok=True)


# ============================================================================
# Demo 1: Basic HEX8 Mesh (XML Format)
# ============================================================================

def demo_1_basic_hex8():
    """Export a basic HEX8 mesh in XML format (.vtu)"""
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Mesh (XML Format)")
    print("="*70)

    # Create mesh with 2x2x2 elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes (3x3x3 grid)
    node_id = 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                x, y, z = float(i) * 10.0, float(j) * 10.0, float(k) * 10.0
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 8 elements (2x2x2 grid)
    elem_id = 1
    for i in range(2):
        for j in range(2):
            for k in range(2):
                # Calculate corner nodes for this element
                n1 = i * 9 + j * 3 + k + 1
                n2 = n1 + 1
                n3 = n1 + 3
                n4 = n1 + 4
                n5 = n1 + 9
                n6 = n5 + 1
                n7 = n5 + 3
                n8 = n5 + 4

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n4, n3, n5, n6, n8, n7]
                )
                elem_id += 1

    # Write to VTU file
    output_file = output_dir / "demo_1_basic_hex8.vtu"
    with VTKWriter(output_file, format='xml', encoding='ascii') as writer:
        writer.write_mesh(mesh)

    print(f"✓ Created: {output_file}")
    print(f"  - Format: VTK XML (.vtu)")
    print(f"  - Encoding: ASCII")
    print(f"  - Nodes: {mesh.num_nodes()}")
    print(f"  - Elements: {mesh.num_elements()}")
    print(f"  - Element Type: HEX8")
    print(f"  - Open with: ParaView, VisIt")


# ============================================================================
# Demo 2: TET4 Mesh (Legacy Format)
# ============================================================================

def demo_2_tet4_legacy():
    """Export TET4 mesh in legacy format (.vtk)"""
    print("\n" + "="*70)
    print("Demo 2: TET4 Mesh (Legacy Format)")
    print("="*70)

    # Create TET4 mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes in a simple pattern
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 10.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 5.0, 10.0, 0.0)
    mesh.nodes[4] = Node(4, 5.0, 5.0, 10.0)
    mesh.nodes[5] = Node(5, 15.0, 5.0, 5.0)
    mesh.nodes[6] = Node(6, 10.0, 10.0, 5.0)

    # Create 4 tet elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 5, 3, 4])
    mesh.elements[3] = Element(3, ElementType.TET4, [3, 5, 6, 4])
    mesh.elements[4] = Element(4, ElementType.TET4, [2, 5, 6, 3])

    # Write to VTK legacy file
    output_file = output_dir / "demo_2_tet4_legacy.vtk"
    with VTKWriter(output_file, format='legacy') as writer:
        writer.write_mesh(mesh)

    print(f"✓ Created: {output_file}")
    print(f"  - Format: VTK Legacy (.vtk)")
    print(f"  - Encoding: ASCII")
    print(f"  - Nodes: {mesh.num_nodes()}")
    print(f"  - Elements: {mesh.num_elements()}")
    print(f"  - Element Type: TET4")
    print(f"  - Compatible with older VTK versions")


# ============================================================================
# Demo 3: Mesh with Scalar Data (Temperature Field)
# ============================================================================

def demo_3_scalar_data():
    """Export mesh with scalar data field"""
    print("\n" + "="*70)
    print("Demo 3: Mesh with Scalar Data (Temperature Field)")
    print("="*70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x2x2 grid
    node_id = 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create single element
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 5, 4, 10, 11, 14, 13])

    # Create temperature field (varies with z-coordinate)
    temperature = []
    for node_id in sorted(mesh.nodes.keys()):
        node = mesh.nodes[node_id]
        # Temperature increases with height
        temp = 20.0 + node.z * 50.0
        temperature.append(temp)

    scalar_data = {'Temperature': temperature}

    # Write to file
    output_file = output_dir / "demo_3_scalar_temperature.vtu"
    with VTKWriter(output_file) as writer:
        writer.write_mesh(mesh, scalar_data=scalar_data)

    print(f"✓ Created: {output_file}")
    print(f"  - Scalar field: Temperature")
    print(f"  - Range: 20°C to 120°C")
    print(f"  - Visualize with: ParaView color mapping")
    print(f"  - Try: Apply 'Warp By Scalar' filter in ParaView")


# ============================================================================
# Demo 4: Mesh with Vector Data (Displacement Field)
# ============================================================================

def demo_4_vector_data():
    """Export mesh with vector data field"""
    print("\n" + "="*70)
    print("Demo 4: Mesh with Vector Data (Displacement Field)")
    print("="*70)

    # Create beam-like mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes along beam (5 elements long)
    node_id = 1
    for i in range(6):
        for j in range(2):
            for k in range(2):
                x = float(i) * 10.0
                y = float(j) * 2.0
                z = float(k) * 2.0
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 5 elements
    for i in range(5):
        elem_id = i + 1
        base = i * 4 + 1
        nodes = [
            base, base + 1, base + 3, base + 2,
            base + 4, base + 5, base + 7, base + 6
        ]
        mesh.elements[elem_id] = Element(elem_id, ElementType.HEX8, nodes)

    # Create displacement field (cantilever beam deflection)
    displacement = []
    for node_id in sorted(mesh.nodes.keys()):
        node = mesh.nodes[node_id]
        # Parabolic deflection pattern
        x_normalized = node.x / 50.0  # Normalize to 0-1
        dy = 0.0
        dz = -5.0 * x_normalized ** 2  # Downward deflection
        dx = 0.5 * x_normalized  # Slight elongation
        displacement.append([dx, dy, dz])

    vector_data = {'Displacement': displacement}

    # Write to file
    output_file = output_dir / "demo_4_vector_displacement.vtu"
    with VTKWriter(output_file) as writer:
        writer.write_mesh(mesh, vector_data=vector_data)

    print(f"✓ Created: {output_file}")
    print(f"  - Vector field: Displacement")
    print(f"  - Simulates: Cantilever beam deflection")
    print(f"  - Visualize with: ParaView 'Glyph' filter")
    print(f"  - Try: Apply 'Warp By Vector' filter")


# ============================================================================
# Demo 5: Binary Encoding (Faster, Smaller Files)
# ============================================================================

def demo_5_binary_encoding():
    """Export mesh with binary encoding"""
    print("\n" + "="*70)
    print("Demo 5: Binary Encoding (Compact Format)")
    print("="*70)

    # Create larger mesh for size comparison
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 5x5x5 grid
    node_id = 1
    for i in range(6):
        for j in range(6):
            for k in range(6):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 125 elements (5x5x5)
    elem_id = 1
    for i in range(5):
        for j in range(5):
            for k in range(5):
                n1 = i * 36 + j * 6 + k + 1
                n2 = n1 + 1
                n3 = n1 + 6
                n4 = n1 + 7
                n5 = n1 + 36
                n6 = n5 + 1
                n7 = n5 + 6
                n8 = n5 + 7

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n4, n3, n5, n6, n8, n7]
                )
                elem_id += 1

    # Write ASCII version
    output_ascii = output_dir / "demo_5_ascii.vtu"
    with VTKWriter(output_ascii, encoding='ascii') as writer:
        writer.write_mesh(mesh)

    # Write binary version
    output_binary = output_dir / "demo_5_binary.vtu"
    with VTKWriter(output_binary, encoding='binary') as writer:
        writer.write_mesh(mesh)

    # Compare file sizes
    size_ascii = output_ascii.stat().st_size / 1024
    size_binary = output_binary.stat().st_size / 1024

    print(f"✓ Created: {output_ascii}")
    print(f"  - Encoding: ASCII")
    print(f"  - File size: {size_ascii:.1f} KB")
    print(f"\n✓ Created: {output_binary}")
    print(f"  - Encoding: Binary (Base64)")
    print(f"  - File size: {size_binary:.1f} KB")
    print(f"\n  - Size reduction: {(1 - size_binary/size_ascii)*100:.1f}%")
    print(f"  - Binary is faster to read/write")


# ============================================================================
# Demo 6: Multi-Field Data
# ============================================================================

def demo_6_multifield():
    """Export mesh with multiple scalar and vector fields"""
    print("\n" + "="*70)
    print("Demo 6: Multi-Field Data Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes
    node_id = 1
    for i in range(4):
        for j in range(4):
            for k in range(4):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create elements
    elem_id = 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                n1 = i * 16 + j * 4 + k + 1
                n2 = n1 + 1
                n3 = n1 + 4
                n4 = n1 + 5
                n5 = n1 + 16
                n6 = n5 + 1
                n7 = n5 + 4
                n8 = n5 + 5

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n4, n3, n5, n6, n8, n7]
                )
                elem_id += 1

    # Create multiple scalar fields
    temperature = []
    pressure = []
    density = []

    # Create multiple vector fields
    velocity = []
    stress = []

    for node_id in sorted(mesh.nodes.keys()):
        node = mesh.nodes[node_id]

        # Scalar fields
        temperature.append(300.0 + node.z * 20.0)
        pressure.append(101325.0 + node.z * 1000.0)
        density.append(1.2 + node.z * 0.1)

        # Vector fields
        velocity.append([node.x * 0.5, node.y * 0.3, node.z * 0.2])
        stress.append([node.x * 100, node.y * 100, node.z * 100])

    scalar_data = {
        'Temperature': temperature,
        'Pressure': pressure,
        'Density': density
    }

    vector_data = {
        'Velocity': velocity,
        'Stress': stress
    }

    # Write to file
    output_file = output_dir / "demo_6_multifield.vtu"
    with VTKWriter(output_file) as writer:
        writer.write_mesh(mesh, scalar_data=scalar_data, vector_data=vector_data)

    print(f"✓ Created: {output_file}")
    print(f"  - Scalar fields: Temperature, Pressure, Density")
    print(f"  - Vector fields: Velocity, Stress")
    print(f"  - ParaView: Use 'Color By' dropdown to switch fields")
    print(f"  - Try: Create derived fields (e.g., speed = magnitude(Velocity))")


# ============================================================================
# Demo 7: All Element Types
# ============================================================================

def demo_7_all_element_types():
    """Demonstrate all supported element types"""
    print("\n" + "="*70)
    print("Demo 7: All Element Types")
    print("="*70)

    # HEX8
    hex8_mesh = MeshData(element_type=ElementType.HEX8)
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)
    ], start=1):
        hex8_mesh.nodes[i] = Node(i, x, y, z)
    hex8_mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

    # TET4
    tet4_mesh = MeshData(element_type=ElementType.TET4)
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (1, 0, 0), (0.5, 1, 0), (0.5, 0.5, 1)
    ], start=1):
        tet4_mesh.nodes[i] = Node(i, x, y, z)
    tet4_mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])

    # PRISM6
    prism_mesh = MeshData(element_type=ElementType.PRISM6)
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (1, 0, 0), (0.5, 1, 0),
        (0, 0, 1), (1, 0, 1), (0.5, 1, 1)
    ], start=1):
        prism_mesh.nodes[i] = Node(i, x, y, z)
    prism_mesh.elements[1] = Element(1, ElementType.PRISM6, [1, 2, 3, 4, 5, 6])

    # PYRAMID5
    pyramid_mesh = MeshData(element_type=ElementType.PYRAMID5)
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0.5, 0.5, 1)
    ], start=1):
        pyramid_mesh.nodes[i] = Node(i, x, y, z)
    pyramid_mesh.elements[1] = Element(1, ElementType.PYRAMID5, [1, 2, 3, 4, 5])

    # Export all
    meshes = [
        (hex8_mesh, "HEX8", 12),
        (tet4_mesh, "TET4", 10),
        (prism_mesh, "PRISM6", 13),
        (pyramid_mesh, "PYRAMID5", 14)
    ]

    for mesh, elem_type, vtk_id in meshes:
        output_file = output_dir / f"demo_7_{elem_type.lower()}.vtu"
        VTKWriter.write_simple(mesh, str(output_file))
        print(f"  ✓ {elem_type}: {output_file.name} (VTK type {vtk_id})")

    print("\n  All element types exported successfully!")
    print("  Open all files in ParaView to compare geometries")


# ============================================================================
# Main: Run All Demos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VTK EXPORT DEMONSTRATION")
    print("="*70)
    print("\nThis demo creates 7 sets of VTK files showing various features.")
    print(f"Output directory: {output_dir.absolute()}")

    # Run all demos
    demo_1_basic_hex8()
    demo_2_tet4_legacy()
    demo_3_scalar_data()
    demo_4_vector_data()
    demo_5_binary_encoding()
    demo_6_multifield()
    demo_7_all_element_types()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Created VTK files in {output_dir}/")
    print("\nKey Features Demonstrated:")
    print("  • XML (.vtu) and Legacy (.vtk) formats")
    print("  • ASCII and Binary encoding")
    print("  • Scalar data fields (Temperature, Pressure, Density)")
    print("  • Vector data fields (Displacement, Velocity, Stress)")
    print("  • All element types (HEX8, TET4, PRISM6, PYRAMID5)")
    print("  • Multi-field data export")
    print("\nVisualization Tools:")
    print("  • ParaView: https://www.paraview.org/")
    print("  • VisIt: https://visit.llnl.gov/")
    print("  • Mayavi: https://docs.enthought.com/mayavi/")
    print("\nParaView Quick Tips:")
    print("  1. Open .vtu or .vtk file")
    print("  2. Click 'Apply' to load mesh")
    print("  3. Use 'Color By' to visualize scalar/vector fields")
    print("  4. Apply filters: Warp By Vector, Glyph, Streamlines, etc.")
    print("  5. Save state for reproducible visualizations")
    print("\n" + "="*70)
