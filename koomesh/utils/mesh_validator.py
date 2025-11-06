"""
Mesh Validation Utility
========================

Validates mesh data for common issues.

Author: KooMeshGenerator Team
License: MIT
"""

import numpy as np
from typing import List, Tuple
from koomesh.meshing.mesh_data import MeshData


class ValidationIssue:
    """Represents a validation issue"""

    def __init__(self, severity: str, message: str, details: str = ""):
        self.severity = severity  # 'error', 'warning', 'info'
        self.message = message
        self.details = details

    def __str__(self):
        prefix = {"error": "❌ ERROR", "warning": "⚠️  WARNING", "info": "ℹ️  INFO"}
        s = f"{prefix.get(self.severity, '•')} {self.message}"
        if self.details:
            s += f"\n    {self.details}"
        return s


class MeshValidator:
    """
    Validates mesh data for common issues

    Example:
        >>> validator = MeshValidator(mesh)
        >>> issues = validator.validate()
        >>> for issue in issues:
        >>>     print(issue)
    """

    def __init__(self, mesh: MeshData):
        """Initialize with mesh data"""
        self.mesh = mesh
        self.issues: List[ValidationIssue] = []

    def validate(self) -> List[ValidationIssue]:
        """
        Run all validations

        Returns:
            List of validation issues found
        """
        self.issues = []

        self._check_empty_mesh()
        self._check_duplicate_nodes()
        self._check_invalid_element_nodes()
        self._check_degenerate_elements()
        self._check_node_usage()

        return self.issues

    def _check_empty_mesh(self):
        """Check if mesh is empty"""
        if not self.mesh.nodes:
            self.issues.append(ValidationIssue(
                "error",
                "Mesh has no nodes",
                "Cannot export empty mesh"
            ))

        if not self.mesh.elements:
            self.issues.append(ValidationIssue(
                "error",
                "Mesh has no elements",
                "Cannot export empty mesh"
            ))

    def _check_duplicate_nodes(self):
        """Check for duplicate node coordinates"""
        coords = {}
        tolerance = 1e-10

        for nid, node in self.mesh.nodes.items():
            coord_key = (
                round(node.x / tolerance),
                round(node.y / tolerance),
                round(node.z / tolerance)
            )

            if coord_key in coords:
                self.issues.append(ValidationIssue(
                    "warning",
                    f"Duplicate node coordinates detected",
                    f"Nodes {coords[coord_key]} and {nid} have same coordinates"
                ))
            else:
                coords[coord_key] = nid

    def _check_invalid_element_nodes(self):
        """Check if all element nodes exist"""
        for eid, elem in self.mesh.elements.items():
            for nid in elem.nodes:
                if nid not in self.mesh.nodes:
                    self.issues.append(ValidationIssue(
                        "error",
                        f"Element {eid} references non-existent node {nid}",
                        "Element connectivity is invalid"
                    ))

    def _check_degenerate_elements(self):
        """Check for degenerate elements"""
        for eid, elem in self.mesh.elements.items():
            # Check for duplicate nodes in element
            if len(elem.nodes) != len(set(elem.nodes)):
                self.issues.append(ValidationIssue(
                    "error",
                    f"Element {eid} has duplicate nodes",
                    "Degenerate element detected"
                ))

            # Check element volume (if possible)
            if elem.type.name in ['HEX8', 'TET4']:
                try:
                    nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
                    coords = np.array([[n.x, n.y, n.z] for n in nodes])

                    if elem.type.name == 'TET4':
                        # Check tetrahedron volume
                        v1 = coords[1] - coords[0]
                        v2 = coords[2] - coords[0]
                        v3 = coords[3] - coords[0]
                        volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0

                        if volume < 1e-10:
                            self.issues.append(ValidationIssue(
                                "warning",
                                f"Element {eid} has near-zero volume",
                                f"Volume: {volume:.3e}"
                            ))
                except:
                    pass

    def _check_node_usage(self):
        """Check for unused nodes"""
        used_nodes = set()
        for elem in self.mesh.elements.values():
            used_nodes.update(elem.nodes)

        all_nodes = set(self.mesh.nodes.keys())
        unused = all_nodes - used_nodes

        if unused:
            self.issues.append(ValidationIssue(
                "info",
                f"Found {len(unused)} unused nodes",
                f"Nodes not referenced by any element"
            ))

    def is_valid(self) -> bool:
        """
        Check if mesh is valid (no errors)

        Returns:
            True if no errors found, False otherwise
        """
        issues = self.validate()
        return not any(issue.severity == 'error' for issue in issues)

    def generate_report(self) -> str:
        """Generate validation report"""
        issues = self.validate()

        if not issues:
            return "✓ Mesh validation passed - no issues found"

        lines = []
        lines.append("Mesh Validation Report")
        lines.append("=" * 60)

        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        infos = [i for i in issues if i.severity == 'info']

        if errors:
            lines.append(f"\n{len(errors)} ERROR(S):")
            for issue in errors:
                lines.append(str(issue))

        if warnings:
            lines.append(f"\n{len(warnings)} WARNING(S):")
            for issue in warnings:
                lines.append(str(issue))

        if infos:
            lines.append(f"\n{len(infos)} INFO:")
            for issue in infos:
                lines.append(str(issue))

        lines.append("\n" + "=" * 60)

        if errors:
            lines.append("Status: ❌ FAILED - Mesh has errors")
        elif warnings:
            lines.append("Status: ⚠️  PASSED WITH WARNINGS")
        else:
            lines.append("Status: ✓ PASSED")

        return "\n".join(lines)


def validate_mesh(mesh: MeshData, print_report: bool = True) -> bool:
    """
    Convenience function to validate mesh

    Args:
        mesh: Mesh data to validate
        print_report: Print validation report

    Returns:
        True if valid (no errors), False otherwise

    Example:
        >>> if validate_mesh(mesh):
        >>>     print("Mesh is valid")
    """
    validator = MeshValidator(mesh)

    if print_report:
        print(validator.generate_report())

    return validator.is_valid()
