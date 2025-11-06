"""
PLY and OBJ Export Demo
========================

Demonstrates exporting meshes to PLY and OBJ formats for 3D visualization.

Author: KooMeshGenerator Team
"""

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.ply_writer import export_to_ply
from koomesh.export.obj_writer import export_to_obj


def demo_ply_ascii():
    """Export to PLY ASCII format"""
    print("\n" + "="*60)
    print("Demo 1: PLY ASCII Export")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)
    
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.5, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.5, 0.5, 1.0))
    mesh.add_element(node_ids)

    export_to_ply(mesh, "ply_obj_examples/tet_ascii.ply", ascii_format=True)
    print("✓ Exported to ply_obj_examples/tet_ascii.ply")
    print("  - ASCII format (human readable)")


def demo_ply_binary():
    """Export to PLY binary format"""
    print("\n" + "="*60)
    print("Demo 2: PLY Binary Export")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    export_to_ply(mesh, "ply_obj_examples/cube_binary.ply", ascii_format=False)
    print("✓ Exported to ply_obj_examples/cube_binary.ply")
    print("  - Binary format (compact)")


def demo_obj_basic():
    """Export to OBJ format"""
    print("\n" + "="*60)
    print("Demo 3: OBJ Export")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)
    
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.5, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.5, 0.5, 1.0))
    mesh.add_element(node_ids)

    export_to_obj(mesh, "ply_obj_examples/tet.obj", "Tetrahedron")
    print("✓ Exported to ply_obj_examples/tet.obj")
    print("  - Object name: Tetrahedron")
    print("  - Includes vertex normals")


def demo_complex_mesh():
    """Export complex mesh"""
    print("\n" + "="*60)
    print("Demo 4: Complex Mesh Export")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 3x3x3 grid
    node_ids = []
    for i in range(4):
        for j in range(4):
            for k in range(4):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    for i in range(3):
        for j in range(3):
            for k in range(3):
                n000 = i * 16 + j * 4 + k
                n100 = (i+1) * 16 + j * 4 + k
                n010 = i * 16 + (j+1) * 4 + k
                n110 = (i+1) * 16 + (j+1) * 4 + k
                n001 = i * 16 + j * 4 + (k+1)
                n101 = (i+1) * 16 + j * 4 + (k+1)
                n011 = i * 16 + (j+1) * 4 + (k+1)
                n111 = (i+1) * 16 + (j+1) * 4 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    print(f"Mesh: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")

    export_to_ply(mesh, "ply_obj_examples/grid3x3x3.ply")
    export_to_obj(mesh, "ply_obj_examples/grid3x3x3.obj", "Grid3x3x3")

    print("✓ Exported to PLY and OBJ formats")


def demo_surface_extraction():
    """Demonstrate surface extraction"""
    print("\n" + "="*60)
    print("Demo 5: Surface Extraction")
    print("="*60)

    # Prism mesh
    mesh = MeshData(element_type=ElementType.PRISM6)

    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.5, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
    node_ids.append(mesh.add_node(0.5, 1.0, 1.0))
    mesh.add_element(node_ids)

    export_to_obj(mesh, "ply_obj_examples/prism.obj", "Prism")
    print("✓ Prism exported with triangulated surfaces")
    print("  - 2 triangular faces + 3 quad faces")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PLY AND OBJ EXPORT DEMONSTRATIONS")
    print("="*60)

    demo_ply_ascii()
    demo_ply_binary()
    demo_obj_basic()
    demo_complex_mesh()
    demo_surface_extraction()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
    print("\nOutput files:")
    print("  - ply_obj_examples/tet_ascii.ply (ASCII)")
    print("  - ply_obj_examples/cube_binary.ply (Binary)")
    print("  - ply_obj_examples/tet.obj")
    print("  - ply_obj_examples/grid3x3x3.ply")
    print("  - ply_obj_examples/grid3x3x3.obj")
    print("  - ply_obj_examples/prism.obj")
    print("\nFormats:")
    print("  PLY: Point cloud and polygon format (3D scanning)")
    print("  OBJ: Universal 3D format (widely supported)")
