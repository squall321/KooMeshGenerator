"""
Error Message Templates and Helpers
====================================

This module provides:
- Common error message templates
- User-friendly error formatting
- Context-aware suggestions
- Error reporting utilities
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys


# ============================================================================
# Common Error Messages
# ============================================================================

COMMON_MESSAGES = {
    # File errors
    "file_not_found": {
        "message": "File not found: {filepath}",
        "suggestion": "Check the file path and ensure the file exists.",
        "tips": [
            "Use absolute paths to avoid path resolution issues",
            "Check for typos in the filename",
            "Verify file permissions"
        ]
    },

    "file_not_readable": {
        "message": "Cannot read file: {filepath}",
        "suggestion": "Check file permissions and that the file is not locked.",
        "tips": [
            "Ensure you have read permissions",
            "Close the file if it's open in another program",
            "Check if the file is corrupted"
        ]
    },

    # Geometry errors
    "invalid_geometry": {
        "message": "Invalid geometry detected",
        "suggestion": "Run 'koomesh geometry info' to check geometry validity.",
        "tips": [
            "Use 'koomesh geometry clean --heal-surfaces' to fix common issues",
            "Check for self-intersections and gaps",
            "Simplify complex geometry if possible"
        ]
    },

    "geometry_too_complex": {
        "message": "Geometry is too complex for automatic processing",
        "suggestion": "Simplify the geometry or increase mesh size.",
        "tips": [
            "Remove unnecessary small features",
            "Use 'koomesh geometry simplify' if available",
            "Increase mesh size to reduce element count"
        ]
    },

    # Meshing errors
    "meshing_failed": {
        "message": "Mesh generation failed",
        "suggestion": "Try adjusting mesh parameters or cleaning geometry first.",
        "tips": [
            "Increase mesh size (e.g., --mesh-size 3.0)",
            "Use --no-hex-priority for complex shapes",
            "Clean geometry with 'koomesh geometry clean' first"
        ]
    },

    "poor_quality": {
        "message": "Mesh quality below acceptable threshold",
        "suggestion": "Reduce mesh size or enable auto-refinement.",
        "tips": [
            "Use smaller mesh size for better quality",
            "Enable adaptive refinement if available",
            "Check geometry for problematic features"
        ]
    },

    # Configuration errors
    "config_invalid": {
        "message": "Configuration validation failed",
        "suggestion": "Run with --validate-only to see detailed errors.",
        "tips": [
            "Check YAML syntax",
            "Verify all required fields are present",
            "Check parameter value ranges"
        ]
    },

    # Dependency errors
    "missing_dependency": {
        "message": "Required dependency not found: {dependency}",
        "suggestion": "Install the missing dependency.",
        "tips": [
            "Run 'koomesh info' to check all dependencies",
            "See build/README.md for installation instructions",
            "Check that dependencies are in PATH"
        ]
    },

    # Memory errors
    "out_of_memory": {
        "message": "Insufficient memory for operation",
        "suggestion": "Reduce mesh density or process in batches.",
        "tips": [
            "Increase mesh size to reduce element count",
            "Use batch processing for multiple files",
            "Close other memory-intensive applications"
        ]
    },
}


# ============================================================================
# Error Message Formatting
# ============================================================================

def format_error_message(
    error_type: str,
    **kwargs
) -> str:
    """
    Format error message with context

    Args:
        error_type: Type of error (key in COMMON_MESSAGES)
        **kwargs: Context variables for message formatting

    Returns:
        Formatted error message with suggestions

    Example:
        >>> msg = format_error_message("file_not_found", filepath="/path/to/file.step")
        >>> print(msg)
    """
    if error_type not in COMMON_MESSAGES:
        return f"Unknown error: {error_type}"

    template = COMMON_MESSAGES[error_type]

    # Format message
    message = template["message"].format(**kwargs)

    # Build full error text
    lines = [
        "ERROR: " + message,
        "",
        "Suggestion: " + template["suggestion"],
    ]

    # Add tips if available
    if "tips" in template and template["tips"]:
        lines.append("")
        lines.append("Tips:")
        for tip in template["tips"]:
            lines.append(f"  • {tip}")

    return "\n".join(lines)


def print_error(
    error_type: str,
    logger=None,
    **kwargs
) -> None:
    """
    Print formatted error message

    Args:
        error_type: Type of error
        logger: Logger instance (optional)
        **kwargs: Context variables
    """
    message = format_error_message(error_type, **kwargs)

    if logger:
        logger.error(message)
    else:
        print(message, file=sys.stderr)


# ============================================================================
# Context-Aware Suggestions
# ============================================================================

def suggest_geometry_fix(issue_type: str) -> List[str]:
    """
    Suggest fixes for geometry issues

    Args:
        issue_type: Type of geometry issue

    Returns:
        List of suggested fixes
    """
    suggestions = {
        "self_intersection": [
            "Run 'koomesh geometry clean --heal-surfaces'",
            "Check CAD software for geometry repair tools",
            "Manually fix intersecting faces in CAD",
        ],
        "open_edges": [
            "Use 'koomesh geometry clean --heal-surfaces --fill-gaps 0.1'",
            "Check for missing faces in CAD",
            "Verify model is water-tight",
        ],
        "small_features": [
            "Use 'koomesh geometry clean --remove-small-features 0.5'",
            "Simplify geometry in CAD software",
            "Increase mesh size to handle small features",
        ],
        "non_manifold": [
            "Check for duplicate faces in CAD",
            "Remove internal faces",
            "Fix T-junctions and zero-thickness regions",
        ],
    }

    return suggestions.get(issue_type, [
        "Run 'koomesh geometry info' to diagnose the issue",
        "Try 'koomesh geometry clean' with various options",
        "Check geometry in CAD software",
    ])


def suggest_meshing_fix(failure_reason: str) -> List[str]:
    """
    Suggest fixes for meshing failures

    Args:
        failure_reason: Reason for meshing failure

    Returns:
        List of suggested fixes
    """
    suggestions = {
        "geometry_invalid": [
            "Clean geometry first: koomesh geometry clean input.step",
            "Check geometry validity: koomesh geometry info input.step",
            "Fix CAD model and re-export",
        ],
        "mesh_size_too_small": [
            "Increase mesh size: --mesh-size 3.0",
            "Use adaptive sizing if available",
            "Focus on region of interest",
        ],
        "complexity_high": [
            "Simplify geometry: koomesh geometry simplify",
            "Use coarser mesh: --mesh-size 5.0",
            "Remove unnecessary details",
        ],
        "element_type_incompatible": [
            "Try different element type: --element-type tet4",
            "Use --no-hex-priority for complex shapes",
            "Check geometry suitability for hex meshing",
        ],
    }

    return suggestions.get(failure_reason, [
        "Increase mesh size",
        "Clean geometry first",
        "Try different meshing parameters",
    ])


def suggest_quality_improvement(metric: str, value: float) -> List[str]:
    """
    Suggest improvements for quality issues

    Args:
        metric: Quality metric name
        value: Current metric value

    Returns:
        List of suggested improvements
    """
    suggestions = {
        "aspect_ratio": [
            "Reduce mesh size for better quality",
            "Use hex elements where geometry permits",
            "Enable adaptive refinement in problem areas",
        ],
        "jacobian": [
            "Check geometry for highly skewed features",
            "Reduce mesh size near problematic areas",
            "Use mesh smoothing if available",
        ],
        "skewness": [
            "Improve element alignment with geometry",
            "Use structured meshing where possible",
            "Refine mesh in high-skew regions",
        ],
        "min_angle": [
            "Increase mesh size slightly",
            "Use quadratic elements (tet10) if supported",
            "Enable automatic mesh optimization",
        ],
    }

    base_suggestions = suggestions.get(metric, [
        "Adjust mesh size",
        "Check geometry quality",
        "Enable mesh optimization",
    ])

    # Add value-specific suggestions
    if metric == "aspect_ratio" and value > 20:
        base_suggestions.append("Consider this a critical issue - remesh with finer size")

    return base_suggestions


# ============================================================================
# Error Reporting
# ============================================================================

def create_error_report(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = False
) -> str:
    """
    Create detailed error report

    Args:
        error: Exception instance
        context: Additional context information
        include_traceback: Include full traceback

    Returns:
        Formatted error report
    """
    import traceback
    from datetime import datetime

    lines = [
        "=" * 60,
        "ERROR REPORT",
        "=" * 60,
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Error Type: {type(error).__name__}",
        f"Error Message: {str(error)}",
        "",
    ]

    # Add context if available
    if context:
        lines.append("Context:")
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    # Add traceback if requested
    if include_traceback:
        lines.append("Traceback:")
        lines.append(traceback.format_exc())

    lines.append("=" * 60)

    return "\n".join(lines)


def save_error_report(
    error: Exception,
    output_file: Path,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save error report to file

    Args:
        error: Exception instance
        output_file: Output file path
        context: Additional context
    """
    report = create_error_report(error, context, include_traceback=True)

    with open(output_file, 'w') as f:
        f.write(report)

    print(f"Error report saved to: {output_file}", file=sys.stderr)


# ============================================================================
# User-Friendly Error Display
# ============================================================================

class ErrorDisplay:
    """Helper class for user-friendly error display"""

    @staticmethod
    def print_file_error(filepath: Path, error_type: str = "not_found"):
        """Print file-related error"""
        print_error(f"file_{error_type}", filepath=str(filepath))

    @staticmethod
    def print_geometry_error(issue: str, suggestions: List[str] = None):
        """Print geometry-related error"""
        print("ERROR: Geometry issue detected", file=sys.stderr)
        print(f"Issue: {issue}", file=sys.stderr)
        print("", file=sys.stderr)

        if suggestions is None:
            suggestions = suggest_geometry_fix(issue)

        if suggestions:
            print("Suggestions:", file=sys.stderr)
            for suggestion in suggestions:
                print(f"  • {suggestion}", file=sys.stderr)

    @staticmethod
    def print_meshing_error(reason: str, suggestions: List[str] = None):
        """Print meshing-related error"""
        print("ERROR: Meshing failed", file=sys.stderr)
        print(f"Reason: {reason}", file=sys.stderr)
        print("", file=sys.stderr)

        if suggestions is None:
            suggestions = suggest_meshing_fix(reason)

        if suggestions:
            print("Suggestions:", file=sys.stderr)
            for suggestion in suggestions:
                print(f"  • {suggestion}", file=sys.stderr)

    @staticmethod
    def print_quality_warning(metric: str, value: float, threshold: float):
        """Print quality warning"""
        print(f"WARNING: Quality issue detected", file=sys.stderr)
        print(f"Metric: {metric}", file=sys.stderr)
        print(f"Value: {value:.3f} (threshold: {threshold:.3f})", file=sys.stderr)
        print("", file=sys.stderr)

        suggestions = suggest_quality_improvement(metric, value)
        if suggestions:
            print("Suggestions:", file=sys.stderr)
            for suggestion in suggestions:
                print(f"  • {suggestion}", file=sys.stderr)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_error_suggestion(error_code: str) -> str:
    """
    Get suggestion for error code

    Args:
        error_code: Error code (e.g., "KOOMESH_201")

    Returns:
        Suggestion text
    """
    # Map error codes to suggestions
    # This can be extended based on actual error codes
    suggestions_map = {
        "KOOMESH_101": "Check file path and ensure file exists",
        "KOOMESH_201": "Run 'koomesh geometry clean --heal-surfaces'",
        "KOOMESH_301": "Increase mesh size or clean geometry first",
        "KOOMESH_401": "Run 'koomesh run config.yaml --validate-only'",
        "KOOMESH_601": "Run 'koomesh info' and check dependencies",
    }

    return suggestions_map.get(
        error_code,
        "Please check documentation or report this issue"
    )
