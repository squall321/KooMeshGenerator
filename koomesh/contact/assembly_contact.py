"""
Assembly Contact Management

Manages contact detection and definition for multi-part assemblies.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import logging
import time

from koomesh.meshing.mesh_data import MeshData
from koomesh.contact.contact_classifier import ContactType, ContactClassifier, ContactParameters
from koomesh.utils.logging_utils import PerformanceLogger, ProgressReporter


@dataclass
class ContactPair:
    """Represents a contact pair between two parts"""
    master_part_idx: int
    slave_part_idx: int
    master_part_name: str
    slave_part_name: str
    contact_type: ContactType
    parameters: ContactParameters
    master_surface_nodes: np.ndarray
    slave_surface_nodes: np.ndarray
    gap_distance: float
    contact_area: float


class SpatialHashGrid:
    """
    Spatial hash grid for fast proximity queries.

    Provides O(n) average-case collision detection vs O(n²) brute force.
    """

    def __init__(self, cell_size: float = 10.0):
        """
        Initialize spatial hash grid.

        Args:
            cell_size: Size of grid cells (mm)
        """
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int, int], List[int]] = {}
        self.bboxes: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}

    def insert(self, idx: int, bbox: Tuple[np.ndarray, np.ndarray]):
        """
        Insert bounding box into grid.

        Args:
            idx: Object index
            bbox: (min_corner, max_corner) tuple
        """
        min_corner, max_corner = bbox
        self.bboxes[idx] = bbox

        # Calculate grid cell range
        min_cell = tuple((min_corner / self.cell_size).astype(int))
        max_cell = tuple((max_corner / self.cell_size).astype(int))

        # Insert into all overlapping cells
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                for z in range(min_cell[2], max_cell[2] + 1):
                    cell = (x, y, z)
                    if cell not in self.grid:
                        self.grid[cell] = []
                    self.grid[cell].append(idx)

    def query(self, bbox: Tuple[np.ndarray, np.ndarray]) -> List[int]:
        """
        Query objects overlapping with bounding box.

        Args:
            bbox: (min_corner, max_corner) tuple

        Returns:
            List of object indices
        """
        min_corner, max_corner = bbox

        # Calculate grid cell range
        min_cell = tuple((min_corner / self.cell_size).astype(int))
        max_cell = tuple((max_corner / self.cell_size).astype(int))

        # Collect unique indices from overlapping cells
        candidates = set()
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                for z in range(min_cell[2], max_cell[2] + 1):
                    cell = (x, y, z)
                    if cell in self.grid:
                        candidates.update(self.grid[cell])

        # Filter to actual bbox overlaps
        result = []
        for idx in candidates:
            if self._bbox_overlap(bbox, self.bboxes[idx]):
                result.append(idx)

        return result

    def _bbox_overlap(
        self,
        bbox1: Tuple[np.ndarray, np.ndarray],
        bbox2: Tuple[np.ndarray, np.ndarray]
    ) -> bool:
        """Check if two bounding boxes overlap."""
        min1, max1 = bbox1
        min2, max2 = bbox2

        # Boxes overlap if they overlap in all 3 dimensions
        return (
            min1[0] <= max2[0] and max1[0] >= min2[0] and
            min1[1] <= max2[1] and max1[1] >= min2[1] and
            min1[2] <= max2[2] and max1[2] >= min2[2]
        )


class AssemblyContactManager:
    """
    Manage contact detection for multi-part assemblies.

    Features:
    - Spatial hashing for O(n) collision detection
    - Automatic contact type classification
    - Parameter optimization
    - LS-DYNA card generation

    Example:
        >>> manager = AssemblyContactManager()
        >>> contacts = manager.detect_all_contacts(
        ...     parts, part_names, config
        ... )
        >>> cards = manager.generate_lsdyna_cards(contacts)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.classifier = ContactClassifier()
        self.perf_logger = PerformanceLogger(__name__)

    def detect_all_contacts(
        self,
        parts: List[MeshData],
        part_names: List[str],
        tolerance: float = 1.0,
        materials: Optional[List[str]] = None,
        simulation_type: str = "crash"
    ) -> List[ContactPair]:
        """
        Detect all contact pairs in assembly.

        Uses spatial hashing for efficient O(n) detection vs O(n²) brute force.

        Args:
            parts: List of MeshData objects
            part_names: Names of parts
            tolerance: Contact detection tolerance (mm)
            materials: Optional material names for each part
            simulation_type: Type of simulation

        Returns:
            List of ContactPair objects

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If contact detection fails
        """
        # Input validation
        if parts is None or not isinstance(parts, list):
            raise TypeError("parts must be a list")

        if len(parts) == 0:
            raise ValueError("parts list is empty")

        if len(parts) == 1:
            self.logger.warning("Only 1 part provided - no contacts possible")
            return []

        if part_names is None or not isinstance(part_names, list):
            raise TypeError("part_names must be a list")

        if len(part_names) != len(parts):
            raise ValueError(f"part_names length ({len(part_names)}) must match parts length ({len(parts)})")

        if tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}")

        if materials is not None:
            if not isinstance(materials, list):
                raise TypeError("materials must be a list or None")
            if len(materials) != len(parts):
                raise ValueError(f"materials length ({len(materials)}) must match parts length ({len(parts)})")

        try:
            with self.perf_logger.timer("assembly_contact_detection"):
                self.logger.info(
                    f"Detecting contacts in assembly ({len(parts)} parts)..."
                )

                # Build spatial hash grid
                with self.perf_logger.timer("spatial_hash_build"):
                    grid = SpatialHashGrid(cell_size=tolerance * 10)

                    for i, part in enumerate(parts):
                        bbox = self._get_bounding_box(part)
                        grid.insert(i, bbox)

                # Find candidate pairs using spatial hash
                with self.perf_logger.timer("spatial_hash_query"):
                    candidate_pairs = []
                    for i in range(len(parts)):
                        bbox_i = grid.bboxes[i]

                        # Expand bbox by tolerance for query
                        min_corner = bbox_i[0] - tolerance
                        max_corner = bbox_i[1] + tolerance

                        neighbors = grid.query((min_corner, max_corner))

                        for j in neighbors:
                            if i < j:  # Avoid duplicates and self-contact
                                candidate_pairs.append((i, j))

                brute_force_pairs = len(parts)*(len(parts)-1)//2
                reduction = 100 * (1 - len(candidate_pairs) / brute_force_pairs) if brute_force_pairs > 0 else 0
                self.logger.info(
                    f"Spatial hash found {len(candidate_pairs)} candidate pairs "
                    f"(vs {brute_force_pairs} brute force, {reduction:.1f}% reduction)"
                )
                self.perf_logger.increment_counter("candidate_pairs", len(candidate_pairs))

                # Detailed contact detection for candidates
                with self.perf_logger.timer("detailed_contact_detection"):
                    contacts = []
                    progress = ProgressReporter(
                        "Checking contact candidates",
                        total=len(candidate_pairs),
                        logger_name=__name__
                    )

                    for idx, (i, j) in enumerate(candidate_pairs):
                        contact = self._detect_contact_detailed(
                            parts[i], parts[j],
                            part_names[i], part_names[j],
                            i, j,
                            tolerance=tolerance,
                            material1=materials[i] if materials else None,
                            material2=materials[j] if materials else None,
                            simulation_type=simulation_type
                        )

                        if contact:
                            contacts.append(contact)

                        progress.update(1)

                    progress.finish()

                self.logger.info(
                    f"Detected {len(contacts)} actual contact pairs "
                    f"({len(contacts)/len(candidate_pairs)*100 if candidate_pairs else 0:.1f}% of candidates)"
                )
                self.perf_logger.increment_counter("contacts_detected", len(contacts))
                self.perf_logger.log_statistics()

                return contacts

        except Exception as e:
            self.logger.error(f"Contact detection failed: {e}")
            raise RuntimeError(f"Assembly contact detection failed: {e}") from e

    def _get_bounding_box(self, mesh: MeshData) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate axis-aligned bounding box."""
        if len(mesh.nodes) == 0:
            return (np.zeros(3), np.zeros(3))

        min_corner = np.min(mesh.nodes, axis=0)
        max_corner = np.max(mesh.nodes, axis=0)

        return (min_corner, max_corner)

    def _detect_contact_detailed(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        name1: str,
        name2: str,
        idx1: int,
        idx2: int,
        tolerance: float,
        material1: Optional[str],
        material2: Optional[str],
        simulation_type: str
    ) -> Optional[ContactPair]:
        """Perform detailed contact detection between two parts."""
        from scipy.spatial import cKDTree

        # Get surface nodes (simplified: use all nodes)
        # In production, would extract actual surface nodes
        nodes1 = mesh1.nodes
        nodes2 = mesh2.nodes

        if len(nodes1) == 0 or len(nodes2) == 0:
            return None

        # Build KD-tree for mesh2
        tree = cKDTree(nodes2)

        # Query distances from mesh1 to mesh2
        distances, indices = tree.query(nodes1, k=1)

        # Find nodes within tolerance
        close_mask = distances < tolerance
        num_close = np.sum(close_mask)

        if num_close < 3:  # Require at least 3 contact nodes
            return None

        # Calculate contact properties
        contact_nodes1 = np.where(close_mask)[0]
        contact_nodes2 = indices[close_mask]

        gap_distance = float(np.mean(distances[close_mask]))
        contact_area = float(num_close * gap_distance ** 2)  # Rough estimate

        # Calculate surface angle (simplified)
        surface_angle = self._estimate_surface_angle(
            mesh1, mesh2, contact_nodes1[:10], contact_nodes2[:10]
        )

        # Classify contact type
        contact_type = self.classifier.classify_contact_type(
            gap=gap_distance,
            surface_angle=surface_angle,
            contact_area=contact_area,
            material1=material1,
            material2=material2,
            simulation_type=simulation_type
        )

        # Optimize parameters
        params = self.classifier.optimize_parameters(
            contact_type=contact_type,
            material1=material1,
            material2=material2,
            simulation_type=simulation_type
        )

        return ContactPair(
            master_part_idx=idx1,
            slave_part_idx=idx2,
            master_part_name=name1,
            slave_part_name=name2,
            contact_type=contact_type,
            parameters=params,
            master_surface_nodes=contact_nodes1,
            slave_surface_nodes=contact_nodes2,
            gap_distance=gap_distance,
            contact_area=contact_area
        )

    def _estimate_surface_angle(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        nodes1: np.ndarray,
        nodes2: np.ndarray
    ) -> float:
        """Estimate angle between contact surfaces (simplified)."""
        if len(nodes1) < 3 or len(nodes2) < 3:
            return 0.0

        # Fit planes to sample points
        def fit_plane(points):
            centroid = np.mean(points, axis=0)
            centered = points - centroid
            _, _, vh = np.linalg.svd(centered)
            normal = vh[-1]  # Last singular vector = normal
            return normal / np.linalg.norm(normal)

        try:
            points1 = mesh1.nodes[nodes1[:min(10, len(nodes1))]]
            points2 = mesh2.nodes[nodes2[:min(10, len(nodes2))]]

            normal1 = fit_plane(points1)
            normal2 = fit_plane(points2)

            # Calculate angle between normals
            cos_angle = np.abs(np.dot(normal1, normal2))
            cos_angle = np.clip(cos_angle, 0.0, 1.0)

            angle_rad = np.arccos(cos_angle)
            angle_deg = np.degrees(angle_rad)

            return float(angle_deg)

        except:
            return 0.0

    def generate_lsdyna_cards(
        self,
        contacts: List[ContactPair],
        start_cid: int = 1
    ) -> List[str]:
        """
        Generate LS-DYNA contact keyword cards.

        Args:
            contacts: List of ContactPair objects
            start_cid: Starting contact ID

        Returns:
            List of LS-DYNA keyword card strings
        """
        cards = []

        for i, contact in enumerate(contacts):
            cid = start_cid + i

            card = self._generate_contact_card(contact, cid)
            cards.append(card)

        return cards

    def _generate_contact_card(
        self,
        contact: ContactPair,
        cid: int
    ) -> str:
        """Generate single LS-DYNA contact card."""
        lines = []

        # Select keyword based on contact type
        if contact.contact_type == ContactType.AUTOMATIC:
            keyword = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"
        elif contact.contact_type == ContactType.TIED:
            keyword = "*CONTACT_TIED_SURFACE_TO_SURFACE_ID"
        elif contact.contact_type == ContactType.SLIDING:
            keyword = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"
        elif contact.contact_type == ContactType.FORMING:
            keyword = "*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE_ID"
        elif contact.contact_type == ContactType.TIEBREAK:
            keyword = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_TIEBREAK_ID"
        else:
            keyword = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"

        lines.append(keyword)
        lines.append(f"$#     cid                                                                 title")
        lines.append(
            f"{cid:10d}Contact: {contact.master_part_name} - {contact.slave_part_name}"
        )

        lines.append(f"$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr")
        lines.append(
            f"{contact.slave_part_idx+1:10d}{contact.master_part_idx+1:10d}         3         3         0         0         0         0"
        )

        # Parameters
        params = contact.parameters
        lines.append(f"$#      fs        fd        dc        vc       vdc    penchk        bt        dt")
        lines.append(
            f"{params.fs:10.3f}{params.fd:10.3f}       0.0       0.0       0.0         0       0.0   1.0E+20"
        )

        lines.append(f"$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf")
        lines.append(
            f"       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0"
        )

        lines.append(f"$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq")
        lines.append(
            f"{params.soft:10d}       0.1         0       1.0{params.sbopt:10d}{params.depth:10d}         0         1"
        )

        # Tiebreak specific
        if contact.contact_type == ContactType.TIEBREAK and params.nfls > 0:
            lines.append(f"$#    nfls      sfls       ")
            lines.append(f"{params.nfls:10.1f}{params.sfls:10.1f}")

        lines.append("")  # Blank line after card

        return "\n".join(lines)

    def generate_summary_report(
        self,
        contacts: List[ContactPair]
    ) -> str:
        """Generate text summary of contacts."""
        lines = []
        lines.append("=" * 60)
        lines.append("ASSEMBLY CONTACT SUMMARY")
        lines.append("=" * 60)
        lines.append("")

        # Count by type
        type_counts = {}
        for contact in contacts:
            ctype = contact.contact_type.value
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        lines.append(f"Total contact pairs: {len(contacts)}")
        lines.append("")
        lines.append("By type:")
        for ctype, count in sorted(type_counts.items()):
            lines.append(f"  {ctype:15s}: {count:3d}")

        lines.append("")
        lines.append("Contact details:")
        lines.append("-" * 60)

        for i, contact in enumerate(contacts):
            lines.append(f"Contact #{i+1}:")
            lines.append(f"  Master: {contact.master_part_name}")
            lines.append(f"  Slave:  {contact.slave_part_name}")
            lines.append(f"  Type:   {contact.contact_type.value}")
            lines.append(f"  Gap:    {contact.gap_distance:.3f} mm")
            lines.append(f"  Area:   {contact.contact_area:.1f} mm²")
            lines.append(f"  Params: fs={contact.parameters.fs:.2f}, soft={contact.parameters.soft}")
            lines.append("")

        return "\n".join(lines)
