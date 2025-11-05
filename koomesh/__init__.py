"""
KooMeshGenerator - Automated mesh generation from STEP files
==============================================================

A comprehensive tool for automatic mesh generation from STEP files with
intelligent geometry analysis and LS-DYNA output.

Main Features:
- Automatic geometry classification
- Hexahedral mesh priority with tetrahedral fallback
- Hierarchy-based contact generation
- LS-DYNA keyword format output
- Cross-platform support (Linux/Windows)

Quick Start:
    >>> from koomesh.core.pipeline import MeshGenerationPipeline
    >>> pipeline = MeshGenerationPipeline({})
    >>> output_file = pipeline.run('model.step', mesh_size=1.0)

For more information, see the documentation at:
https://github.com/yourorg/KooMeshGenerator
"""

__version__ = "1.0.0"
__author__ = "KooMesh Team"
__license__ = "MIT"

# Import commonly used classes for convenience
try:
    from koomesh.config import Config
    from koomesh.utils.logger import setup_logger
except ImportError:
    # During initial setup, imports may fail
    pass

__all__ = [
    '__version__',
    '__author__',
    '__license__',
    'Config',
    'setup_logger',
]
