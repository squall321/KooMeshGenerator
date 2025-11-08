"""
Mesh Quality Module
===================

Mesh quality assessment and automatic refinement for FEA simulations.
"""

from .quality_metrics import (
    MeshQualityMetrics,
    QualityAnalyzer,
    ElementQuality,
    compute_jacobian,
    compute_aspect_ratio,
    compute_skewness,
)

from .auto_remeshing import (
    AutoRemesher,
    RefinementStrategy,
    QualityThreshold,
    RemeshingResult,
)

__all__ = [
    'MeshQualityMetrics',
    'QualityAnalyzer',
    'ElementQuality',
    'compute_jacobian',
    'compute_aspect_ratio',
    'compute_skewness',
    'AutoRemesher',
    'RefinementStrategy',
    'QualityThreshold',
    'RemeshingResult',
]
