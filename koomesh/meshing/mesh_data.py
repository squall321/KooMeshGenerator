"""
Mesh Data Structures Module
============================

This module provides data structures for representing finite element meshes.

Structures:
- Node: Mesh node with coordinates
- Element: Mesh element with connectivity
- MeshData: Complete mesh data container
- ElementType: Element type enumeration

Usage:
    >>> from koomesh.meshing.mesh_data import MeshData, ElementType
    >>> mesh = MeshData(element_type=ElementType.HEX8)
    >>> mesh.add_node(0, 0, 0)
    >>> mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8])
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import numpy as np
import logging


class ElementType(Enum):
    """
    Finite element type enumeration

    Supported element types:
    - TET4: 4-node tetrahedron
    - TET10: 10-node tetrahedron (quadratic)
    - HEX8: 8-node hexahedron
    - HEX20: 20-node hexahedron (quadratic)
    - PYRAMID5: 5-node pyramid
    - PRISM6: 6-node prism/wedge
    - QUAD4: 4-node quadrilateral (2D)
    - TRI3: 3-node triangle (2D)
    """
    TET4 = ("tet4", 4, "tetrahedron")
    TET10 = ("tet10", 10, "tetrahedron")
    HEX8 = ("hex8", 8, "hexahedron")
    HEX20 = ("hex20", 20, "hexahedron")
    PYRAMID5 = ("pyramid5", 5, "pyramid")
    PRISM6 = ("prism6", 6, "prism")
    QUAD4 = ("quad4", 4, "quadrilateral")
    TRI3 = ("tri3", 3, "triangle")

    def __init__(self, code: str, num_nodes: int, description: str):
        self.code = code
        self.num_nodes = num_nodes
        self.description = description

    def is_3d(self) -> bool:
        """Check if element is 3D"""
        return self in [ElementType.TET4, ElementType.TET10,
                       ElementType.HEX8, ElementType.HEX20,
                       ElementType.PYRAMID5, ElementType.PRISM6]

    def is_2d(self) -> bool:
        """Check if element is 2D"""
        return self in [ElementType.QUAD4, ElementType.TRI3]

    def is_hex(self) -> bool:
        """Check if element is hexahedral"""
        return self in [ElementType.HEX8, ElementType.HEX20]

    def is_tet(self) -> bool:
        """Check if element is tetrahedral"""
        return self in [ElementType.TET4, ElementType.TET10]


@dataclass
class Node:
    """
    Mesh node with coordinates

    Attributes:
        id: Node ID (1-based for LS-DYNA compatibility)
        x: X coordinate
        y: Y coordinate
        z: Z coordinate
        metadata: Additional node data (boundary conditions, etc.)
    """
    id: int
    x: float
    y: float
    z: float
    metadata: Dict = field(default_factory=dict)

    def coordinates(self) -> np.ndarray:
        """Get coordinates as numpy array"""
        return np.array([self.x, self.y, self.z])

    def distance_to(self, other: 'Node') -> float:
        """Calculate distance to another node"""
        return np.linalg.norm(self.coordinates() - other.coordinates())

    def __repr__(self) -> str:
        return f"Node({self.id}: [{self.x:.3f}, {self.y:.3f}, {self.z:.3f}])"


@dataclass
class Element:
    """
    Mesh element with connectivity

    Attributes:
        id: Element ID (1-based)
        type: Element type
        nodes: List of node IDs (connectivity)
        part_id: Part/material ID
        metadata: Additional element data
    """
    id: int
    type: ElementType
    nodes: List[int]
    part_id: int = 1
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate element after initialization"""
        if len(self.nodes) != self.type.num_nodes:
            raise ValueError(
                f"Element type {self.type.code} requires {self.type.num_nodes} nodes, "
                f"but {len(self.nodes)} were provided"
            )

    def get_face_nodes(self, face_id: int) -> List[int]:
        """
        Get node IDs for a specific face

        Args:
            face_id: Face index (0-based)

        Returns:
            List of node IDs forming the face
        """
        if self.type == ElementType.HEX8:
            # Hex8 face definitions (0-indexed)
            faces = [
                [0, 3, 2, 1],  # Face 0: bottom (-Z)
                [4, 5, 6, 7],  # Face 1: top (+Z)
                [0, 1, 5, 4],  # Face 2: front (-Y)
                [2, 3, 7, 6],  # Face 3: back (+Y)
                [0, 4, 7, 3],  # Face 4: left (-X)
                [1, 2, 6, 5],  # Face 5: right (+X)
            ]
            if 0 <= face_id < 6:
                return [self.nodes[i] for i in faces[face_id]]

        elif self.type == ElementType.TET4:
            # Tet4 face definitions
            faces = [
                [0, 2, 1],  # Face 0
                [0, 1, 3],  # Face 1
                [1, 2, 3],  # Face 2
                [2, 0, 3],  # Face 3
            ]
            if 0 <= face_id < 4:
                return [self.nodes[i] for i in faces[face_id]]

        raise ValueError(f"Invalid face_id {face_id} for element type {self.type.code}")

    def num_faces(self) -> int:
        """Get number of faces for this element type"""
        if self.type.is_hex():
            return 6
        elif self.type.is_tet():
            return 4
        elif self.type == ElementType.PYRAMID5:
            return 5
        elif self.type == ElementType.PRISM6:
            return 5
        return 0

    def __repr__(self) -> str:
        return f"Element({self.id}: {self.type.code}, nodes={self.nodes})"


class MeshData:
    """
    Complete mesh data container

    This class stores all mesh data including nodes, elements, and metadata.
    It provides methods for adding, querying, and validating mesh data.

    Attributes:
        element_type: Primary element type
        nodes: Dictionary of Node objects (node_id -> Node)
        elements: Dictionary of Element objects (elem_id -> Element)
        node_sets: Named sets of node IDs
        element_sets: Named sets of element IDs
        metadata: Additional mesh metadata

    Example:
        >>> mesh = MeshData(ElementType.HEX8)
        >>> nid1 = mesh.add_node(0, 0, 0)
        >>> nid2 = mesh.add_node(1, 0, 0)
        >>> # ... add more nodes
        >>> eid = mesh.add_element([nid1, nid2, ...])
        >>> print(f"Mesh has {mesh.num_nodes()} nodes")
    """

    def __init__(self, element_type: ElementType = ElementType.HEX8):
        """
        Initialize mesh data

        Args:
            element_type: Primary element type for this mesh
        """
        self.element_type = element_type
        self.nodes: Dict[int, Node] = {}
        self.elements: Dict[int, Element] = {}
        self.node_sets: Dict[str, Set[int]] = {}
        self.element_sets: Dict[str, Set[int]] = {}
        self.metadata: Dict = {}

        self.logger = logging.getLogger(__name__)

        # Counters for auto-incrementing IDs
        self._next_node_id = 1
        self._next_element_id = 1

    def add_node(self, x: float, y: float, z: float,
                 node_id: Optional[int] = None,
                 metadata: Optional[Dict] = None) -> int:
        """
        Add a node to the mesh

        Args:
            x, y, z: Node coordinates
            node_id: Optional node ID (auto-generated if not provided)
            metadata: Optional node metadata

        Returns:
            Node ID
        """
        if node_id is None:
            node_id = self._next_node_id
            self._next_node_id += 1
        else:
            if node_id in self.nodes:
                raise ValueError(f"Node ID {node_id} already exists")
            self._next_node_id = max(self._next_node_id, node_id + 1)

        node = Node(
            id=node_id,
            x=x, y=y, z=z,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node

        return node_id

    def add_element(self, node_ids: List[int],
                   element_id: Optional[int] = None,
                   element_type: Optional[ElementType] = None,
                   part_id: int = 1,
                   metadata: Optional[Dict] = None) -> int:
        """
        Add an element to the mesh

        Args:
            node_ids: List of node IDs (connectivity)
            element_id: Optional element ID (auto-generated if not provided)
            element_type: Element type (uses mesh default if not provided)
            part_id: Part/material ID
            metadata: Optional element metadata

        Returns:
            Element ID
        """
        if element_type is None:
            element_type = self.element_type

        if element_id is None:
            element_id = self._next_element_id
            self._next_element_id += 1
        else:
            if element_id in self.elements:
                raise ValueError(f"Element ID {element_id} already exists")
            self._next_element_id = max(self._next_element_id, element_id + 1)

        # Validate that all nodes exist
        for nid in node_ids:
            if nid not in self.nodes:
                raise ValueError(f"Node ID {nid} does not exist in mesh")

        element = Element(
            id=element_id,
            type=element_type,
            nodes=node_ids,
            part_id=part_id,
            metadata=metadata or {}
        )
        self.elements[element_id] = element

        return element_id

    def get_node(self, node_id: int) -> Node:
        """Get node by ID"""
        if node_id not in self.nodes:
            raise KeyError(f"Node ID {node_id} not found")
        return self.nodes[node_id]

    def get_element(self, element_id: int) -> Element:
        """Get element by ID"""
        if element_id not in self.elements:
            raise KeyError(f"Element ID {element_id} not found")
        return self.elements[element_id]

    def num_nodes(self) -> int:
        """Get number of nodes"""
        return len(self.nodes)

    def num_elements(self) -> int:
        """Get number of elements"""
        return len(self.elements)

    def get_node_coordinates(self) -> np.ndarray:
        """
        Get all node coordinates as numpy array

        Returns:
            Array of shape (num_nodes, 3)
        """
        coords = np.zeros((len(self.nodes), 3))
        for i, node in enumerate(self.nodes.values()):
            coords[i] = node.coordinates()
        return coords

    def get_element_connectivity(self) -> np.ndarray:
        """
        Get element connectivity as numpy array

        Returns:
            Array of shape (num_elements, nodes_per_element)
        """
        if not self.elements:
            return np.array([])

        num_nodes_per_elem = self.element_type.num_nodes
        connectivity = np.zeros((len(self.elements), num_nodes_per_elem), dtype=int)

        for i, elem in enumerate(self.elements.values()):
            connectivity[i] = elem.nodes

        return connectivity

    def create_node_set(self, name: str, node_ids: List[int]):
        """
        Create a named set of nodes

        Args:
            name: Set name
            node_ids: List of node IDs
        """
        self.node_sets[name] = set(node_ids)
        self.logger.debug(f"Created node set '{name}' with {len(node_ids)} nodes")

    def create_element_set(self, name: str, element_ids: List[int]):
        """
        Create a named set of elements

        Args:
            name: Set name
            element_ids: List of element IDs
        """
        self.element_sets[name] = set(element_ids)
        self.logger.debug(f"Created element set '{name}' with {len(element_ids)} elements")

    def find_surface_elements(self) -> List[Tuple[int, int]]:
        """
        Find surface elements (element_id, face_id pairs)

        A face is on the surface if it's not shared with another element.

        Returns:
            List of (element_id, face_id) tuples
        """
        # Build face -> element map
        face_map: Dict[Tuple, List[Tuple[int, int]]] = {}

        for elem_id, elem in self.elements.items():
            for face_id in range(elem.num_faces()):
                face_nodes = tuple(sorted(elem.get_face_nodes(face_id)))

                if face_nodes not in face_map:
                    face_map[face_nodes] = []
                face_map[face_nodes].append((elem_id, face_id))

        # Find faces that appear only once (surface faces)
        surface = []
        for face_nodes, face_list in face_map.items():
            if len(face_list) == 1:
                surface.append(face_list[0])

        self.logger.debug(f"Found {len(surface)} surface faces")
        return surface

    def get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get mesh bounding box

        Returns:
            Tuple of (min_coords, max_coords)
        """
        coords = self.get_node_coordinates()
        return coords.min(axis=0), coords.max(axis=0)

    def translate(self, dx: float, dy: float, dz: float):
        """
        Translate entire mesh

        Args:
            dx, dy, dz: Translation vector
        """
        for node in self.nodes.values():
            node.x += dx
            node.y += dy
            node.z += dz

        self.logger.debug(f"Translated mesh by ({dx}, {dy}, {dz})")

    def scale(self, factor: float):
        """
        Scale entire mesh

        Args:
            factor: Scale factor
        """
        for node in self.nodes.values():
            node.x *= factor
            node.y *= factor
            node.z *= factor

        self.logger.debug(f"Scaled mesh by factor {factor}")

    def merge(self, other: 'MeshData', tolerance: float = 1e-6):
        """
        Merge another mesh into this one

        Duplicate nodes within tolerance will be merged.

        Args:
            other: Mesh to merge
            tolerance: Distance tolerance for node merging
        """
        from scipy.spatial import cKDTree

        # Build KD-tree of existing nodes
        existing_coords = self.get_node_coordinates()
        tree = cKDTree(existing_coords)

        # Map from other mesh node IDs to this mesh node IDs
        node_id_map: Dict[int, int] = {}

        # Process nodes from other mesh
        for other_node in other.nodes.values():
            coord = other_node.coordinates()

            # Find close nodes
            indices = tree.query_ball_point(coord, tolerance)

            if indices:
                # Use existing node
                existing_node_id = list(self.nodes.keys())[indices[0]]
                node_id_map[other_node.id] = existing_node_id
            else:
                # Add new node
                new_id = self.add_node(
                    other_node.x, other_node.y, other_node.z,
                    metadata=other_node.metadata
                )
                node_id_map[other_node.id] = new_id

        # Process elements from other mesh
        for other_elem in other.elements.values():
            # Map node IDs
            new_node_ids = [node_id_map[nid] for nid in other_elem.nodes]

            self.add_element(
                new_node_ids,
                element_type=other_elem.type,
                part_id=other_elem.part_id,
                metadata=other_elem.metadata
            )

        self.logger.info(f"Merged mesh: {other.num_nodes()} nodes, {other.num_elements()} elements")

    def get_statistics(self) -> Dict:
        """
        Get mesh statistics

        Returns:
            Dictionary with mesh statistics
        """
        bbox_min, bbox_max = self.get_bounding_box()
        dimensions = bbox_max - bbox_min

        return {
            'num_nodes': self.num_nodes(),
            'num_elements': self.num_elements(),
            'element_type': self.element_type.code,
            'bounding_box': {
                'min': bbox_min.tolist(),
                'max': bbox_max.tolist(),
                'dimensions': dimensions.tolist()
            },
            'node_sets': len(self.node_sets),
            'element_sets': len(self.element_sets)
        }

    def validate(self) -> bool:
        """
        Validate mesh data

        Returns:
            True if mesh is valid, raises exception otherwise
        """
        # Check that all elements reference valid nodes
        for elem in self.elements.values():
            for nid in elem.nodes:
                if nid not in self.nodes:
                    raise ValueError(
                        f"Element {elem.id} references non-existent node {nid}"
                    )

        # Check for duplicate nodes (within tolerance)
        # This is a simple check; for large meshes, use KD-tree
        if self.num_nodes() < 10000:
            coords = self.get_node_coordinates()
            for i in range(len(coords)):
                for j in range(i + 1, len(coords)):
                    dist = np.linalg.norm(coords[i] - coords[j])
                    if dist < 1e-10:
                        node_ids = list(self.nodes.keys())
                        self.logger.warning(
                            f"Duplicate nodes found: {node_ids[i]}, {node_ids[j]}"
                        )

        self.logger.debug("Mesh validation passed")
        return True

    def __repr__(self) -> str:
        return (f"MeshData(type={self.element_type.code}, "
                f"nodes={self.num_nodes()}, elements={self.num_elements()})")


def create_structured_box_mesh(
    length: float,
    width: float,
    height: float,
    nx: int,
    ny: int,
    nz: int,
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> MeshData:
    """
    Create a structured hexahedral mesh for a box

    This is a utility function for creating simple test meshes.

    Args:
        length: Box length (X direction)
        width: Box width (Y direction)
        height: Box height (Z direction)
        nx: Number of elements in X direction
        ny: Number of elements in Y direction
        nz: Number of elements in Z direction
        origin: Box origin coordinates

    Returns:
        MeshData with structured hex mesh

    Example:
        >>> mesh = create_structured_box_mesh(10.0, 10.0, 10.0, 2, 2, 2)
        >>> mesh.num_nodes()
        27
        >>> mesh.num_elements()
        8
    """
    mesh = MeshData(element_type=ElementType.HEX8)

    ox, oy, oz = origin
    dx = length / nx
    dy = width / ny
    dz = height / nz

    # Create nodes
    node_id = 1
    node_map = {}  # (i,j,k) -> node_id

    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                x = ox + i * dx
                y = oy + j * dy
                z = oz + k * dz

                mesh.add_node(x, y, z, node_id=node_id)
                node_map[(i, j, k)] = node_id
                node_id += 1

    # Create hex elements
    elem_id = 1
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Hex8 node ordering (LS-DYNA convention)
                n1 = node_map[(i, j, k)]
                n2 = node_map[(i + 1, j, k)]
                n3 = node_map[(i + 1, j + 1, k)]
                n4 = node_map[(i, j + 1, k)]
                n5 = node_map[(i, j, k + 1)]
                n6 = node_map[(i + 1, j, k + 1)]
                n7 = node_map[(i + 1, j + 1, k + 1)]
                n8 = node_map[(i, j + 1, k + 1)]

                mesh.add_element(
                    node_ids=[n1, n2, n3, n4, n5, n6, n7, n8],
                    element_id=elem_id,
                    element_type=ElementType.HEX8
                )
                elem_id += 1

    return mesh
