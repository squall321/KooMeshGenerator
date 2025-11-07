"""
Configuration Package
=====================

Configuration management for KooMeshGenerator.

- Config / KooMeshConfig: Application-wide configuration
- WorkflowConfig: Workflow-specific configuration for 'koomesh run' command

Author: KooMeshGenerator Team
"""

# Application config (from app_config.py)
from .app_config import (
    Config,
    KooMeshConfig,
    MeshConfig,
    GeometryConfig,
    ContactConfig as AppContactConfig,
    ExportConfig,
    BuildConfig,
    LogConfig,
    get_config,
    set_config,
)

# Workflow config (from workflow_schema.py)
from .workflow_schema import (
    WorkflowConfig,
    ProjectConfig,
    InputConfig,
    MeshingConfig,
    QualityConfig,
    ContactConfig,
    MaterialsConfig,
    OutputConfig,
    ParallelConfig,
    VisualizationConfig,
    BoundaryLayerConfig,
    QualityThresholdsConfig,
    ScreenshotConfig,
    ElementTypeEnum,
    MeshAlgorithmEnum,
    OutputFormatEnum,
)

__all__ = [
    # Application config
    'Config',
    'KooMeshConfig',
    'MeshConfig',
    'GeometryConfig',
    'AppContactConfig',
    'ExportConfig',
    'BuildConfig',
    'LogConfig',
    'get_config',
    'set_config',
    # Workflow config
    'WorkflowConfig',
    'ProjectConfig',
    'InputConfig',
    'MeshingConfig',
    'QualityConfig',
    'ContactConfig',
    'MaterialsConfig',
    'OutputConfig',
    'ParallelConfig',
    'VisualizationConfig',
    'BoundaryLayerConfig',
    'QualityThresholdsConfig',
    'ScreenshotConfig',
    'ElementTypeEnum',
    'MeshAlgorithmEnum',
    'OutputFormatEnum',
]
