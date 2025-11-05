"""
Unit tests for configuration module
"""

import pytest
from pathlib import Path
from koomesh.config import Config, MeshConfig, get_config, set_config


def test_default_config():
    """Test default configuration values"""
    config = Config()

    assert config.mesh.default_size == 1.0
    assert config.mesh.hex_enabled is True
    assert config.contact.enabled is True
    assert config.log.level == 'INFO'


def test_config_validation():
    """Test configuration validation"""
    config = Config()

    # Valid configuration should pass
    assert config.validate() is True

    # Invalid mesh size should raise error
    config.mesh.default_size = -1
    with pytest.raises(ValueError, match="must be positive"):
        config.validate()


def test_config_save_load(temp_dir):
    """Test saving and loading configuration"""
    config1 = Config()
    config1.mesh.default_size = 2.5
    config1.contact.default_friction = 0.3

    config_file = temp_dir / 'config.yaml'
    config1.save_to_file(config_file)

    # Load configuration
    config2 = Config.load_from_file(config_file)

    assert config2.mesh.default_size == 2.5
    assert config2.contact.default_friction == 0.3


def test_global_config():
    """Test global configuration instance"""
    config = get_config()
    assert isinstance(config, Config)

    new_config = Config()
    new_config.mesh.default_size = 3.0
    set_config(new_config)

    assert get_config().mesh.default_size == 3.0
