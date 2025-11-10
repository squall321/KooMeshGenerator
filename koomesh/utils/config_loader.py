"""
Configuration File Loader

Loads and validates YAML configuration files for KooMeshGenerator.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class ConfigLoader:
    """
    Load and validate configuration files.

    Supports YAML format for configuration.

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load_config("koomesh_config.yaml")
        >>> mesh_size = config.get_mesh_size()
    """

    def __init__(self):
        self.config_data: Dict[str, Any] = {}
        self.config_file: Optional[Path] = None

    def load_config(self, config_path: str) -> 'ConfigLoader':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Self for method chaining

        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
            ImportError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for configuration files. "
                "Install with: pip install pyyaml"
            )

        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        if not config_file.is_file():
            raise ConfigurationError(f"Configuration path is not a file: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f) or {}

            self.config_file = config_file
            logger.info(f"Loaded configuration from {config_path}")

            # Validate configuration
            self._validate_config()

            return self

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _validate_config(self):
        """Validate loaded configuration."""
        if not isinstance(self.config_data, dict):
            raise ConfigurationError("Configuration must be a dictionary")

        # Validate known sections
        valid_sections = {'meshing', 'contact', 'materials', 'output', 'logging'}
        unknown_sections = set(self.config_data.keys()) - valid_sections

        if unknown_sections:
            logger.warning(f"Unknown configuration sections: {unknown_sections}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., "meshing.mesh_size")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("meshing.mesh_size", 5.0)
            5.0
        """
        keys = key.split('.')
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_meshing_config(self) -> Dict[str, Any]:
        """Get meshing configuration section."""
        return self.config_data.get('meshing', {})

    def get_contact_config(self) -> Dict[str, Any]:
        """Get contact configuration section."""
        return self.config_data.get('contact', {})

    def get_materials_config(self) -> Dict[str, Any]:
        """Get materials configuration section."""
        return self.config_data.get('materials', {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration section."""
        return self.config_data.get('output', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration section."""
        return self.config_data.get('logging', {})

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self.config_data.copy()

    @staticmethod
    def create_example_config(output_path: str):
        """
        Create an example configuration file.

        Args:
            output_path: Path where to save example config

        Example:
            >>> ConfigLoader.create_example_config("koomesh_config.yaml")
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required. Install with: pip install pyyaml"
            )

        example_config = {
            'meshing': {
                'mesh_size': 5.0,
                'element_type': 'SOLID',
                'refinement_factor': 0.5,
                'quality_threshold': 0.3,
                'max_iterations': 10
            },
            'contact': {
                'tolerance': 1.0,
                'auto_classify': True,
                'contact_aware_meshing': True,
                'validate': True,
                'types': {
                    'spot_weld': {
                        'gap_threshold': 0.01,
                        'area_threshold': 10.0,
                        'nfls': 500.0,
                        'sfls': 400.0
                    }
                }
            },
            'materials': {
                'template': 'automotive',
                'auto_assign': True,
                'default_material': 'Steel_Mild',
                'rules': {
                    '*hood*': 'Aluminum_5052',
                    '*pillar*': 'Steel_UltraHighStrength',
                    '*floor*': 'Steel_HighStrength'
                }
            },
            'output': {
                'format': 'lsdyna',
                'precision': 8,
                'include_comments': True,
                'compress': False
            },
            'logging': {
                'level': 'INFO',
                'file': None,
                'format': 'detailed'
            }
        }

        output_file = Path(output_path)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    example_config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2
                )

            logger.info(f"Created example configuration at {output_path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to create example config: {e}") from e


def load_config(config_path: str) -> ConfigLoader:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        ConfigLoader instance with loaded configuration

    Example:
        >>> config = load_config("koomesh_config.yaml")
        >>> mesh_size = config.get("meshing.mesh_size")
    """
    loader = ConfigLoader()
    return loader.load_config(config_path)
