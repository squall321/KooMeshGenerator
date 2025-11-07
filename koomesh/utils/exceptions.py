"""
Custom Exception Classes for KooMeshGenerator
==============================================

This module defines a hierarchy of custom exceptions with:
- Clear error messages
- Helpful suggestions for common errors
- Context information
- Error codes for automation

Exception Hierarchy:
    KooMeshException (base)
    ├── InputError
    │   ├── FileNotFoundError
    │   ├── InvalidFileFormatError
    │   └── FileReadError
    ├── GeometryError
    │   ├── InvalidGeometryError
    │   ├── GeometryLoadError
    │   ├── SelfIntersectionError
    │   └── TopologyError
    ├── MeshingError
    │   ├── MeshGenerationError
    │   ├── MeshQualityError
    │   ├── ElementGenerationError
    │   └── MeshSizeError
    ├── ConfigError
    │   ├── ConfigValidationError
    │   ├── ConfigLoadError
    │   └── InvalidParameterError
    ├── ExportError
    │   ├── FormatNotSupportedError
    │   ├── ExportFailedError
    │   └── OutputWriteError
    └── SystemError
        ├── DependencyError
        ├── MemoryError
        └── ProcessError
"""

from typing import Optional, Dict, Any
from pathlib import Path


class KooMeshException(Exception):
    """
    Base exception for all KooMeshGenerator errors

    Attributes:
        message: Error message
        suggestion: Helpful suggestion for resolving the error
        error_code: Unique error code for automation
        context: Additional context information
    """

    error_code = "KOOMESH_000"
    default_suggestion = "Please check the documentation or report this issue."

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception

        Args:
            message: Error message
            suggestion: Helpful suggestion (uses default if not provided)
            context: Additional context information
        """
        self.message = message
        self.suggestion = suggestion or self.default_suggestion
        self.context = context or {}

        # Build full error message
        full_message = self._build_full_message()
        super().__init__(full_message)

    def _build_full_message(self) -> str:
        """Build formatted error message with suggestion"""
        lines = [
            f"ERROR [{self.error_code}]: {self.message}",
        ]

        # Add context if available
        if self.context:
            lines.append("Context:")
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")

        # Add suggestion
        lines.append(f"Suggestion: {self.suggestion}")

        return "\n".join(lines)


# ============================================================================
# Input/Output Errors
# ============================================================================

class InputError(KooMeshException):
    """Base exception for input-related errors"""
    error_code = "KOOMESH_100"
    default_suggestion = "Check that the input file exists and is readable."


class FileNotFoundError(InputError):
    """File not found error"""
    error_code = "KOOMESH_101"
    default_suggestion = "Check the file path and ensure the file exists."

    def __init__(self, filepath: Path, **kwargs):
        message = f"File not found: {filepath}"
        context = {"filepath": str(filepath)}
        super().__init__(message, context=context, **kwargs)


class InvalidFileFormatError(InputError):
    """Invalid file format error"""
    error_code = "KOOMESH_102"
    default_suggestion = "Supported formats: STEP (.step, .stp), IGES (.iges, .igs)"

    def __init__(self, filepath: Path, expected_format: str = None, **kwargs):
        message = f"Invalid or unsupported file format: {filepath}"
        context = {"filepath": str(filepath)}
        if expected_format:
            context["expected_format"] = expected_format
        super().__init__(message, context=context, **kwargs)


class FileReadError(InputError):
    """File read error"""
    error_code = "KOOMESH_103"
    default_suggestion = "Check file permissions and that the file is not corrupted."

    def __init__(self, filepath: Path, reason: str = None, **kwargs):
        message = f"Failed to read file: {filepath}"
        if reason:
            message += f" - {reason}"
        context = {"filepath": str(filepath)}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


# ============================================================================
# Geometry Errors
# ============================================================================

class GeometryError(KooMeshException):
    """Base exception for geometry-related errors"""
    error_code = "KOOMESH_200"
    default_suggestion = "Try cleaning the geometry with 'koomesh geometry clean' first."


class InvalidGeometryError(GeometryError):
    """Invalid geometry error"""
    error_code = "KOOMESH_201"
    default_suggestion = (
        "Run 'koomesh geometry info' to check geometry validity, "
        "then use 'koomesh geometry clean --heal-surfaces' to fix issues."
    )

    def __init__(self, reason: str = None, **kwargs):
        message = "Invalid or malformed geometry detected"
        if reason:
            message += f": {reason}"
        context = {}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class GeometryLoadError(GeometryError):
    """Geometry load error"""
    error_code = "KOOMESH_202"
    default_suggestion = "Check that the STEP/IGES file is valid and not corrupted."

    def __init__(self, filepath: Path, reason: str = None, **kwargs):
        message = f"Failed to load geometry from: {filepath}"
        if reason:
            message += f" - {reason}"
        context = {"filepath": str(filepath)}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class SelfIntersectionError(GeometryError):
    """Self-intersection detected in geometry"""
    error_code = "KOOMESH_203"
    default_suggestion = (
        "Run 'koomesh geometry clean --heal-surfaces --fix-invalid' "
        "to attempt automatic repair."
    )

    def __init__(self, face_ids: list = None, **kwargs):
        message = "Self-intersecting geometry detected"
        context = {}
        if face_ids:
            message += f" (faces: {', '.join(map(str, face_ids))})"
            context["face_ids"] = face_ids
        super().__init__(message, context=context, **kwargs)


class TopologyError(GeometryError):
    """Topology error in geometry"""
    error_code = "KOOMESH_204"
    default_suggestion = "Check geometry for missing faces, open edges, or non-manifold vertices."

    def __init__(self, topology_issue: str, **kwargs):
        message = f"Topology error: {topology_issue}"
        context = {"issue": topology_issue}
        super().__init__(message, context=context, **kwargs)


# ============================================================================
# Meshing Errors
# ============================================================================

class MeshingError(KooMeshException):
    """Base exception for meshing-related errors"""
    error_code = "KOOMESH_300"
    default_suggestion = "Try adjusting mesh size or using different element type."


class MeshGenerationError(MeshingError):
    """Mesh generation failed"""
    error_code = "KOOMESH_301"
    default_suggestion = (
        "Try: 1) Increase mesh size, 2) Clean geometry first, "
        "3) Use --no-hex-priority for complex shapes."
    )

    def __init__(self, reason: str = None, **kwargs):
        message = "Mesh generation failed"
        if reason:
            message += f": {reason}"
        context = {}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class MeshQualityError(MeshingError):
    """Mesh quality below threshold"""
    error_code = "KOOMESH_302"
    default_suggestion = (
        "Reduce mesh size, use adaptive refinement, "
        "or adjust quality thresholds in config."
    )

    def __init__(self, metric: str, value: float, threshold: float, **kwargs):
        message = f"Mesh quality below threshold: {metric}={value:.3f} (threshold: {threshold:.3f})"
        context = {
            "metric": metric,
            "value": value,
            "threshold": threshold
        }
        super().__init__(message, context=context, **kwargs)


class ElementGenerationError(MeshingError):
    """Element generation error"""
    error_code = "KOOMESH_303"
    default_suggestion = "Check geometry for very small or degenerate features."

    def __init__(self, element_type: str, reason: str = None, **kwargs):
        message = f"Failed to generate {element_type} elements"
        if reason:
            message += f": {reason}"
        context = {"element_type": element_type}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class MeshSizeError(MeshingError):
    """Invalid mesh size"""
    error_code = "KOOMESH_304"
    default_suggestion = "Use mesh size between 0.1 and 100.0 mm."

    def __init__(self, mesh_size: float, **kwargs):
        message = f"Invalid mesh size: {mesh_size}"
        context = {"mesh_size": mesh_size}
        super().__init__(message, context=context, **kwargs)


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigError(KooMeshException):
    """Base exception for configuration-related errors"""
    error_code = "KOOMESH_400"
    default_suggestion = "Check your configuration file against the schema."


class ConfigValidationError(ConfigError):
    """Configuration validation failed"""
    error_code = "KOOMESH_401"
    default_suggestion = (
        "Run 'koomesh run config.yaml --validate-only' to see detailed validation errors."
    )

    def __init__(self, validation_errors: list, **kwargs):
        message = f"Configuration validation failed ({len(validation_errors)} errors)"
        context = {"errors": validation_errors}
        super().__init__(message, context=context, **kwargs)


class ConfigLoadError(ConfigError):
    """Configuration file load error"""
    error_code = "KOOMESH_402"
    default_suggestion = "Check YAML syntax and file encoding."

    def __init__(self, filepath: Path, reason: str = None, **kwargs):
        message = f"Failed to load configuration: {filepath}"
        if reason:
            message += f" - {reason}"
        context = {"filepath": str(filepath)}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class InvalidParameterError(ConfigError):
    """Invalid parameter value"""
    error_code = "KOOMESH_403"
    default_suggestion = "Check parameter value against valid range or options."

    def __init__(self, parameter: str, value: Any, valid_values: str = None, **kwargs):
        message = f"Invalid parameter value: {parameter}={value}"
        context = {"parameter": parameter, "value": value}
        if valid_values:
            message += f" (valid: {valid_values})"
            context["valid_values"] = valid_values
        super().__init__(message, context=context, **kwargs)


# ============================================================================
# Export Errors
# ============================================================================

class ExportError(KooMeshException):
    """Base exception for export-related errors"""
    error_code = "KOOMESH_500"
    default_suggestion = "Check output directory permissions and disk space."


class FormatNotSupportedError(ExportError):
    """Export format not supported"""
    error_code = "KOOMESH_501"
    default_suggestion = "Supported formats: lsdyna, abaqus, nastran, vtk, stl, obj"

    def __init__(self, format_name: str, **kwargs):
        message = f"Export format not supported: {format_name}"
        context = {"format": format_name}
        super().__init__(message, context=context, **kwargs)


class ExportFailedError(ExportError):
    """Export failed"""
    error_code = "KOOMESH_502"
    default_suggestion = "Check that mesh is valid and output path is writable."

    def __init__(self, output_path: Path, reason: str = None, **kwargs):
        message = f"Export failed: {output_path}"
        if reason:
            message += f" - {reason}"
        context = {"output_path": str(output_path)}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class OutputWriteError(ExportError):
    """Output file write error"""
    error_code = "KOOMESH_503"
    default_suggestion = "Check directory permissions and available disk space."

    def __init__(self, filepath: Path, reason: str = None, **kwargs):
        message = f"Failed to write output file: {filepath}"
        if reason:
            message += f" - {reason}"
        context = {"filepath": str(filepath)}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


# ============================================================================
# System Errors
# ============================================================================

class SystemError(KooMeshException):
    """Base exception for system-related errors"""
    error_code = "KOOMESH_600"
    default_suggestion = "Check system resources and dependencies."


class DependencyError(SystemError):
    """Missing or incompatible dependency"""
    error_code = "KOOMESH_601"
    default_suggestion = (
        "Run 'koomesh info' to check dependencies. "
        "See build/README.md for installation instructions."
    )

    def __init__(self, dependency: str, reason: str = None, **kwargs):
        message = f"Dependency error: {dependency}"
        if reason:
            message += f" - {reason}"
        context = {"dependency": dependency}
        if reason:
            context["reason"] = reason
        super().__init__(message, context=context, **kwargs)


class MemoryError(SystemError):
    """Insufficient memory"""
    error_code = "KOOMESH_602"
    default_suggestion = (
        "Try: 1) Reduce mesh density, 2) Process in batches, "
        "3) Use streaming mode for large files."
    )

    def __init__(self, required_mb: float = None, available_mb: float = None, **kwargs):
        message = "Insufficient memory"
        context = {}
        if required_mb and available_mb:
            message += f" (required: {required_mb:.1f}MB, available: {available_mb:.1f}MB)"
            context["required_mb"] = required_mb
            context["available_mb"] = available_mb
        super().__init__(message, context=context, **kwargs)


class ProcessError(SystemError):
    """Process execution error"""
    error_code = "KOOMESH_603"
    default_suggestion = "Check system logs and process output for details."

    def __init__(self, process_name: str, exit_code: int = None, **kwargs):
        message = f"Process failed: {process_name}"
        context = {"process": process_name}
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
            context["exit_code"] = exit_code
        super().__init__(message, context=context, **kwargs)
