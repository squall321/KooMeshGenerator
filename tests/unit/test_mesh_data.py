"""
Unit tests for mesh data structures
"""

import pytest
import numpy as np
from koomesh.meshing.mesh_data import (
    MeshData, Node, Element, ElementType
)


def test_node_creation():
    """Test node creation"""
    node = Node(id=1, x=0.0, y=1.0, z=2.0)

    assert node.id == 1
    assert node.x == 0.0
    assert node.y == 1.0
    assert node.z == 2.0

    coords = node.coordinates()
    assert np.allclose(coords, [0.0, 1.0, 2.0])


def test_node_distance():
    """Test node distance calculation"""
    node1 = Node(id=1, x=0.0, y=0.0, z=0.0)
    node2 = Node(id=2, x=3.0, y=4.0, z=0.0)

    distance = node1.distance_to(node2)
    assert abs(distance - 5.0) < 1e-10


def test_element_creation():
    """Test element creation"""
    elem = Element(
        id=1,
        type=ElementType.HEX8,
        nodes=[1, 2, 3, 4, 5, 6, 7, 8],
        part_id=1
    )

    assert elem.id == 1
    assert elem.type == ElementType.HEX8
    assert len(elem.nodes) == 8
    assert elem.part_id == 1


def test_element_validation():
    """Test element validation"""
    # Should raise error for wrong number of nodes
    with pytest.raises(ValueError):
        Element(
            id=1,
            type=ElementType.HEX8,
            nodes=[1, 2, 3, 4],  # Only 4 nodes, should be 8
            part_id=1
        )


def test_element_faces():
    """Test element face extraction"""
    elem = Element(
        id=1,
        type=ElementType.HEX8,
        nodes=[1, 2, 3, 4, 5, 6, 7, 8]
    )

    assert elem.num_faces() == 6

    face0 = elem.get_face_nodes(0)
    assert len(face0) == 4


def test_mesh_data_creation():
    """Test mesh data creation"""
    mesh = MeshData(ElementType.HEX8)

    assert mesh.element_type == ElementType.HEX8
    assert mesh.num_nodes() == 0
    assert mesh.num_elements() == 0


def test_mesh_add_node():
    """Test adding nodes to mesh"""
    mesh = MeshData()

    nid1 = mesh.add_node(0, 0, 0)
    nid2 = mesh.add_node(1, 0, 0)
    nid3 = mesh.add_node(1, 1, 0)

    assert mesh.num_nodes() == 3
    assert nid1 == 1
    assert nid2 == 2
    assert nid3 == 3

    node = mesh.get_node(nid1)
    assert node.x == 0
    assert node.y == 0


def test_mesh_add_element():
    """Test adding elements to mesh"""
    mesh = MeshData(ElementType.HEX8)

    # Add nodes first
    nodes = []
    for i in range(8):
        nid = mesh.add_node(i, i, i)
        nodes.append(nid)

    # Add element
    eid = mesh.add_element(nodes)

    assert mesh.num_elements() == 1
    assert eid == 1

    elem = mesh.get_element(eid)
    assert elem.type == ElementType.HEX8
    assert len(elem.nodes) == 8


def test_mesh_validation():
    """Test mesh validation"""
    mesh = MeshData(ElementType.TET4)

    # Add nodes
    for i in range(4):
        mesh.add_node(i, i, i)

    # Add valid element
    mesh.add_element([1, 2, 3, 4])

    # Should pass validation
    assert mesh.validate()

    # Try to add element with invalid node reference
    with pytest.raises(ValueError):
        mesh.add_element([1, 2, 3, 999])  # Node 999 doesn't exist


def test_mesh_bounding_box():
    """Test mesh bounding box calculation"""
    mesh = MeshData()

    mesh.add_node(0, 0, 0)
    mesh.add_node(10, 0, 0)
    mesh.add_node(0, 5, 0)
    mesh.add_node(0, 0, 3)

    bbox_min, bbox_max = mesh.get_bounding_box()

    assert np.allclose(bbox_min, [0, 0, 0])
    assert np.allclose(bbox_max, [10, 5, 3])


def test_mesh_translate():
    """Test mesh translation"""
    mesh = MeshData()

    mesh.add_node(0, 0, 0)
    mesh.add_node(1, 1, 1)

    mesh.translate(5, 5, 5)

    node1 = mesh.get_node(1)
    assert node1.x == 5
    assert node1.y == 5
    assert node1.z == 5


def test_mesh_scale():
    """Test mesh scaling"""
    mesh = MeshData()

    mesh.add_node(1, 2, 3)

    mesh.scale(2.0)

    node = mesh.get_node(1)
    assert node.x == 2
    assert node.y == 4
    assert node.z == 6


def test_mesh_surface_detection():
    """Test surface element detection"""
    mesh = MeshData(ElementType.HEX8)

    # Create a simple 2x2x2 box mesh (8 elements)
    # This is a simplified test
    for k in range(3):
        for j in range(3):
            for i in range(3):
                mesh.add_node(i, j, k)

    # Add one hex element (nodes 1-8)
    mesh.add_element([1, 2, 5, 4, 10, 11, 14, 13])

    # Find surface faces
    surface = mesh.find_surface_elements()

    # Single element should have 6 surface faces
    assert len(surface) == 6
