"""
Validation Utilities

Common validation functions for input checking and data validation.
"""

from typing import Any, List, Optional, Union
from pathlib import Path
import numpy as np


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_positive_number(
    value: Union[int, float],
    name: str,
    allow_zero: bool = False
) -> Union[int, float]:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        name: Name of the parameter (for error messages)
        allow_zero: Whether to allow zero

    Returns:
        The validated value

    Raises:
        TypeError: If value is not a number
        ValueError: If value is not positive

    Example:
        >>> validate_positive_number(5.0, "tolerance")
        5.0
        >>> validate_positive_number(-1.0, "tolerance")
        ValueError: tolerance must be positive, got -1.0
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")

    if np.isnan(value) or np.isinf(value):
        raise ValueError(f"{name} must be finite, got {value}")

    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be non-negative, got {value}")
    else:
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")

    return value


def validate_range(
    value: Union[int, float],
    name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    inclusive: bool = True
) -> Union[int, float]:
    """
    Validate that a number is within a range.

    Args:
        value: Number to validate
        name: Name of the parameter
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        inclusive: Whether min/max are inclusive

    Returns:
        The validated value

    Raises:
        TypeError: If value is not a number
        ValueError: If value is out of range

    Example:
        >>> validate_range(0.5, "factor", min_value=0.0, max_value=1.0)
        0.5
        >>> validate_range(1.5, "factor", min_value=0.0, max_value=1.0)
        ValueError: factor must be in [0.0, 1.0], got 1.5
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")

    if np.isnan(value) or np.isinf(value):
        raise ValueError(f"{name} must be finite, got {value}")

    if min_value is not None:
        if inclusive:
            if value < min_value:
                raise ValueError(f"{name} must be >= {min_value}, got {value}")
        else:
            if value <= min_value:
                raise ValueError(f"{name} must be > {min_value}, got {value}")

    if max_value is not None:
        if inclusive:
            if value > max_value:
                raise ValueError(f"{name} must be <= {max_value}, got {value}")
        else:
            if value >= max_value:
                raise ValueError(f"{name} must be < {max_value}, got {value}")

    return value


def validate_list(
    value: Any,
    name: str,
    min_length: int = 0,
    max_length: Optional[int] = None,
    allow_empty: bool = True
) -> List:
    """
    Validate that value is a list with optional length constraints.

    Args:
        value: Value to validate
        name: Name of the parameter
        min_length: Minimum list length
        max_length: Maximum list length
        allow_empty: Whether to allow empty lists

    Returns:
        The validated list

    Raises:
        TypeError: If value is not a list
        ValueError: If list constraints are violated

    Example:
        >>> validate_list([1, 2, 3], "parts", min_length=1)
        [1, 2, 3]
        >>> validate_list([], "parts", allow_empty=False)
        ValueError: parts list cannot be empty
    """
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a list, got {type(value).__name__}")

    if not allow_empty and len(value) == 0:
        raise ValueError(f"{name} list cannot be empty")

    if len(value) < min_length:
        raise ValueError(
            f"{name} list must have at least {min_length} elements, got {len(value)}"
        )

    if max_length is not None and len(value) > max_length:
        raise ValueError(
            f"{name} list must have at most {max_length} elements, got {len(value)}"
        )

    return value


def validate_file_path(
    path: Union[str, Path],
    name: str,
    must_exist: bool = True,
    extensions: Optional[List[str]] = None
) -> Path:
    """
    Validate file path.

    Args:
        path: Path to validate
        name: Name of the parameter
        must_exist: Whether file must already exist
        extensions: List of allowed extensions (e.g., ['.step', '.stp'])

    Returns:
        Path object

    Raises:
        TypeError: If path is invalid type
        ValueError: If path validation fails

    Example:
        >>> validate_file_path("model.step", "input_file", extensions=['.step', '.stp'])
        Path('model.step')
    """
    if not isinstance(path, (str, Path)):
        raise TypeError(f"{name} must be a string or Path, got {type(path).__name__}")

    path_obj = Path(path)

    if must_exist:
        if not path_obj.exists():
            raise ValueError(f"{name} does not exist: {path}")

        if not path_obj.is_file():
            raise ValueError(f"{name} is not a file: {path}")

    if extensions is not None:
        ext = path_obj.suffix.lower()
        extensions_lower = [e.lower() for e in extensions]

        if ext not in extensions_lower:
            raise ValueError(
                f"{name} must have one of these extensions: {extensions}, got {ext}"
            )

    return path_obj


def validate_vector(
    value: Any,
    name: str,
    dimensions: int = 3,
    allow_zero: bool = True
) -> np.ndarray:
    """
    Validate that value is a valid vector.

    Args:
        value: Value to validate
        name: Name of the parameter
        dimensions: Expected number of dimensions
        allow_zero: Whether to allow zero-length vectors

    Returns:
        NumPy array

    Raises:
        TypeError: If value cannot be converted to array
        ValueError: If vector is invalid

    Example:
        >>> validate_vector([1, 0, 0], "normal", dimensions=3)
        array([1, 0, 0])
    """
    if not isinstance(value, np.ndarray):
        try:
            value = np.array(value)
        except Exception as e:
            raise TypeError(f"{name} must be array-like, got {type(value).__name__}") from e

    if value.size == 0:
        raise ValueError(f"{name} cannot be empty")

    if len(value) != dimensions:
        raise ValueError(
            f"{name} must be {dimensions}D, got {len(value)}D"
        )

    if not allow_zero:
        norm = np.linalg.norm(value)
        if norm < 1e-10:
            raise ValueError(f"{name} cannot be zero-length")

    return value


def validate_enum(
    value: Any,
    name: str,
    allowed_values: List[Any]
) -> Any:
    """
    Validate that value is one of allowed values.

    Args:
        value: Value to validate
        name: Name of the parameter
        allowed_values: List of allowed values

    Returns:
        The validated value

    Raises:
        ValueError: If value is not in allowed values

    Example:
        >>> validate_enum("crash", "simulation_type", ["crash", "forming", "impact"])
        "crash"
        >>> validate_enum("unknown", "simulation_type", ["crash", "forming"])
        ValueError: simulation_type must be one of ['crash', 'forming'], got 'unknown'
    """
    if value not in allowed_values:
        raise ValueError(
            f"{name} must be one of {allowed_values}, got '{value}'"
        )

    return value


def validate_dict(
    value: Any,
    name: str,
    required_keys: Optional[List[str]] = None,
    allow_extra_keys: bool = True
) -> dict:
    """
    Validate dictionary.

    Args:
        value: Value to validate
        name: Name of the parameter
        required_keys: List of required keys
        allow_extra_keys: Whether to allow keys not in required_keys

    Returns:
        The validated dictionary

    Raises:
        TypeError: If value is not a dict
        ValueError: If required keys are missing

    Example:
        >>> validate_dict({"a": 1, "b": 2}, "config", required_keys=["a"])
        {"a": 1, "b": 2}
    """
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dictionary, got {type(value).__name__}")

    if required_keys is not None:
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise ValueError(
                f"{name} is missing required keys: {missing_keys}"
            )

        if not allow_extra_keys:
            extra_keys = set(value.keys()) - set(required_keys)
            if extra_keys:
                raise ValueError(
                    f"{name} has unexpected keys: {extra_keys}"
                )

    return value
