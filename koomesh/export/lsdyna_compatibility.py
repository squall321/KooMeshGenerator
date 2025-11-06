"""
LS-DYNA Compatibility Checker
==============================

This module provides functionality to validate mesh data against LS-DYNA
format constraints and requirements.

Features:
- Node ID validation (range, duplicates)
- Element ID validation (range, duplicates)
- Element type compatibility checking
- Node count per element validation
- Coordinate range validation
- Comprehensive error reporting

Usage:
    >>> from koomesh.export.lsdyna_compatibility import LSDynaCompatibilityChecker
    >>> checker = LSDynaCompatibilityChecker()
    >>> result = checker.check_mesh(mesh)
    >>> if not result.is_valid():
    ...     print(result.summary())
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType


# LS-DYNA Constraints
MAX_NODE_ID = 99999999  # 8-digit maximum
MAX_ELEMENT_ID = 99999999  # 8-digit maximum
MAX_COORDINATE_VALUE = 1e15  # Practical limit for coordinate values
MIN_NODE_ID = 1  # Must be positive
MIN_ELEMENT_ID = 1  # Must be positive

# Element type requirements
ELEMENT_NODE_COUNTS = {
    ElementType.TET4: 4,
    ElementType.TET10: 10,
    ElementType.HEX8: 8,
    ElementType.HEX20: 20,
    ElementType.HEX27: 27,
    ElementType.PRISM6: 6,
    ElementType.PYRAMID5: 5,
}


@dataclass
class CompatibilityIssue:
    """Single compatibility issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'node_id', 'element_id', 'element_type', etc.
    message: str
    details: Optional[Dict] = None


@dataclass
class CompatibilityReport:
    """
    LS-DYNA compatibility check report

    Attributes:
        is_compatible: Overall compatibility status
        num_errors: Number of errors found
        num_warnings: Number of warnings found
        issues: List of all issues found
        node_stats: Node-related statistics
        element_stats: Element-related statistics
    """
    is_compatible: bool = True
    num_errors: int = 0
    num_warnings: int = 0
    issues: List[CompatibilityIssue] = field(default_factory=list)
    node_stats: Dict = field(default_factory=dict)
    element_stats: Dict = field(default_factory=dict)

    def add_issue(self, severity: str, category: str, message: str, details: Optional[Dict] = None):
        """Add an issue to the report"""
        issue = CompatibilityIssue(severity, category, message, details)
        self.issues.append(issue)

        if severity == 'error':
            self.num_errors += 1
            self.is_compatible = False
        elif severity == 'warning':
            self.num_warnings += 1

    def is_valid(self) -> bool:
        """Check if mesh is valid (no errors)"""
        return self.is_compatible and self.num_errors == 0

    def summary(self) -> str:
        """Get report summary as string"""
        lines = [
            "="*70,
            "LS-DYNA COMPATIBILITY REPORT",
            "="*70,
            "",
            f"Status: {'✓ COMPATIBLE' if self.is_compatible else '✗ INCOMPATIBLE'}",
            f"Errors: {self.num_errors}",
            f"Warnings: {self.num_warnings}",
            "",
        ]

        if self.node_stats:
            lines.extend([
                "Node Statistics:",
                f"  Total Nodes: {self.node_stats.get('total', 0)}",
                f"  ID Range: {self.node_stats.get('min_id', 0)} - {self.node_stats.get('max_id', 0)}",
                "",
            ])

        if self.element_stats:
            lines.extend([
                "Element Statistics:",
                f"  Total Elements: {self.element_stats.get('total', 0)}",
                f"  ID Range: {self.element_stats.get('min_id', 0)} - {self.element_stats.get('max_id', 0)}",
                "",
            ])

        if self.issues:
            lines.append("Issues Found:")
            lines.append("-"*70)

            # Group by severity
            errors = [i for i in self.issues if i.severity == 'error']
            warnings = [i for i in self.issues if i.severity == 'warning']
            infos = [i for i in self.issues if i.severity == 'info']

            if errors:
                lines.append("\nERRORS:")
                for issue in errors[:10]:  # Show first 10
                    lines.append(f"  [{issue.category}] {issue.message}")
                if len(errors) > 10:
                    lines.append(f"  ... and {len(errors) - 10} more errors")

            if warnings:
                lines.append("\nWARNINGS:")
                for issue in warnings[:10]:  # Show first 10
                    lines.append(f"  [{issue.category}] {issue.message}")
                if len(warnings) > 10:
                    lines.append(f"  ... and {len(warnings) - 10} more warnings")

            if infos:
                lines.append("\nINFO:")
                for issue in infos[:5]:  # Show first 5
                    lines.append(f"  [{issue.category}] {issue.message}")

        lines.extend([
            "",
            "="*70,
        ])

        return "\n".join(lines)


class LSDynaCompatibilityChecker:
    """
    LS-DYNA compatibility checker

    This class validates mesh data against LS-DYNA format constraints
    and provides detailed compatibility reports.

    Example:
        >>> checker = LSDynaCompatibilityChecker()
        >>> report = checker.check_mesh(mesh)
        >>> if not report.is_valid():
        ...     print(report.summary())
        ...     for issue in report.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self,
                 max_node_id: int = MAX_NODE_ID,
                 max_element_id: int = MAX_ELEMENT_ID,
                 strict_mode: bool = False):
        """
        Initialize compatibility checker

        Args:
            max_node_id: Maximum allowed node ID
            max_element_id: Maximum allowed element ID
            strict_mode: Enable strict validation (treat warnings as errors)
        """
        self.max_node_id = max_node_id
        self.max_element_id = max_element_id
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)

    def check_mesh(self, mesh: MeshData) -> CompatibilityReport:
        """
        Check mesh compatibility with LS-DYNA format

        Args:
            mesh: MeshData to check

        Returns:
            CompatibilityReport with validation results
        """
        self.logger.info("Checking LS-DYNA compatibility...")

        report = CompatibilityReport()

        # Check nodes
        self._check_nodes(mesh, report)

        # Check elements
        self._check_elements(mesh, report)

        # Check element types
        self._check_element_types(mesh, report)

        # Check coordinate ranges
        self._check_coordinate_ranges(mesh, report)

        # Add statistics
        report.node_stats = {
            'total': mesh.num_nodes(),
            'min_id': min(mesh.nodes.keys()) if mesh.nodes else 0,
            'max_id': max(mesh.nodes.keys()) if mesh.nodes else 0,
        }

        report.element_stats = {
            'total': mesh.num_elements(),
            'min_id': min(mesh.elements.keys()) if mesh.elements else 0,
            'max_id': max(mesh.elements.keys()) if mesh.elements else 0,
        }

        self.logger.info(f"Compatibility check complete: {report.num_errors} errors, {report.num_warnings} warnings")

        return report

    def _check_nodes(self, mesh: MeshData, report: CompatibilityReport):
        """Check node ID validity"""
        # Check for duplicate node IDs (shouldn't happen, but validate)
        node_ids = list(mesh.nodes.keys())
        unique_ids = set(node_ids)

        if len(node_ids) != len(unique_ids):
            duplicates = [nid for nid in unique_ids if node_ids.count(nid) > 1]
            report.add_issue(
                'error', 'node_id',
                f"Found {len(duplicates)} duplicate node IDs",
                {'duplicates': duplicates[:10]}
            )

        # Check node ID ranges
        invalid_ids = []
        for node_id in mesh.nodes.keys():
            if node_id < MIN_NODE_ID:
                invalid_ids.append(node_id)
                report.add_issue(
                    'error', 'node_id',
                    f"Node ID {node_id} is below minimum ({MIN_NODE_ID})"
                )
            elif node_id > self.max_node_id:
                invalid_ids.append(node_id)
                report.add_issue(
                    'error', 'node_id',
                    f"Node ID {node_id} exceeds maximum ({self.max_node_id})"
                )

        if invalid_ids:
            self.logger.warning(f"Found {len(invalid_ids)} nodes with invalid IDs")

    def _check_elements(self, mesh: MeshData, report: CompatibilityReport):
        """Check element ID validity"""
        # Check for duplicate element IDs
        elem_ids = list(mesh.elements.keys())
        unique_ids = set(elem_ids)

        if len(elem_ids) != len(unique_ids):
            duplicates = [eid for eid in unique_ids if elem_ids.count(eid) > 1]
            report.add_issue(
                'error', 'element_id',
                f"Found {len(duplicates)} duplicate element IDs",
                {'duplicates': duplicates[:10]}
            )

        # Check element ID ranges
        invalid_ids = []
        for elem_id in mesh.elements.keys():
            if elem_id < MIN_ELEMENT_ID:
                invalid_ids.append(elem_id)
                report.add_issue(
                    'error', 'element_id',
                    f"Element ID {elem_id} is below minimum ({MIN_ELEMENT_ID})"
                )
            elif elem_id > self.max_element_id:
                invalid_ids.append(elem_id)
                report.add_issue(
                    'error', 'element_id',
                    f"Element ID {elem_id} exceeds maximum ({self.max_element_id})"
                )

        if invalid_ids:
            self.logger.warning(f"Found {len(invalid_ids)} elements with invalid IDs")

    def _check_element_types(self, mesh: MeshData, report: CompatibilityReport):
        """Check element type compatibility and node counts"""
        # Check if element type is supported
        if mesh.element_type not in ELEMENT_NODE_COUNTS:
            report.add_issue(
                'error', 'element_type',
                f"Element type {mesh.element_type.code} is not supported by LS-DYNA",
                {'element_type': mesh.element_type.code}
            )
            return

        expected_node_count = ELEMENT_NODE_COUNTS[mesh.element_type]

        # Check each element's node count
        invalid_elements = []
        for elem_id, elem in mesh.elements.items():
            actual_count = len(elem.nodes)
            if actual_count != expected_node_count:
                invalid_elements.append(elem_id)
                report.add_issue(
                    'error', 'element_nodes',
                    f"Element {elem_id} has {actual_count} nodes, expected {expected_node_count}",
                    {'element_id': elem_id, 'actual': actual_count, 'expected': expected_node_count}
                )

        if invalid_elements:
            self.logger.warning(f"Found {len(invalid_elements)} elements with invalid node counts")

        # Check for undefined nodes in elements
        undefined_nodes = set()
        for elem in mesh.elements.values():
            for node_id in elem.nodes:
                if node_id not in mesh.nodes:
                    undefined_nodes.add(node_id)

        if undefined_nodes:
            report.add_issue(
                'error', 'element_nodes',
                f"Found {len(undefined_nodes)} undefined node IDs referenced in elements",
                {'undefined_nodes': list(undefined_nodes)[:10]}
            )

    def _check_coordinate_ranges(self, mesh: MeshData, report: CompatibilityReport):
        """Check if coordinates are within acceptable ranges"""
        out_of_range_nodes = []

        for node_id, node in mesh.nodes.items():
            coords = node.coordinates()
            if any(abs(c) > MAX_COORDINATE_VALUE for c in coords):
                out_of_range_nodes.append(node_id)
                max_coord = max(abs(c) for c in coords)
                report.add_issue(
                    'warning', 'coordinate_range',
                    f"Node {node_id} has coordinate value {max_coord:.2e} exceeding recommended limit",
                    {'node_id': node_id, 'max_coord': max_coord}
                )

        if out_of_range_nodes and len(out_of_range_nodes) > 10:
            self.logger.warning(f"Found {len(out_of_range_nodes)} nodes with extreme coordinate values")

    def fix_node_ids(self, mesh: MeshData, start_id: int = 1) -> Dict[int, int]:
        """
        Renumber node IDs to be sequential starting from start_id

        Args:
            mesh: Mesh to modify
            start_id: Starting node ID

        Returns:
            Mapping from old IDs to new IDs
        """
        old_to_new = {}
        new_nodes = {}

        for i, (old_id, node) in enumerate(sorted(mesh.nodes.items()), start=start_id):
            new_id = i
            old_to_new[old_id] = new_id
            new_nodes[new_id] = node

        # Update mesh nodes
        mesh.nodes = new_nodes

        # Update element node references
        for elem in mesh.elements.values():
            elem.nodes = [old_to_new[nid] for nid in elem.nodes]

        self.logger.info(f"Renumbered {len(old_to_new)} nodes starting from {start_id}")

        return old_to_new

    def fix_element_ids(self, mesh: MeshData, start_id: int = 1) -> Dict[int, int]:
        """
        Renumber element IDs to be sequential starting from start_id

        Args:
            mesh: Mesh to modify
            start_id: Starting element ID

        Returns:
            Mapping from old IDs to new IDs
        """
        old_to_new = {}
        new_elements = {}

        for i, (old_id, elem) in enumerate(sorted(mesh.elements.items()), start=start_id):
            new_id = i
            old_to_new[old_id] = new_id
            elem.id = new_id
            new_elements[new_id] = elem

        # Update mesh elements
        mesh.elements = new_elements

        self.logger.info(f"Renumbered {len(old_to_new)} elements starting from {start_id}")

        return old_to_new
