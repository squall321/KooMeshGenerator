"""
Elmer FEM Export Demo
=====================

Demonstrates exporting meshes to Elmer FEM format for multiphysics simulations.

Author: KooMeshGenerator Team
"""

from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.elmer_writer import ElmerWriter, export_to_elmer


def demo_basic_hex_export():
    """Export a simple hex mesh to Elmer format"""
    print("\n" + "="*60)
    print("Demo 1: Basic Hex Mesh Export to Elmer")
    print("="*60)

    # Create a simple cube mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    # Export
    output_dir = "elmer_examples/basic_hex"
    writer = ElmerWriter(output_dir)
    writer.write_mesh(mesh)

    print(f"✓ Exported hex mesh to {output_dir}/")
    print(f"  - mesh.header: Header information")
    print(f"  - mesh.nodes: {len(mesh.nodes)} nodes")
    print(f"  - mesh.elements: {len(mesh.elements)} elements")
    print(f"  - mesh.boundary: Boundary elements")


def demo_tet_mesh_export():
    """Export tetrahedral mesh to Elmer"""
    print("\n" + "="*60)
    print("Demo 2: Tetrahedral Mesh Export")
    print("="*60)

    # Create tet mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Create multiple tets
    for x in range(3):
        for y in range(3):
            node_ids = []
            node_ids.append(mesh.add_node(float(x), float(y), 0.0))
            node_ids.append(mesh.add_node(float(x+1), float(y), 0.0))
            node_ids.append(mesh.add_node(float(x), float(y+1), 0.0))
            node_ids.append(mesh.add_node(float(x+0.5), float(y+0.5), 1.0))
            mesh.add_element(node_ids)

    output_dir = "elmer_examples/tet_mesh"
    export_to_elmer(mesh, output_dir)

    print(f"✓ Exported tet mesh to {output_dir}/")
    print(f"  - {len(mesh.elements)} TET4 elements")
    print(f"  - Element type code: 504")


def demo_multi_element_mesh():
    """Export mesh with multiple elements"""
    print("\n" + "="*60)
    print("Demo 3: Multi-Element Hex Mesh")
    print("="*60)

    # Create 2x2x2 grid of hex elements
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    # Create 8 hex elements
    for i in range(2):
        for j in range(2):
            for k in range(2):
                n000 = i * 9 + j * 3 + k
                n100 = (i+1) * 9 + j * 3 + k
                n010 = i * 9 + (j+1) * 3 + k
                n110 = (i+1) * 9 + (j+1) * 3 + k
                n001 = i * 9 + j * 3 + (k+1)
                n101 = (i+1) * 9 + j * 3 + (k+1)
                n011 = i * 9 + (j+1) * 3 + (k+1)
                n111 = (i+1) * 9 + (j+1) * 3 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    output_dir = "elmer_examples/multi_hex"
    export_to_elmer(mesh, output_dir)

    print(f"✓ Exported multi-element mesh to {output_dir}/")
    print(f"  - {len(mesh.nodes)} nodes")
    print(f"  - {len(mesh.elements)} HEX8 elements")
    print(f"  - 2x2x2 structured grid")


def demo_prism_mesh():
    """Export prism (wedge) mesh"""
    print("\n" + "="*60)
    print("Demo 4: Prism Mesh Export")
    print("="*60)

    mesh = MeshData(element_type=ElementType.PRISM6)

    # Create prism elements
    for i in range(2):
        node_ids = []
        # Bottom triangle
        node_ids.append(mesh.add_node(float(i), 0.0, 0.0))
        node_ids.append(mesh.add_node(float(i+1), 0.0, 0.0))
        node_ids.append(mesh.add_node(float(i+0.5), 1.0, 0.0))
        # Top triangle
        node_ids.append(mesh.add_node(float(i), 0.0, 1.0))
        node_ids.append(mesh.add_node(float(i+1), 0.0, 1.0))
        node_ids.append(mesh.add_node(float(i+0.5), 1.0, 1.0))
        mesh.add_element(node_ids)

    output_dir = "elmer_examples/prism_mesh"
    export_to_elmer(mesh, output_dir)

    print(f"✓ Exported prism mesh to {output_dir}/")
    print(f"  - {len(mesh.elements)} PRISM6 elements")
    print(f"  - Element type code: 706")


def demo_file_inspection():
    """Show how to inspect Elmer files"""
    print("\n" + "="*60)
    print("Demo 5: Inspecting Elmer Files")
    print("="*60)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.TET4)
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
    mesh.add_element(node_ids)

    output_dir = "elmer_examples/inspect"
    export_to_elmer(mesh, output_dir)

    # Read and display file contents
    output_path = Path(output_dir)

    print(f"\n✓ mesh.header content:")
    print((output_path / "mesh.header").read_text())

    print(f"✓ mesh.nodes content:")
    print((output_path / "mesh.nodes").read_text())

    print(f"✓ mesh.elements content:")
    print((output_path / "mesh.elements").read_text())

    print(f"✓ mesh.boundary content:")
    print((output_path / "mesh.boundary").read_text())


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ELMER FEM EXPORT DEMONSTRATIONS")
    print("="*60)

    demo_basic_hex_export()
    demo_tet_mesh_export()
    demo_multi_element_mesh()
    demo_prism_mesh()
    demo_file_inspection()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
    print("\nOutput directories:")
    print("  - elmer_examples/basic_hex/")
    print("  - elmer_examples/tet_mesh/")
    print("  - elmer_examples/multi_hex/")
    print("  - elmer_examples/prism_mesh/")
    print("  - elmer_examples/inspect/")
    print("\nUse these files with Elmer FEM for multiphysics simulations!")
