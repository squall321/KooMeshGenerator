"""
Mesh Partitioning Demo
======================

Demonstrates mesh splitting and partitioning for parallel processing.

Author: KooMeshGenerator Team
"""

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_partition import (
    split_mesh_by_plane,
    partition_mesh,
    extract_mesh_region
)
from koomesh.utils.mesh_info import print_mesh_info


def demo_split_by_plane():
    """Split mesh by plane"""
    print("\n" + "="*60)
    print("Demo 1: Split Mesh by Plane")
    print("="*60)

    # Create simple hex mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x2x2 grid
    node_ids = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

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

    print_mesh_info(mesh, "Original Mesh")

    # Split at X=1.0
    left, right = split_mesh_by_plane(mesh, 'x', 1.0)

    print_mesh_info(left, "Left Half (X < 1.0)")
    print_mesh_info(right, "Right Half (X >= 1.0)")

    print(f"\nVerification:")
    print(f"  Original: {len(mesh.elements)} elements")
    print(f"  Left + Right: {len(left.elements)} + {len(right.elements)} = {len(left.elements) + len(right.elements)}")


def demo_split_different_axes():
    """Split along different axes"""
    print("\n" + "="*60)
    print("Demo 2: Split Along Different Axes")
    print("="*60)

    # Create 3x2x1 mesh
    mesh = MeshData(element_type=ElementType.TET4)

    for i in range(3):
        for j in range(2):
            node_ids = []
            node_ids.append(mesh.add_node(float(i), float(j), 0.0))
            node_ids.append(mesh.add_node(float(i+1), float(j), 0.0))
            node_ids.append(mesh.add_node(float(i), float(j+1), 0.0))
            node_ids.append(mesh.add_node(float(i+0.5), float(j+0.5), 1.0))
            mesh.add_element(node_ids)

    print(f"Original mesh: {len(mesh.elements)} elements")

    # Split along X
    left_x, right_x = split_mesh_by_plane(mesh, 'x', 1.5)
    print(f"\nSplit along X at 1.5:")
    print(f"  Left:  {len(left_x.elements)} elements")
    print(f"  Right: {len(right_x.elements)} elements")

    # Split along Y
    bottom_y, top_y = split_mesh_by_plane(mesh, 'y', 1.0)
    print(f"\nSplit along Y at 1.0:")
    print(f"  Bottom: {len(bottom_y.elements)} elements")
    print(f"  Top:    {len(top_y.elements)} elements")

    # Split along Z
    low_z, high_z = split_mesh_by_plane(mesh, 'z', 0.5)
    print(f"\nSplit along Z at 0.5:")
    print(f"  Low:  {len(low_z.elements)} elements")
    print(f"  High: {len(high_z.elements)} elements")


def demo_partition_into_parts():
    """Partition mesh into multiple parts"""
    print("\n" + "="*60)
    print("Demo 3: Partition into Multiple Parts")
    print("="*60)

    # Create longer mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(5):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    for i in range(4):
        for j in range(1):
            for k in range(1):
                n000 = i * 4 + j * 2 + k
                n100 = (i+1) * 4 + j * 2 + k
                n010 = i * 4 + (j+1) * 2 + k
                n110 = (i+1) * 4 + (j+1) * 2 + k
                n001 = i * 4 + j * 2 + (k+1)
                n101 = (i+1) * 4 + j * 2 + (k+1)
                n011 = i * 4 + (j+1) * 2 + (k+1)
                n111 = (i+1) * 4 + (j+1) * 2 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    print(f"Original mesh: {len(mesh.elements)} elements")

    # Partition into 4 parts
    parts = partition_mesh(mesh, 4, 'x')

    print(f"\nPartitioned into {len(parts)} parts along X:")
    for i, part in enumerate(parts):
        print(f"  Part {i+1}: {len(part.elements)} elements, {len(part.nodes)} nodes")

    total = sum(len(p.elements) for p in parts)
    print(f"\nTotal elements in all parts: {total}")
    print(f"Original elements: {len(mesh.elements)}")
    print(f"✓ All elements preserved: {total == len(mesh.elements)}")


def demo_extract_region():
    """Extract mesh region within bounding box"""
    print("\n" + "="*60)
    print("Demo 4: Extract Mesh Region")
    print("="*60)

    # Create large mesh
    mesh = MeshData(element_type=ElementType.TET4)

    for i in range(10):
        for j in range(10):
            node_ids = []
            node_ids.append(mesh.add_node(float(i), float(j), 0.0))
            node_ids.append(mesh.add_node(float(i+1), float(j), 0.0))
            node_ids.append(mesh.add_node(float(i), float(j+1), 0.0))
            node_ids.append(mesh.add_node(float(i+0.5), float(j+0.5), 1.0))
            mesh.add_element(node_ids)

    print_mesh_info(mesh, "Full Mesh")

    # Extract center region
    region = extract_mesh_region(mesh, (3.0, 3.0, 0.0), (7.0, 7.0, 1.0))

    print_mesh_info(region, "Extracted Region (3-7, 3-7, 0-1)")

    print(f"\nExtraction ratio: {len(region.elements)}/{len(mesh.elements)} = {100*len(region.elements)/len(mesh.elements):.1f}%")


def demo_parallel_decomposition():
    """Decompose mesh for parallel processing"""
    print("\n" + "="*60)
    print("Demo 5: Parallel Domain Decomposition")
    print("="*60)

    # Create 3D mesh
    mesh = MeshData(element_type=ElementType.HEX8)

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

    print(f"Full mesh: {len(mesh.elements)} elements")

    # Decompose for 8 processors (2x2x2)
    print(f"\nDecomposing for 8 processors (2x2x2 decomposition)...")

    # First split in X
    x_parts = partition_mesh(mesh, 2, 'x')

    # Then split each in Y
    xy_parts = []
    for x_part in x_parts:
        xy_parts.extend(partition_mesh(x_part, 2, 'y'))

    # Finally split each in Z
    xyz_parts = []
    for xy_part in xy_parts:
        xyz_parts.extend(partition_mesh(xy_part, 2, 'z'))

    print(f"\nDomain decomposition:")
    for i, part in enumerate(xyz_parts):
        print(f"  Rank {i}: {len(part.elements)} elements, {len(part.nodes)} nodes")

    total = sum(len(p.elements) for p in xyz_parts)
    avg = total / len(xyz_parts)
    print(f"\nLoad balance:")
    print(f"  Average: {avg:.1f} elements/rank")
    print(f"  Min: {min(len(p.elements) for p in xyz_parts)}")
    print(f"  Max: {max(len(p.elements) for p in xyz_parts)}")


def demo_selective_refinement():
    """Extract region for selective refinement"""
    print("\n" + "="*60)
    print("Demo 6: Selective Refinement Region")
    print("="*60)

    # Create base mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(6):
        for j in range(6):
            for k in range(3):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    for i in range(5):
        for j in range(5):
            for k in range(2):
                n000 = i * 18 + j * 3 + k
                n100 = (i+1) * 18 + j * 3 + k
                n010 = i * 18 + (j+1) * 3 + k
                n110 = (i+1) * 18 + (j+1) * 3 + k
                n001 = i * 18 + j * 3 + (k+1)
                n101 = (i+1) * 18 + j * 3 + (k+1)
                n011 = i * 18 + (j+1) * 3 + (k+1)
                n111 = (i+1) * 18 + (j+1) * 3 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    print(f"Base mesh: {len(mesh.elements)} elements")

    # Extract regions for refinement
    coarse_region = extract_mesh_region(mesh, (0, 0, 0), (2, 6, 3))
    fine_region = extract_mesh_region(mesh, (2, 2, 0), (4, 4, 3))
    coarse_region2 = extract_mesh_region(mesh, (4, 0, 0), (6, 6, 3))

    print(f"\nRegion extraction for selective refinement:")
    print(f"  Coarse region 1: {len(coarse_region.elements)} elements")
    print(f"  Fine region (center): {len(fine_region.elements)} elements <- refine here")
    print(f"  Coarse region 2: {len(coarse_region2.elements)} elements")

    print(f"\nWorkflow: Refine the fine region mesh separately,")
    print(f"          then combine with coarse regions.")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MESH PARTITIONING DEMONSTRATIONS")
    print("="*60)

    demo_split_by_plane()
    demo_split_different_axes()
    demo_partition_into_parts()
    demo_extract_region()
    demo_parallel_decomposition()
    demo_selective_refinement()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
    print("\nUse Cases:")
    print("  - Parallel processing: Decompose mesh for MPI domains")
    print("  - Selective refinement: Extract regions for detailed meshing")
    print("  - Load balancing: Partition for distributed computation")
    print("  - Region analysis: Extract and analyze specific zones")
