"""
Contact Type Classification

Automatically classifies contact types based on geometry and material properties.
"""

from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import numpy as np
import logging


class ContactType(Enum):
    """Types of contact interactions"""
    AUTOMATIC = "automatic"  # General automatic contact
    TIED = "tied"  # Fully bonded (welded, glued)
    SLIDING = "sliding"  # Friction sliding contact
    TIEBREAK = "tiebreak"  # Breakable connection (spot weld)
    FORMING = "forming"  # Metal forming contact (tool-part)
    ERODING = "eroding"  # Eroding contact for element deletion


@dataclass
class ContactParameters:
    """LS-DYNA contact parameters"""
    fs: float = 0.0  # Static friction coefficient
    fd: float = 0.0  # Dynamic friction coefficient
    soft: int = 0  # Penalty/constraint formulation (0=constraint, 1=penalty, 2=soft)
    depth: int = 5  # Search depth multiplier
    sbopt: int = 0  # Bucket sort option for slave
    mbopt: int = 0  # Bucket sort option for master

    # Tiebreak specific
    option: int = 0  # Contact option (9=tiebreak)
    nfls: float = 0.0  # Normal failure stress (MPa)
    sfls: float = 0.0  # Shear failure stress (MPa)

    # Forming specific
    fct: float = 0.0  # Coulomb friction scaling factor

    def to_lsdyna_dict(self) -> Dict[str, Any]:
        """Convert to LS-DYNA keyword format"""
        return {
            'FS': self.fs,
            'FD': self.fd,
            'SOFT': self.soft,
            'DEPTH': self.depth,
            'SBOPT': self.sbopt,
            'MBOPT': self.mbopt,
            'OPTION': self.option if self.option > 0 else None,
            'NFLS': self.nfls if self.nfls > 0 else None,
            'SFLS': self.sfls if self.sfls > 0 else None,
            'FCT': self.fct if self.fct > 0 else None
        }


class ContactClassifier:
    """
    Automatically classify contact types and optimize parameters.

    Classification based on:
    - Gap distance
    - Surface orientation
    - Contact area
    - Material combination
    - Simulation type

    Example:
        >>> classifier = ContactClassifier()
        >>> contact_type = classifier.classify_contact_type(
        ...     gap=0.005,
        ...     angle=2.0,
        ...     area=50.0,
        ...     material1='Steel_Mild',
        ...     material2='Steel_Mild'
        ... )
        >>> params = classifier.optimize_parameters(contact_type, materials)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def classify_contact_type(
        self,
        gap: float,
        surface_angle: float,
        contact_area: float,
        material1: Optional[str] = None,
        material2: Optional[str] = None,
        simulation_type: str = "crash"
    ) -> ContactType:
        """
        Classify contact type based on geometric and material properties.

        Args:
            gap: Gap distance between surfaces (mm)
            surface_angle: Angle between surface normals (degrees)
            contact_area: Contact surface area (mm²)
            material1: Material name for first surface
            material2: Material name for second surface
            simulation_type: Type of simulation (crash, forming, etc.)

        Returns:
            ContactType enum

        Raises:
            ValueError: If parameters are invalid

        Classification Rules:
        - gap < 0.01mm AND area < 10mm² → TIEBREAK (spot weld)
        - gap < 0.01mm → TIED (bonded)
        - angle > 80° → SLIDING (perpendicular surfaces)
        - area > 100mm² AND angle < 5° → FORMING (large parallel surfaces)
        - otherwise → AUTOMATIC
        """
        # Input validation
        if gap is None or gap < 0:
            raise ValueError(f"gap must be non-negative, got {gap}")

        if surface_angle is None or surface_angle < 0 or surface_angle > 180:
            raise ValueError(f"surface_angle must be in [0, 180] degrees, got {surface_angle}")

        if contact_area is None or contact_area <= 0:
            raise ValueError(f"contact_area must be positive, got {contact_area}")

        if simulation_type not in ['crash', 'forming', 'impact', 'drop_test']:
            self.logger.warning(f"Unknown simulation_type: {simulation_type}, using 'crash'")
            simulation_type = 'crash'

        self.logger.debug(
            f"Classifying contact: gap={gap:.3f}mm, angle={surface_angle:.1f}°, "
            f"area={contact_area:.1f}mm²"
        )

        # Rule 1: Very tight gap with small area = spot weld
        if gap < 0.01 and contact_area < 10.0:
            self.logger.info(
                f"Classified as TIEBREAK (spot weld): "
                f"gap={gap:.3f}mm, area={contact_area:.1f}mm²"
            )
            return ContactType.TIEBREAK

        # Rule 2: Very tight gap = bonded connection
        if gap < 0.01:
            self.logger.info(
                f"Classified as TIED: gap={gap:.3f}mm"
            )
            return ContactType.TIED

        # Rule 3: Nearly perpendicular surfaces = sliding
        if surface_angle > 80:
            self.logger.info(
                f"Classified as SLIDING: angle={surface_angle:.1f}°"
            )
            return ContactType.SLIDING

        # Rule 4: Large parallel surfaces = forming contact
        if contact_area > 100.0 and surface_angle < 5:
            # Check for tool-part combination
            if material1 and material2:
                if self._is_tool_part_combination(material1, material2):
                    self.logger.info(
                        f"Classified as FORMING: "
                        f"area={contact_area:.1f}mm², angle={surface_angle:.1f}°, "
                        f"tool-part materials"
                    )
                    return ContactType.FORMING

        # Rule 5: Eroding contact for high-speed impact
        if simulation_type == "impact" and gap > 1.0:
            self.logger.info(
                f"Classified as ERODING: simulation_type={simulation_type}"
            )
            return ContactType.ERODING

        # Default: automatic contact
        self.logger.info("Classified as AUTOMATIC (default)")
        return ContactType.AUTOMATIC

    def _is_tool_part_combination(self, material1: str, material2: str) -> bool:
        """Check if material combination is tool-part."""
        tools = ['Tool_Steel', 'Rigid', 'Carbide']
        parts = ['Aluminum', 'Steel_Mild', 'Steel_HighStrength']

        mat1_is_tool = any(tool in material1 for tool in tools)
        mat2_is_tool = any(tool in material2 for tool in tools)
        mat1_is_part = any(part in material1 for part in parts)
        mat2_is_part = any(part in material2 for part in parts)

        return (mat1_is_tool and mat2_is_part) or (mat2_is_tool and mat1_is_part)

    def optimize_parameters(
        self,
        contact_type: ContactType,
        material1: Optional[str] = None,
        material2: Optional[str] = None,
        simulation_type: str = "crash"
    ) -> ContactParameters:
        """
        Optimize contact parameters for given contact type.

        Args:
            contact_type: Type of contact
            material1: First material name
            material2: Second material name
            simulation_type: Simulation type

        Returns:
            ContactParameters with optimized values

        Raises:
            TypeError: If contact_type is not a ContactType enum
            ValueError: If parameters are invalid
        """
        # Input validation
        if contact_type is None:
            raise TypeError("contact_type cannot be None")

        if not isinstance(contact_type, ContactType):
            raise TypeError(f"contact_type must be ContactType enum, got {type(contact_type).__name__}")

        if simulation_type not in ['crash', 'forming', 'impact', 'drop_test']:
            self.logger.warning(f"Unknown simulation_type: {simulation_type}, using default parameters")

        params = ContactParameters()

        if contact_type == ContactType.AUTOMATIC:
            # General automatic contact
            params.fs = 0.3  # Default friction
            params.fd = 0.25  # Slightly lower dynamic
            params.soft = 1  # Penalty formulation
            params.depth = 5  # Standard search depth
            params.sbopt = 3  # Bucket sort both directions
            params.mbopt = 3

        elif contact_type == ContactType.TIED:
            # Tied/bonded contact
            params.fs = 0.0  # No friction needed
            params.fd = 0.0
            params.soft = 0  # Constraint formulation (stiff)
            params.depth = 2  # Smaller search depth
            params.sbopt = 3
            params.mbopt = 3

        elif contact_type == ContactType.SLIDING:
            # Sliding contact (low friction)
            params.fs = 0.1  # Low static friction
            params.fd = 0.08  # Lower dynamic
            params.soft = 1  # Penalty
            params.depth = 5
            params.sbopt = 3
            params.mbopt = 3

        elif contact_type == ContactType.FORMING:
            # Forming contact (tool-part)
            params.fs = 0.15  # Tool-part friction
            params.fd = 0.12
            params.soft = 2  # Soft constraint
            params.depth = 10  # Large search for large deformation
            params.sbopt = 3
            params.mbopt = 3
            params.fct = 1.0  # Coulomb friction scaling

        elif contact_type == ContactType.TIEBREAK:
            # Breakable connection (spot weld)
            params.fs = 0.0
            params.fd = 0.0
            params.soft = 0  # Constraint until failure
            params.depth = 2
            params.option = 9  # Tiebreak option

            # Estimate failure stresses based on materials
            params.nfls = self._estimate_normal_failure_stress(material1, material2)
            params.sfls = self._estimate_shear_failure_stress(material1, material2)

        elif contact_type == ContactType.ERODING:
            # Eroding contact
            params.fs = 0.3
            params.fd = 0.25
            params.soft = 1
            params.depth = 3  # Smaller depth for eroding
            params.sbopt = 3
            params.mbopt = 3

        self.logger.info(
            f"Optimized parameters for {contact_type.value}: "
            f"fs={params.fs}, soft={params.soft}, depth={params.depth}"
        )

        return params

    def _estimate_normal_failure_stress(
        self,
        material1: Optional[str],
        material2: Optional[str]
    ) -> float:
        """Estimate normal failure stress for spot weld (MPa)."""
        # Typical spot weld tensile strength: 400-600 MPa
        # Conservative estimate
        return 500.0

    def _estimate_shear_failure_stress(
        self,
        material1: Optional[str],
        material2: Optional[str]
    ) -> float:
        """Estimate shear failure stress for spot weld (MPa)."""
        # Typically 60-80% of tensile strength
        return 400.0

    def calculate_surface_angle(
        self,
        normal1: np.ndarray,
        normal2: np.ndarray
    ) -> float:
        """
        Calculate angle between two surface normals.

        Args:
            normal1: Normal vector of first surface
            normal2: Normal vector of second surface

        Returns:
            Angle in degrees (0-180)

        Raises:
            ValueError: If vectors are invalid or zero-length
            TypeError: If inputs are not numpy arrays
        """
        # Input validation
        if normal1 is None or normal2 is None:
            raise TypeError("normal vectors cannot be None")

        if not isinstance(normal1, np.ndarray) or not isinstance(normal2, np.ndarray):
            raise TypeError("normal vectors must be numpy arrays")

        if normal1.size == 0 or normal2.size == 0:
            raise ValueError("normal vectors cannot be empty")

        if len(normal1) != 3 or len(normal2) != 3:
            raise ValueError(f"normal vectors must be 3D, got shapes {normal1.shape} and {normal2.shape}")

        try:
            # Calculate norms
            norm1 = np.linalg.norm(normal1)
            norm2 = np.linalg.norm(normal2)

            if norm1 < 1e-10 or norm2 < 1e-10:
                raise ValueError(f"normal vectors cannot be zero-length: norms={norm1:.2e}, {norm2:.2e}")

            # Normalize vectors
            n1 = normal1 / norm1
            n2 = normal2 / norm2

            # Calculate angle
            cos_angle = np.dot(n1, n2)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Numerical stability

            angle_rad = np.arccos(cos_angle)
            angle_deg = np.degrees(angle_rad)

            return angle_deg

        except Exception as e:
            self.logger.error(f"Failed to calculate surface angle: {e}")
            raise RuntimeError(f"Surface angle calculation failed: {e}") from e


class ContactClassificationRules:
    """
    Predefined rules for contact classification.

    Can be loaded from YAML configuration files.
    """

    @staticmethod
    def get_automotive_rules() -> Dict[str, Any]:
        """Rules for automotive crash simulation"""
        return {
            'spot_welds': {
                'gap_threshold': 0.01,
                'area_threshold': 10.0,
                'contact_type': ContactType.TIEBREAK,
                'nfls': 500.0,  # MPa
                'sfls': 400.0   # MPa
            },
            'bolted_connections': {
                'gap_threshold': 0.05,
                'contact_type': ContactType.TIED,
            },
            'panel_interactions': {
                'gap_threshold': 1.0,
                'friction': 0.3,
                'contact_type': ContactType.AUTOMATIC
            }
        }

    @staticmethod
    def get_forming_rules() -> Dict[str, Any]:
        """Rules for metal forming simulation"""
        return {
            'tool_blank': {
                'contact_type': ContactType.FORMING,
                'friction': 0.15,
                'soft': 2
            },
            'blank_binder': {
                'contact_type': ContactType.FORMING,
                'friction': 0.12,
                'soft': 2
            }
        }

    @staticmethod
    def get_drop_test_rules() -> Dict[str, Any]:
        """Rules for drop test simulation"""
        return {
            'object_floor': {
                'contact_type': ContactType.AUTOMATIC,
                'friction': 0.4,
                'soft': 1
            },
            'self_contact': {
                'contact_type': ContactType.AUTOMATIC,
                'friction': 0.3,
                'soft': 1
            }
        }
