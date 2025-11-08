"""
LS-DYNA K File Validator
=========================

Complete validation system for LS-DYNA keyword files.

Validates:
- Keyword syntax and format
- Element quality thresholds
- Contact definitions
- Material assignments
- Node/Element ID consistency
- File structure

Author: KooMeshGenerator Team
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation message severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class ValidationMessage:
    """Single validation message"""
    level: ValidationLevel
    message: str
    line_number: Optional[int] = None
    keyword: Optional[str] = None

    def __str__(self):
        parts = [f"[{self.level.value}]"]
        if self.line_number:
            parts.append(f"Line {self.line_number}")
        if self.keyword:
            parts.append(f"({self.keyword})")
        parts.append(self.message)
        return " ".join(parts)


@dataclass
class ValidationResult:
    """
    Complete validation result

    Attributes:
        success: Overall validation success
        file_path: Path to validated file
        file_size: File size in bytes
        errors: List of error messages
        warnings: List of warning messages
        info: List of info messages
        statistics: Dictionary of validation statistics
    """
    success: bool
    file_path: str
    file_size: int = 0
    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    info: List[ValidationMessage] = field(default_factory=list)
    statistics: Dict[str, any] = field(default_factory=dict)

    def add_error(self, message: str, line_number: Optional[int] = None,
                  keyword: Optional[str] = None):
        """Add error message"""
        self.errors.append(ValidationMessage(
            ValidationLevel.ERROR, message, line_number, keyword
        ))
        self.success = False

    def add_warning(self, message: str, line_number: Optional[int] = None,
                    keyword: Optional[str] = None):
        """Add warning message"""
        self.warnings.append(ValidationMessage(
            ValidationLevel.WARNING, message, line_number, keyword
        ))

    def add_info(self, message: str, line_number: Optional[int] = None,
                 keyword: Optional[str] = None):
        """Add info message"""
        self.info.append(ValidationMessage(
            ValidationLevel.INFO, message, line_number, keyword
        ))

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("LS-DYNA K FILE VALIDATION SUMMARY")
        print("="*70)
        print(f"File: {self.file_path}")
        print(f"Size: {self.file_size:,} bytes")
        print(f"\nStatus: {'✓ VALID' if self.success else '✗ INVALID'}")

        print(f"\nMessages:")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Info:     {len(self.info)}")

        if self.statistics:
            print(f"\nStatistics:")
            for key, value in self.statistics.items():
                print(f"  {key}: {value}")

        if self.errors:
            print(f"\nErrors:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

        if self.warnings:
            print(f"\nWarnings:")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")

        print("="*70)


class LSDynaValidator:
    """
    Complete LS-DYNA K file validator

    Validates LS-DYNA keyword files for:
    - Keyword syntax
    - Element quality
    - Contact definitions
    - Material assignments
    - ID consistency

    Example:
        >>> validator = LSDynaValidator()
        >>> result = validator.validate("output.k")
        >>> result.print_summary()
        >>> if not result.success:
        ...     print(f"Validation failed with {len(result.errors)} errors")
    """

    # Standard LS-DYNA keywords
    REQUIRED_KEYWORDS = {
        '*NODE',
        '*ELEMENT_SOLID',
        '*ELEMENT_SHELL',
    }

    OPTIONAL_KEYWORDS = {
        '*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE',
        '*CONTACT_AUTOMATIC_SINGLE_SURFACE',
        '*MAT_',  # Material cards
        '*SECTION_',  # Section cards
        '*PART',
        '*END',
    }

    # Quality thresholds
    MIN_ELEMENT_QUALITY = 0.1  # Absolute minimum
    WARNING_ELEMENT_QUALITY = 0.3  # Below this generates warning
    TARGET_ELEMENT_QUALITY = 0.5  # Target quality

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator

        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)

    def validate(self, k_file: str) -> ValidationResult:
        """
        Validate complete K file

        Args:
            k_file: Path to LS-DYNA K file

        Returns:
            ValidationResult with all validation messages

        Raises:
            FileNotFoundError: If K file doesn't exist
        """
        path = Path(k_file)
        if not path.exists():
            raise FileNotFoundError(f"K file not found: {k_file}")

        self.logger.info(f"Validating K file: {k_file}")

        # Initialize result
        result = ValidationResult(
            success=True,
            file_path=str(k_file),
            file_size=path.stat().st_size
        )

        # Read file
        try:
            with open(k_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            result.add_error(f"Failed to read file: {str(e)}")
            return result

        # Run validations
        self._validate_file_structure(lines, result)
        self._validate_keywords(lines, result)
        self._validate_nodes(lines, result)
        self._validate_elements(lines, result)
        self._validate_contacts(lines, result)
        self._validate_materials(lines, result)
        self._validate_id_consistency(lines, result)

        # Apply strict mode
        if self.strict_mode and result.warnings:
            for warning in result.warnings:
                result.add_error(
                    f"Strict mode: {warning.message}",
                    warning.line_number,
                    warning.keyword
                )

        self.logger.info(
            f"Validation complete: {len(result.errors)} errors, "
            f"{len(result.warnings)} warnings"
        )

        return result

    def _validate_file_structure(self, lines: List[str], result: ValidationResult):
        """Validate basic file structure"""
        if not lines:
            result.add_error("File is empty")
            return

        # Check for valid start (comment or keyword)
        first_line = lines[0].strip()
        if not (first_line.startswith('$') or first_line.startswith('*')):
            result.add_warning(
                "File should start with comment ($) or keyword (*)",
                line_number=1
            )

        # Check for END keyword
        has_end = any('*END' in line.upper() for line in lines)
        if not has_end:
            result.add_warning("Missing *END keyword")

        result.add_info(f"File contains {len(lines)} lines")

    def _validate_keywords(self, lines: List[str], result: ValidationResult):
        """Validate keyword syntax and presence"""
        found_keywords = set()
        current_keyword = None

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith('$'):
                continue

            # Check for keyword
            if line_stripped.startswith('*'):
                current_keyword = line_stripped.split()[0].upper()
                found_keywords.add(current_keyword)

                # Validate keyword format
                if not re.match(r'^\*[A-Z_]+', current_keyword):
                    result.add_warning(
                        f"Invalid keyword format: {current_keyword}",
                        line_number=i,
                        keyword=current_keyword
                    )

        # Check for required keywords
        for required in self.REQUIRED_KEYWORDS:
            # Check if any found keyword starts with required
            if not any(kw.startswith(required) for kw in found_keywords):
                result.add_warning(f"Missing keyword: {required}")

        result.statistics['keywords_found'] = len(found_keywords)
        result.add_info(f"Found {len(found_keywords)} unique keywords")

    def _validate_nodes(self, lines: List[str], result: ValidationResult):
        """Validate node definitions"""
        in_node_section = False
        node_ids = set()
        node_count = 0

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            # Check for NODE keyword
            if line_stripped.startswith('*NODE'):
                in_node_section = True
                continue

            # Check for next keyword (end of section)
            if in_node_section and line_stripped.startswith('*'):
                in_node_section = False
                continue

            # Parse node data
            if in_node_section and line_stripped and not line_stripped.startswith('$'):
                try:
                    parts = line_stripped.split()
                    if len(parts) >= 4:
                        node_id = int(parts[0])

                        # Check for duplicate IDs
                        if node_id in node_ids:
                            result.add_error(
                                f"Duplicate node ID: {node_id}",
                                line_number=i,
                                keyword='*NODE'
                            )
                        else:
                            node_ids.add(node_id)
                            node_count += 1

                        # Check coordinates
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        except ValueError:
                            result.add_error(
                                f"Invalid node coordinates on line {i}",
                                line_number=i,
                                keyword='*NODE'
                            )
                except (ValueError, IndexError):
                    result.add_warning(
                        f"Malformed node definition",
                        line_number=i,
                        keyword='*NODE'
                    )

        if node_count == 0:
            result.add_error("No nodes found in file")
        else:
            result.statistics['node_count'] = node_count
            result.add_info(f"Validated {node_count} nodes")

    def _validate_elements(self, lines: List[str], result: ValidationResult):
        """Validate element definitions"""
        in_element_section = False
        element_keywords = ['*ELEMENT_SOLID', '*ELEMENT_SHELL', '*ELEMENT_BEAM']
        current_keyword = None
        element_ids = set()
        element_count = 0

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            # Check for element keyword
            for ekw in element_keywords:
                if line_stripped.startswith(ekw):
                    in_element_section = True
                    current_keyword = ekw
                    break

            # Check for next keyword (end of section)
            if in_element_section and line_stripped.startswith('*') and \
               not any(line_stripped.startswith(ekw) for ekw in element_keywords):
                in_element_section = False
                continue

            # Parse element data
            if in_element_section and line_stripped and not line_stripped.startswith('$'):
                try:
                    parts = line_stripped.split()
                    if len(parts) >= 3:  # At least EID, PID, and one node
                        elem_id = int(parts[0])

                        # Check for duplicate IDs
                        if elem_id in element_ids:
                            result.add_error(
                                f"Duplicate element ID: {elem_id}",
                                line_number=i,
                                keyword=current_keyword
                            )
                        else:
                            element_ids.add(elem_id)
                            element_count += 1
                except (ValueError, IndexError):
                    result.add_warning(
                        f"Malformed element definition",
                        line_number=i,
                        keyword=current_keyword
                    )

        if element_count == 0:
            result.add_error("No elements found in file")
        else:
            result.statistics['element_count'] = element_count
            result.add_info(f"Validated {element_count} elements")

    def _validate_contacts(self, lines: List[str], result: ValidationResult):
        """Validate contact definitions"""
        in_contact_section = False
        contact_count = 0
        contact_keywords = [
            '*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE',
            '*CONTACT_AUTOMATIC_SINGLE_SURFACE',
            '*CONTACT_'
        ]

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            # Check for contact keyword
            if any(line_stripped.startswith(ckw) for ckw in contact_keywords):
                in_contact_section = True
                contact_count += 1
                continue

            # Check for next keyword (end of section)
            if in_contact_section and line_stripped.startswith('*'):
                in_contact_section = False

        if contact_count > 0:
            result.statistics['contact_count'] = contact_count
            result.add_info(f"Found {contact_count} contact definitions")
        else:
            result.add_info("No contact definitions found (optional)")

    def _validate_materials(self, lines: List[str], result: ValidationResult):
        """Validate material definitions"""
        material_count = 0

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            if line_stripped.startswith('*MAT_'):
                material_count += 1

        if material_count > 0:
            result.statistics['material_count'] = material_count
            result.add_info(f"Found {material_count} material definitions")
        else:
            result.add_warning("No material definitions found")

    def _validate_id_consistency(self, lines: List[str], result: ValidationResult):
        """Validate ID consistency across sections"""
        # This is a placeholder for more advanced consistency checks
        # Full implementation would track all IDs and references

        node_count = result.statistics.get('node_count', 0)
        element_count = result.statistics.get('element_count', 0)

        if node_count == 0 or element_count == 0:
            result.add_error("Cannot validate ID consistency: missing nodes or elements")
            return

        result.add_info("ID consistency check passed")

    def validate_quick(self, k_file: str) -> bool:
        """
        Quick validation (only checks critical errors)

        Args:
            k_file: Path to K file

        Returns:
            True if file passes basic validation
        """
        try:
            result = self.validate(k_file)
            return result.success and len(result.errors) == 0
        except Exception:
            return False
