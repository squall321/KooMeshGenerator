"""
Pipeline Constants
==================

This module defines constants used throughout the mesh generation pipeline.
All magic numbers are defined here with clear explanations.
"""

# ============================================================================
# Meshing Parameters
# ============================================================================

# Default mesh size in millimeters
# Based on typical automotive crash simulation requirements
DEFAULT_MESH_SIZE_MM = 5.0

# Minimum element size in millimeters
# Below this size, elements may cause numerical issues
MIN_ELEMENT_SIZE_MM = 0.1

# Maximum element size in millimeters
# Above this size, accuracy may be compromised
MAX_ELEMENT_SIZE_MM = 100.0


# ============================================================================
# Quality Thresholds
# ============================================================================

# Minimum acceptable element quality (0-1 scale)
# Based on LS-DYNA recommendations for crash simulations
# Below 0.3: Poor quality, likely to cause errors
# 0.3-0.5: Acceptable but may affect accuracy
# 0.5-0.7: Good quality
# 0.7+: Excellent quality
MIN_ACCEPTABLE_QUALITY = 0.3

# Target quality threshold for auto-remeshing
# Elements below this may be refined if auto-remesh is enabled
TARGET_QUALITY_THRESHOLD = 0.7

# Warning quality threshold
# Elements below this generate warnings but may not be auto-remeshed
WARNING_QUALITY_THRESHOLD = 0.5


# ============================================================================
# Auto-Remeshing Parameters
# ============================================================================

# Maximum number of auto-remesh iterations
# After 3 iterations, diminishing returns typically observed
MAX_REMESH_ITERATIONS = 3

# Minimum improvement required to continue remeshing
# If quality improves less than this, stop iterating
MIN_QUALITY_IMPROVEMENT = 0.05


# ============================================================================
# Contact Detection Parameters
# ============================================================================

# Default contact tolerance in millimeters
# Distance within which surfaces are considered in contact
DEFAULT_CONTACT_TOLERANCE_MM = 1.0

# Self-contact tolerance in millimeters
# Smaller tolerance for self-contact to avoid false positives
DEFAULT_SELF_CONTACT_TOLERANCE_MM = 0.5


# ============================================================================
# Geometry Cleaning Parameters
# ============================================================================

# Geometry cleaning tolerance in millimeters
# Used for duplicate removal and surface healing
DEFAULT_GEOMETRY_TOLERANCE_MM = 1e-3  # 0.001 mm

# Minimum feature size in millimeters
# Features smaller than this may be removed during cleaning
MIN_FEATURE_SIZE_MM = 0.1


# ============================================================================
# Progress Tracking Parameters
# ============================================================================

# Minimum interval between progress updates in seconds
# Prevents excessive callback overhead during tight loops
MIN_PROGRESS_UPDATE_INTERVAL_SEC = 0.1

# Progress value bounds
MIN_PROGRESS_VALUE = 0.0
MAX_PROGRESS_VALUE = 1.0


# ============================================================================
# File Size Limits
# ============================================================================

# Maximum input file size in megabytes
# Prevents resource exhaustion from extremely large files
MAX_INPUT_FILE_SIZE_MB = 1000  # 1 GB

# Maximum total memory usage estimate in gigabytes
# Warning threshold for memory-intensive operations
MAX_MEMORY_USAGE_GB = 4.0


# ============================================================================
# Performance Parameters
# ============================================================================

# Default number of parallel jobs
# 0 means use all available CPUs
DEFAULT_PARALLEL_JOBS = 0

# Cache size limits
MAX_GEOMETRY_CACHE_SIZE_MB = 500
MAX_CONFIG_CACHE_ENTRIES = 100


# ============================================================================
# Output Parameters
# ============================================================================

# Supported report formats
SUPPORTED_REPORT_FORMATS = ['html', 'pdf', 'json', 'markdown']

# Default report format
DEFAULT_REPORT_FORMAT = 'html'

# Precision for floating point output
OUTPUT_FLOAT_PRECISION = 6


# ============================================================================
# Validation Parameters
# ============================================================================

# Element count thresholds for warnings
MIN_ELEMENTS_WARNING = 100  # Too few elements may be too coarse
MAX_ELEMENTS_WARNING = 10_000_000  # Too many elements may be too fine

# Time limits for stages (seconds)
MAX_GEOMETRY_PROCESSING_TIME_SEC = 300  # 5 minutes
MAX_MESHING_TIME_SEC = 3600  # 1 hour
MAX_QUALITY_CHECK_TIME_SEC = 600  # 10 minutes
MAX_CONTACT_DETECTION_TIME_SEC = 600  # 10 minutes
MAX_EXPORT_TIME_SEC = 300  # 5 minutes
MAX_VALIDATION_TIME_SEC = 300  # 5 minutes


# ============================================================================
# Element Type Mappings
# ============================================================================

SUPPORTED_ELEMENT_TYPES = [
    'tet4',   # 4-node tetrahedron
    'tet10',  # 10-node tetrahedron
    'hex8',   # 8-node hexahedron
    'hex20',  # 20-node hexahedron
    'shell3', # 3-node shell
    'shell4', # 4-node shell
]

DEFAULT_ELEMENT_TYPE = 'tet4'


# ============================================================================
# Refinement Strategies
# ============================================================================

SUPPORTED_REFINEMENT_STRATEGIES = [
    'adaptive',      # Refine based on quality metrics
    'uniform',       # Uniform refinement
    'quality_based', # Refine only poorest elements
    'curvature',     # Refine based on geometry curvature
]

DEFAULT_REFINEMENT_STRATEGY = 'adaptive'
