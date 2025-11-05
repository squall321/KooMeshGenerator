"""
Hierarchy Parser Module
========================

This module provides functionality to parse and manage hierarchical structures
from STEP files and directory structures.

Features:
- Parse STEP assembly hierarchies
- Parse directory-based hierarchies
- Build tree structures
- Navigate and query hierarchies

Usage:
    >>> from koomesh.io.hierarchy_parser import HierarchyParser
    >>> parser = HierarchyParser()
    >>> root = parser.parse_from_step('assembly.step')
    >>> root.print_tree()
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Iterator
from pathlib import Path
import logging

# Try to import PythonOCC for STEP parsing
try:
    from OCC.Extend.DataExchange import read_step_file_with_names_colors
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.TDocStd import TDocStd_Document
    from OCC.Core.XCAFDoc import (
        XCAFDoc_DocumentTool_ShapeTool,
        XCAFDoc_DocumentTool_ColorTool
    )
    from OCC.Core.XCAFApp import XCAFApp_Application
    from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
    from OCC.Core.TCollection import TCollection_ExtendedString
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False
    TopoDS_Shape = object  # Dummy type


@dataclass
class HierarchyNode:
    """
    Node in a hierarchical structure

    Represents a single component in the assembly hierarchy, which can be
    either a part, sub-assembly, or the root assembly.

    Attributes:
        name: Node name/label
        shape: Associated geometric shape (TopoDS_Shape)
        parent: Parent node (None for root)
        children: List of child nodes
        level: Depth in tree (0 for root)
        part_type: Type of component (component, assembly, part)
        metadata: Additional metadata dictionary

    Example:
        >>> node = HierarchyNode("Part1", shape, part_type="part")
        >>> node.add_child(child_node)
        >>> path = node.get_path()  # Returns "/Assembly/SubAsm/Part1"
    """

    name: str
    shape: Optional[TopoDS_Shape] = None
    parent: Optional['HierarchyNode'] = None
    children: List['HierarchyNode'] = field(default_factory=list)
    level: int = 0
    part_type: str = "component"  # component, assembly, part
    metadata: Dict = field(default_factory=dict)

    def add_child(self, child: 'HierarchyNode'):
        """
        Add a child node

        Args:
            child: Child node to add
        """
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)

    def remove_child(self, child: 'HierarchyNode'):
        """
        Remove a child node

        Args:
            child: Child node to remove
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_path(self) -> str:
        """
        Get hierarchical path from root to this node

        Returns:
            Path string like "/Assembly/SubAsm/Part1"

        Example:
            >>> node.get_path()
            '/RootAssembly/SubAssembly/Part1'
        """
        if self.parent is None:
            return f"/{self.name}"
        return f"{self.parent.get_path()}/{self.name}"

    def is_leaf(self) -> bool:
        """
        Check if node is a leaf (has no children)

        Returns:
            True if node has no children
        """
        return len(self.children) == 0

    def is_root(self) -> bool:
        """
        Check if node is root (has no parent)

        Returns:
            True if node has no parent
        """
        return self.parent is None

    def num_children(self) -> int:
        """
        Get number of children

        Returns:
            Number of child nodes
        """
        return len(self.children)

    def get_siblings(self) -> List['HierarchyNode']:
        """
        Get sibling nodes (nodes with same parent)

        Returns:
            List of sibling nodes
        """
        if self.parent is None:
            return []

        return [child for child in self.parent.children if child != self]

    def get_descendants(self) -> Iterator['HierarchyNode']:
        """
        Get all descendant nodes (children, grandchildren, etc.)

        Yields:
            Descendant nodes in depth-first order
        """
        for child in self.children:
            yield child
            yield from child.get_descendants()

    def get_ancestors(self) -> Iterator['HierarchyNode']:
        """
        Get all ancestor nodes (parent, grandparent, etc.)

        Yields:
            Ancestor nodes from parent to root
        """
        if self.parent is not None:
            yield self.parent
            yield from self.parent.get_ancestors()

    def find_by_name(self, name: str) -> Optional['HierarchyNode']:
        """
        Find descendant node by name

        Args:
            name: Node name to search for

        Returns:
            First matching node, or None if not found
        """
        if self.name == name:
            return self

        for child in self.children:
            result = child.find_by_name(name)
            if result is not None:
                return result

        return None

    def count_descendants(self) -> int:
        """
        Count total number of descendants

        Returns:
            Number of descendant nodes
        """
        count = len(self.children)
        for child in self.children:
            count += child.count_descendants()
        return count

    def print_tree(self, indent: int = 0, show_metadata: bool = False):
        """
        Print tree structure starting from this node

        Args:
            indent: Current indentation level
            show_metadata: Whether to show metadata

        Example:
            >>> root.print_tree()
            ├─ RootAssembly [assembly]
              ├─ SubAssembly [assembly]
                ├─ Part1 [part]
                ├─ Part2 [part]
        """
        prefix = "  " * indent
        symbol = "├─" if indent > 0 else "●"

        metadata_str = ""
        if show_metadata and self.metadata:
            metadata_str = f" {self.metadata}"

        print(f"{prefix}{symbol} {self.name} [{self.part_type}]{metadata_str}")

        for child in self.children:
            child.print_tree(indent + 1, show_metadata)

    def to_dict(self) -> Dict:
        """
        Convert node and its subtree to dictionary

        Returns:
            Dictionary representation of node tree
        """
        return {
            'name': self.name,
            'part_type': self.part_type,
            'level': self.level,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children]
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"HierarchyNode(name='{self.name}', type='{self.part_type}', children={len(self.children)})"


class HierarchyParser:
    """
    Parser for hierarchical structures from STEP files and directories

    This class can parse hierarchy from:
    1. STEP file assembly structure (using XDE - Extended Data Exchange)
    2. Directory structure (folder hierarchy represents assembly hierarchy)

    Example:
        >>> parser = HierarchyParser()
        >>> root = parser.parse_from_step('assembly.step')
        >>> root.print_tree()
    """

    def __init__(self):
        """Initialize hierarchy parser"""
        self.logger = logging.getLogger(__name__)
        self.root: Optional[HierarchyNode] = None

    def parse_from_step(self, filepath: str) -> HierarchyNode:
        """
        Parse hierarchy from STEP file

        Args:
            filepath: Path to STEP file

        Returns:
            Root node of hierarchy tree

        Raises:
            FileNotFoundError: If file does not exist
            RuntimeError: If PythonOCC is not available
        """
        if not PYTHONOCC_AVAILABLE:
            raise RuntimeError(
                "PythonOCC is not installed. Cannot parse STEP hierarchy."
            )

        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"STEP file not found: {filepath}")

        self.logger.info(f"Parsing hierarchy from STEP file: {filepath}")

        # Try to use XDE for assembly structure
        try:
            root = self._parse_with_xde(str(file_path))
        except Exception as e:
            self.logger.warning(f"XDE parsing failed: {e}, falling back to simple parsing")
            root = self._parse_simple(str(file_path))

        self.root = root
        self.logger.info(f"Parsed hierarchy with {root.count_descendants()} nodes")

        return root

    def _parse_with_xde(self, filepath: str) -> HierarchyNode:
        """
        Parse STEP file using XDE (Extended Data Exchange)

        This method extracts the full assembly structure with names and colors.
        """
        self.logger.debug("Parsing STEP with XDE...")

        # Create XDE document
        app = XCAFApp_Application.GetApplication()
        doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
        app.InitDocument(doc)

        # Create STEP reader
        reader = STEPCAFControl_Reader()
        reader.SetNameMode(True)
        reader.SetColorMode(True)

        # Read file
        status = reader.ReadFile(filepath)
        if status != 1:  # IFSelect_RetDone
            raise RuntimeError(f"Failed to read STEP file with XDE")

        # Transfer to document
        reader.Transfer(doc)

        # Get shape tool
        shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())

        # Get free shapes (top-level assemblies)
        free_shapes = shape_tool.GetFreeShapes()

        # Build hierarchy
        file_name = Path(filepath).stem
        root = HierarchyNode(
            name=file_name,
            part_type="assembly",
            level=0
        )

        for label in free_shapes:
            child = self._build_xde_node(label, shape_tool)
            if child:
                root.add_child(child)

        return root

    def _build_xde_node(self, label, shape_tool) -> Optional[HierarchyNode]:
        """Build hierarchy node from XDE label"""
        # Get shape
        shape = shape_tool.GetShape(label)

        # Get name
        name_string = shape_tool.GetNameString(label)
        name = name_string if name_string else f"Shape_{label.Tag()}"

        # Determine if it's an assembly
        is_assembly = shape_tool.IsAssembly(label)

        node = HierarchyNode(
            name=name,
            shape=shape,
            part_type="assembly" if is_assembly else "part"
        )

        # If assembly, process children
        if is_assembly:
            components = shape_tool.GetComponents(label)
            for comp_label in components:
                child = self._build_xde_node(comp_label, shape_tool)
                if child:
                    node.add_child(child)

        return node

    def _parse_simple(self, filepath: str) -> HierarchyNode:
        """
        Simple STEP parsing without XDE

        Falls back to basic shape reading when XDE is not available or fails.
        """
        from koomesh.io.step_reader import STEPReader

        self.logger.debug("Parsing STEP with simple method...")

        reader = STEPReader()
        shape = reader.read_file(filepath)

        file_name = Path(filepath).stem
        root = HierarchyNode(
            name=file_name,
            shape=shape,
            part_type="part"
        )

        # Extract solids as children
        solids = reader.extract_solids(shape)
        for i, solid in enumerate(solids):
            child = HierarchyNode(
                name=f"{file_name}_solid_{i+1}",
                shape=solid,
                part_type="part"
            )
            root.add_child(child)

        # If no solids found, this is a single part
        if not solids:
            root.part_type = "part"

        return root

    def parse_from_directory(self, directory: Path) -> HierarchyNode:
        """
        Parse hierarchy from directory structure

        Directory structure represents assembly hierarchy:
        - Each directory is an assembly
        - Each STEP file is a part

        Args:
            directory: Root directory path

        Returns:
            Root node of hierarchy tree

        Example:
            >>> parser = HierarchyParser()
            >>> root = parser.parse_from_directory(Path('./assemblies'))
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        self.logger.info(f"Parsing hierarchy from directory: {directory}")

        root = self._parse_directory_recursive(directory)

        self.root = root
        self.logger.info(f"Parsed hierarchy with {root.count_descendants()} nodes")

        return root

    def _parse_directory_recursive(self, directory: Path, level: int = 0) -> HierarchyNode:
        """
        Recursively parse directory structure

        Args:
            directory: Current directory
            level: Current depth level

        Returns:
            Node representing this directory
        """
        node = HierarchyNode(
            name=directory.name,
            part_type="assembly",
            level=level
        )

        # Iterate through directory contents
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                # Subdirectory = sub-assembly
                child = self._parse_directory_recursive(item, level + 1)
                node.add_child(child)

            elif item.suffix.lower() in ['.step', '.stp']:
                # STEP file = part
                try:
                    from koomesh.io.step_reader import STEPReader
                    reader = STEPReader()
                    shape = reader.read_file(str(item))

                    child = HierarchyNode(
                        name=item.stem,
                        shape=shape,
                        part_type="part",
                        level=level + 1,
                        metadata={'filepath': str(item)}
                    )
                    node.add_child(child)

                except Exception as e:
                    self.logger.warning(f"Failed to read {item}: {e}")

        return node

    def flatten(self, node: Optional[HierarchyNode] = None) -> List[HierarchyNode]:
        """
        Flatten hierarchy tree to list

        Args:
            node: Starting node (uses root if None)

        Returns:
            List of all nodes in depth-first order

        Example:
            >>> all_nodes = parser.flatten()
            >>> for node in all_nodes:
            ...     print(node.get_path())
        """
        if node is None:
            node = self.root

        if node is None:
            return []

        result = [node]
        for child in node.children:
            result.extend(self.flatten(child))

        return result

    def get_leaf_nodes(self, node: Optional[HierarchyNode] = None) -> List[HierarchyNode]:
        """
        Get all leaf nodes (parts without children)

        Args:
            node: Starting node (uses root if None)

        Returns:
            List of leaf nodes

        Example:
            >>> parts = parser.get_leaf_nodes()
            >>> print(f"Total parts: {len(parts)}")
        """
        if node is None:
            node = self.root

        if node is None:
            return []

        if node.is_leaf():
            return [node]

        leaves = []
        for child in node.children:
            leaves.extend(self.get_leaf_nodes(child))

        return leaves

    def get_level_nodes(self, level: int) -> List[HierarchyNode]:
        """
        Get all nodes at a specific level

        Args:
            level: Level number (0 = root)

        Returns:
            List of nodes at specified level
        """
        all_nodes = self.flatten()
        return [node for node in all_nodes if node.level == level]

    def print_hierarchy(self, show_metadata: bool = False):
        """
        Print entire hierarchy tree

        Args:
            show_metadata: Whether to show metadata

        Example:
            >>> parser.print_hierarchy()
        """
        if self.root is None:
            print("No hierarchy loaded")
            return

        print(f"\nHierarchy Tree ({self.root.count_descendants()} nodes):")
        print("=" * 60)
        self.root.print_tree(show_metadata=show_metadata)
        print("=" * 60)
