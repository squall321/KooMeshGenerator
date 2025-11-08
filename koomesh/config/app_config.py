"""
Configuration Management for KooMeshGenerator
==============================================

This module provides centralized configuration management for the entire
application. It handles default settings, user overrides, and environment
variable configuration.

Usage:
    >>> from koomesh.config import Config
    >>> config = Config()
    >>> config.mesh.default_size
    1.0
    >>> config.mesh.default_size = 0.5
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import os
import yaml


@dataclass
class MeshConfig:
    """Mesh generation configuration"""
    default_size: float = 1.0
    min_size: float = 0.01
    max_size: float = 100.0

    # Hexahedral mesh settings
    hex_enabled: bool = True
    hex_priority: bool = True  # Try hex first before tet

    # Tetrahedral mesh settings
    tet_enabled: bool = True
    tet_algorithm: str = "delaunay"  # delaunay, frontal, etc.
    tet_optimize: bool = True

    # Hybrid mesh settings
    hybrid_enabled: bool = True
    pyramid_layer: bool = True  # Use pyramid elements at hex-tet boundary

    # Quality thresholds
    min_jacobian: float = 0.1
    max_aspect_ratio: float = 10.0
    max_skewness: float = 0.8


@dataclass
class GeometryConfig:
    """Geometry analysis configuration"""
    tolerance: float = 1e-6
    sweepable_detection: bool = True
    decomposition_enabled: bool = True
    max_decomposition_depth: int = 5

    # Shape classification
    box_tolerance: float = 1e-5
    cylinder_tolerance: float = 1e-5


@dataclass
class ContactConfig:
    """Contact generation configuration"""
    enabled: bool = True
    automatic_detection: bool = True
    distance_tolerance: float = 1e-4

    # Contact types
    tied_contact_enabled: bool = True
    surface_contact_enabled: bool = True
    automatic_contact_enabled: bool = True

    # Hierarchy rules
    sibling_contact_type: str = "tied"  # tied, surface, auto
    different_assembly_type: str = "surface"
    parent_child_type: str = "tied"

    # Contact parameters
    default_friction: float = 0.0
    default_penalty_factor: float = 1.0


@dataclass
class ExportConfig:
    """Export/output configuration"""
    format: str = "lsdyna"  # lsdyna, abaqus, nastran (future)

    # LS-DYNA specific
    lsdyna_version: str = "R13.0"
    lsdyna_precision: str = "double"  # double, single
    lsdyna_format: str = "keyword"  # keyword, structured

    # Output options
    compress_output: bool = False
    generate_include_files: bool = False
    separate_parts: bool = False


@dataclass
class BuildConfig:
    """Build environment configuration"""
    occt_root: str = "/opt/opencascade"
    gmsh_root: str = "/opt/gmsh"
    pythonocc_installed: bool = False
    gmsh_installed: bool = False


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_output: bool = True
    file_output: bool = True
    log_file: str = "koomesh.log"
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


class Config:
    """
    Main configuration class for KooMeshGenerator

    This class manages all configuration settings and provides methods
    to load/save configurations from/to files.

    Attributes:
        mesh: Mesh generation settings
        geometry: Geometry analysis settings
        contact: Contact generation settings
        export: Export/output settings
        build: Build environment settings
        log: Logging settings

    Usage:
        >>> config = Config()
        >>> config.mesh.default_size = 2.0
        >>> config.save_to_file('config.yaml')
        >>> config2 = Config.load_from_file('config.yaml')
    """

    def __init__(self):
        """Initialize configuration with default values"""
        self.mesh = MeshConfig()
        self.geometry = GeometryConfig()
        self.contact = ContactConfig()
        self.export = ExportConfig()
        self.build = BuildConfig()
        self.log = LogConfig()

        # Load from environment variables
        self._load_from_env()

        # Load from default config file if exists
        default_config = Path.home() / ".koomesh" / "config.yaml"
        if default_config.exists():
            self.load_from_file(default_config)

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Build paths
        if "CASROOT" in os.environ:
            self.build.occt_root = os.environ["CASROOT"]

        if "GMSH_ROOT" in os.environ:
            self.build.gmsh_root = os.environ["GMSH_ROOT"]

        # Mesh settings
        if "KOOMESH_DEFAULT_SIZE" in os.environ:
            try:
                self.mesh.default_size = float(os.environ["KOOMESH_DEFAULT_SIZE"])
            except ValueError:
                pass

        # Log level
        if "KOOMESH_LOG_LEVEL" in os.environ:
            self.log.level = os.environ["KOOMESH_LOG_LEVEL"].upper()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'mesh': self._dataclass_to_dict(self.mesh),
            'geometry': self._dataclass_to_dict(self.geometry),
            'contact': self._dataclass_to_dict(self.contact),
            'export': self._dataclass_to_dict(self.export),
            'build': self._dataclass_to_dict(self.build),
            'log': self._dataclass_to_dict(self.log),
        }

    @staticmethod
    def _dataclass_to_dict(obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary"""
        return {k: v for k, v in obj.__dict__.items()}

    def save_to_file(self, filepath: Path):
        """
        Save configuration to YAML file

        Args:
            filepath: Path to save configuration file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Config':
        """
        Load configuration from YAML file

        Args:
            filepath: Path to configuration file

        Returns:
            Config instance with loaded settings
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        config = cls()

        # Update configuration from loaded data
        if 'mesh' in data:
            for k, v in data['mesh'].items():
                if hasattr(config.mesh, k):
                    setattr(config.mesh, k, v)

        if 'geometry' in data:
            for k, v in data['geometry'].items():
                if hasattr(config.geometry, k):
                    setattr(config.geometry, k, v)

        if 'contact' in data:
            for k, v in data['contact'].items():
                if hasattr(config.contact, k):
                    setattr(config.contact, k, v)

        if 'export' in data:
            for k, v in data['export'].items():
                if hasattr(config.export, k):
                    setattr(config.export, k, v)

        if 'build' in data:
            for k, v in data['build'].items():
                if hasattr(config.build, k):
                    setattr(config.build, k, v)

        if 'log' in data:
            for k, v in data['log'].items():
                if hasattr(config.log, k):
                    setattr(config.log, k, v)

        return config

    def update(self, updates: Dict[str, Any]):
        """
        Update configuration from dictionary

        Args:
            updates: Dictionary with configuration updates
        """
        for section, values in updates.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def validate(self) -> bool:
        """
        Validate configuration values

        Returns:
            True if configuration is valid, raises ValueError otherwise
        """
        # Mesh validation
        if self.mesh.default_size <= 0:
            raise ValueError("mesh.default_size must be positive")

        if self.mesh.min_size >= self.mesh.max_size:
            raise ValueError("mesh.min_size must be less than mesh.max_size")

        if self.mesh.min_jacobian <= 0 or self.mesh.min_jacobian >= 1:
            raise ValueError("mesh.min_jacobian must be between 0 and 1")

        # Geometry validation
        if self.geometry.tolerance <= 0:
            raise ValueError("geometry.tolerance must be positive")

        # Contact validation
        if self.contact.distance_tolerance <= 0:
            raise ValueError("contact.distance_tolerance must be positive")

        # Log validation
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log.level not in valid_levels:
            raise ValueError(f"log.level must be one of {valid_levels}")

        return True

    def __repr__(self) -> str:
        """String representation of configuration"""
        return f"Config(mesh={self.mesh}, geometry={self.geometry}, contact={self.contact})"


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance

    Returns:
        Global Config instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config):
    """
    Set global configuration instance

    Args:
        config: Config instance to set as global
    """
    global _global_config
    _global_config = config


# Alias for consistency with newer modules
KooMeshConfig = Config
