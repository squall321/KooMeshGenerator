"""
Preprocessing Package
=====================

Geometry preprocessing tools for KooMeshGenerator.

- GeometryAnalyzer: Analyze geometry (volume, area, face count, etc.)
- GeometryCleaner: Clean geometry (remove features, heal surfaces)
- GeometryInfo: Geometry analysis results
- CleaningResult: Cleaning operation results

Author: KooMeshGenerator Team
"""

from .geometry_analyzer import GeometryAnalyzer, GeometryInfo
from .geometry_cleaner import GeometryCleaner, CleaningResult

__all__ = [
    'GeometryAnalyzer',
    'GeometryInfo',
    'GeometryCleaner',
    'CleaningResult',
]
