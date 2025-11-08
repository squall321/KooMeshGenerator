"""
Workflow Configuration Schema
==============================

Pydantic models for workflow configuration files.
These configs define complete meshing workflows including input files,
meshing parameters, quality checks, contact detection, material assignments, etc.

Author: KooMeshGenerator Team
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class ElementTypeEnum(str, Enum):
    """Element type options"""
    TET4 = "tet4"
    TET10 = "tet10"
    HEX8 = "hex8"
    HEX20 = "hex20"
    HEX27 = "hex27"
    AUTO = "auto"


class MeshAlgorithmEnum(str, Enum):
    """Meshing algorithm options"""
    DELAUNAY = "delaunay"
    FRONTAL = "frontal"
    AUTOMATIC = "automatic"


class OutputFormatEnum(str, Enum):
    """Output format options"""
    LSDYNA = "lsdyna"
    ABAQUS = "abaqus"
    NASTRAN = "nastran"
    VTK = "vtk"


# ============================================================================
# Workflow Config Sections
# ============================================================================

class ProjectConfig(BaseModel):
    """Project metadata"""
    name: str = Field(description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    output_dir: str = Field("output", description="Output directory")

    model_config = ConfigDict(extra='forbid')


class InputConfig(BaseModel):
    """Input files configuration"""
    step_files: List[str] = Field(description="List of STEP files to process")
    working_dir: Optional[str] = Field(None, description="Working directory for relative paths")

    model_config = ConfigDict(extra='forbid')

    @field_validator('step_files')
    @classmethod
    def validate_step_files(cls, v):
        if not v:
            raise ValueError("At least one STEP file must be specified")
        return v


class BoundaryLayerConfig(BaseModel):
    """Boundary layer mesh configuration"""
    enabled: bool = Field(False, description="Enable boundary layer meshing")
    thickness: float = Field(0.5, gt=0, description="Boundary layer thickness")
    num_layers: int = Field(3, ge=1, le=20, description="Number of boundary layers")
    growth_ratio: float = Field(1.2, ge=1.0, le=3.0, description="Layer growth ratio")
    surfaces: Optional[List[str]] = Field(None, description="Surfaces to apply boundary layer")

    model_config = ConfigDict(extra='forbid')


class MeshingConfig(BaseModel):
    """Meshing parameters configuration"""
    algorithm: MeshAlgorithmEnum = Field(MeshAlgorithmEnum.DELAUNAY, description="Meshing algorithm")
    mesh_size: float = Field(1.0, gt=0, description="Target mesh element size")
    element_type: ElementTypeEnum = Field(ElementTypeEnum.AUTO, description="Element type")
    optimize: bool = Field(True, description="Optimize mesh quality")
    boundary_layer: Optional[BoundaryLayerConfig] = Field(None, description="Boundary layer configuration")

    model_config = ConfigDict(extra='forbid')


class QualityThresholdsConfig(BaseModel):
    """Quality thresholds"""
    aspect_ratio: float = Field(10.0, gt=0, description="Maximum aspect ratio")
    jacobian: float = Field(0.1, gt=0, lt=1, description="Minimum Jacobian")
    skewness: float = Field(0.8, gt=0, lt=1, description="Maximum skewness")

    model_config = ConfigDict(extra='forbid')


class QualityConfig(BaseModel):
    """Quality checking configuration"""
    enabled: bool = Field(True, description="Enable quality checking")
    thresholds: QualityThresholdsConfig = Field(default_factory=QualityThresholdsConfig, description="Quality thresholds")
    checks: List[str] = Field(default_factory=lambda: ["aspect_ratio", "jacobian", "skewness"], description="Quality checks to perform")
    report_format: str = Field("html", description="Report format (html, json, text)")
    report_file: Optional[str] = Field(None, description="Report output file")

    model_config = ConfigDict(extra='forbid')


class ContactConfig(BaseModel):
    """Contact detection configuration"""
    enabled: bool = Field(True, description="Enable contact detection")
    auto_detect: bool = Field(True, description="Automatically detect contacts")
    tolerance: float = Field(0.1, gt=0, description="Contact detection tolerance")
    self_contact: bool = Field(True, description="Detect self-contact")
    min_angle: float = Field(120.0, ge=0, le=180, description="Minimum angle for self-contact (degrees)")
    export_format: str = Field("lsdyna", description="Contact export format")

    model_config = ConfigDict(extra='forbid')


class MaterialsConfig(BaseModel):
    """Materials configuration"""
    library: Optional[str] = Field(None, description="Material library file path")
    assignments: Dict[str, str] = Field(default_factory=dict, description="Part name to material mapping")
    export_cards: bool = Field(True, description="Export material cards")

    model_config = ConfigDict(extra='forbid')


class OutputConfig(BaseModel):
    """Output configuration"""
    format: OutputFormatEnum = Field(OutputFormatEnum.LSDYNA, description="Output format")
    filename: str = Field("output.k", description="Output filename")
    include_contact: bool = Field(True, description="Include contact definitions")
    include_materials: bool = Field(True, description="Include material definitions")
    separate_parts: bool = Field(False, description="Write parts to separate files")

    model_config = ConfigDict(extra='forbid')


class ParallelConfig(BaseModel):
    """Parallel processing configuration"""
    enabled: bool = Field(False, description="Enable parallel processing")
    n_jobs: int = Field(-1, description="Number of parallel jobs (-1 = all cores)")
    batch_size: int = Field(100, ge=1, description="Batch size for parallel processing")

    model_config = ConfigDict(extra='forbid')


class ScreenshotConfig(BaseModel):
    """Screenshot configuration"""
    metric: str = Field("aspect_ratio", description="Quality metric to visualize")
    filename: str = Field("screenshot.png", description="Screenshot filename")
    view: str = Field("isometric", description="Camera view")
    window_size: List[int] = Field([1920, 1080], description="Window size [width, height]")

    model_config = ConfigDict(extra='forbid')

    @field_validator('window_size')
    @classmethod
    def validate_window_size(cls, v):
        if len(v) != 2:
            raise ValueError("window_size must be [width, height]")
        if v[0] <= 0 or v[1] <= 0:
            raise ValueError("window_size dimensions must be positive")
        return v


class VisualizationConfig(BaseModel):
    """Visualization configuration"""
    enabled: bool = Field(False, description="Enable visualization")
    screenshots: List[ScreenshotConfig] = Field(default_factory=list, description="Screenshots to generate")

    model_config = ConfigDict(extra='forbid')


# ============================================================================
# Main Workflow Config
# ============================================================================

class WorkflowConfig(BaseModel):
    """
    Complete workflow configuration

    This model defines a complete meshing workflow including:
    - Project metadata
    - Input files
    - Meshing parameters
    - Quality checking
    - Contact detection
    - Material assignments
    - Output settings
    - Parallel processing
    - Visualization

    Example:
        >>> config = WorkflowConfig.from_yaml("config.yaml")
        >>> print(config.project.name)
        >>> config.meshing.mesh_size = 2.0
    """
    project: ProjectConfig
    input: InputConfig
    meshing: MeshingConfig = Field(default_factory=MeshingConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    contact: ContactConfig = Field(default_factory=ContactConfig)
    materials: Optional[MaterialsConfig] = Field(None)
    output: OutputConfig = Field(default_factory=OutputConfig)
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)

    model_config = ConfigDict(extra='forbid')

    @classmethod
    def from_yaml(cls, filepath: str) -> 'WorkflowConfig':
        """
        Load workflow config from YAML file

        Args:
            filepath: Path to YAML config file

        Returns:
            WorkflowConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If config is invalid
        """
        import yaml

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml(self, filepath: str):
        """
        Save workflow config to YAML file

        Args:
            filepath: Path to save YAML config file
        """
        import yaml

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and write
        data = self.model_dump(exclude_none=True)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.model_dump(exclude_none=True)

    def apply_overrides(self, overrides: Dict[str, Any]):
        """
        Apply overrides to configuration

        Args:
            overrides: Dictionary of overrides in dot notation
                      e.g., {"meshing.mesh_size": 2.0}
        """
        for key, value in overrides.items():
            parts = key.split('.')
            obj = self

            # Navigate to the target object
            for part in parts[:-1]:
                obj = getattr(obj, part)

            # Set the final value
            setattr(obj, parts[-1], value)
