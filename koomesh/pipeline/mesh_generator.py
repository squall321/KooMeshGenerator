"""
Mesh Generator for Pipeline
============================

Unified mesh generator wrapper for pipeline integration.

This module integrates TetMesher and HexMesher, providing:
- Automatic mesher selection based on shape type
- Template system integration
- Unified mesh generation interface

Author: KooMeshGenerator Team
"""

import logging
from typing import List, Tuple, Any, Optional, Dict
from pathlib import Path

from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.hex_mesher import HexMesher
from koomesh.meshing.mesh_data import MeshData
from koomesh.templates.template_manager import SimulationTemplate
from koomesh.pipeline.constants import (
    DEFAULT_MESH_SIZE_MM,
    MIN_ELEMENT_SIZE_MM,
    MAX_ELEMENT_SIZE_MM,
    DEFAULT_ELEMENT_TYPE,
)

logger = logging.getLogger(__name__)


class MeshGenerationError(Exception):
    """Raised when mesh generation fails"""
    pass


class MeshGenerator:
    """
    Unified mesh generator wrapper

    This class integrates TetMesher and HexMesher, providing:
    - Automatic mesher selection based on shape type
    - Template system integration for parameter override
    - Consistent interface for all mesh types

    Example:
        >>> generator = MeshGenerator()
        >>> shapes = [(shape1, 'solid'), (shape2, 'shell')]
        >>> meshes = generator.generate(
        ...     shapes=shapes,
        ...     mesh_size=5.0,
        ...     element_type='tet4'
        ... )
        >>> print(f"Generated {len(meshes)} meshes")
    """

    def __init__(self):
        """Initialize mesh generator"""
        self.logger = logging.getLogger(__name__)
        self._tet_mesher = None
        self._hex_mesher = None

    def generate(
        self,
        shapes: List[Tuple[Any, str]],
        template: Optional[SimulationTemplate] = None,
        **kwargs
    ) -> List[MeshData]:
        """
        Generate meshes for all shapes

        Args:
            shapes: List of (shape, shape_type) tuples from GeometryProcessor
            template: Optional SimulationTemplate to override parameters
            **kwargs: Additional meshing parameters (fallback if no template)
                - mesh_size: Target element size (mm)
                - element_type: Element type ('tet4', 'hex8', etc.)
                - min_element_size: Minimum element size (mm)
                - max_element_size: Maximum element size (mm)
                - algorithm: Meshing algorithm
                - optimize: Enable mesh optimization

        Returns:
            List of MeshData objects

        Raises:
            MeshGenerationError: If mesh generation fails
            ValueError: If input parameters are invalid
        """
        if not shapes:
            raise ValueError("No shapes provided for meshing")

        self.logger.info(
            f"Generating meshes for {len(shapes)} shape(s) "
            f"(template: {template.name if template else 'None'})"
        )

        meshes = []
        errors = []

        for i, (shape, shape_type) in enumerate(shapes):
            try:
                self.logger.debug(
                    f"Meshing shape {i+1}/{len(shapes)}: type={shape_type}"
                )

                # Get meshing parameters
                params = self._get_mesh_params(shape_type, template, kwargs)

                # Select mesher
                mesher = self._select_mesher(shape_type, params['element_type'])

                # Generate mesh
                mesh = self._generate_single_mesh(
                    mesher=mesher,
                    shape=shape,
                    shape_type=shape_type,
                    params=params
                )

                meshes.append(mesh)

                self.logger.debug(
                    f"Generated mesh {i+1}: "
                    f"{mesh.num_nodes()} nodes, "
                    f"{mesh.num_elements()} elements"
                )

            except Exception as e:
                error_msg = f"Failed to mesh shape {i+1} (type={shape_type}): {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                # Continue with other shapes

        if errors and not meshes:
            # All shapes failed
            raise MeshGenerationError(
                f"Failed to generate any meshes. Errors:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        if errors:
            # Some shapes failed
            self.logger.warning(
                f"Generated {len(meshes)} meshes, {len(errors)} failed"
            )

        self.logger.info(
            f"Mesh generation complete: {len(meshes)} mesh(es) generated"
        )

        return meshes

    def _get_mesh_params(
        self,
        shape_type: str,
        template: Optional[SimulationTemplate],
        config_params: Dict
    ) -> Dict[str, Any]:
        """
        Get meshing parameters with priority: template > config > defaults

        Args:
            shape_type: Shape type ('solid', 'shell', 'beam')
            template: Optional template
            config_params: Parameters from config

        Returns:
            Dictionary of meshing parameters
        """
        params = {}

        # Start with defaults
        params['mesh_size'] = DEFAULT_MESH_SIZE_MM
        params['element_type'] = DEFAULT_ELEMENT_TYPE
        params['min_element_size'] = MIN_ELEMENT_SIZE_MM
        params['max_element_size'] = MAX_ELEMENT_SIZE_MM
        params['algorithm'] = 'delaunay'
        params['optimize'] = True

        # Apply config parameters
        if 'mesh_size' in config_params:
            params['mesh_size'] = config_params['mesh_size']
        if 'element_type' in config_params:
            params['element_type'] = config_params['element_type']
        if 'min_element_size' in config_params:
            params['min_element_size'] = config_params['min_element_size']
        if 'max_element_size' in config_params:
            params['max_element_size'] = config_params['max_element_size']
        if 'algorithm' in config_params:
            params['algorithm'] = config_params['algorithm']
        if 'optimize' in config_params:
            params['optimize'] = config_params['optimize']

        # Template overrides everything
        if template:
            params['mesh_size'] = template.target_element_size
            params['element_type'] = template.element_formulation
            params['min_element_size'] = template.min_element_size
            params['max_element_size'] = template.max_element_size
            # Template doesn't have algorithm/optimize, keep from config

        return params

    def _select_mesher(self, shape_type: str, element_type: str):
        """
        Select appropriate mesher based on shape type and element type

        Args:
            shape_type: Shape classification ('solid', 'shell', 'beam')
            element_type: Desired element type ('tet4', 'hex8', etc.)

        Returns:
            TetMesher or HexMesher instance
        """
        # Determine if we need tet or hex mesher
        use_hex = False

        if 'hex' in element_type.lower():
            use_hex = True
        elif shape_type == 'solid' and element_type == DEFAULT_ELEMENT_TYPE:
            # For solids with default element type, try hex first
            use_hex = True
        else:
            use_hex = False

        if use_hex:
            if self._hex_mesher is None:
                self._hex_mesher = HexMesher()
            return self._hex_mesher
        else:
            if self._tet_mesher is None:
                self._tet_mesher = TetMesher()
            return self._tet_mesher

    def _generate_single_mesh(
        self,
        mesher: Any,
        shape: Any,
        shape_type: str,
        params: Dict[str, Any]
    ) -> MeshData:
        """
        Generate mesh for a single shape

        Args:
            mesher: Mesher instance (TetMesher or HexMesher)
            shape: Shape to mesh
            shape_type: Shape classification
            params: Meshing parameters

        Returns:
            MeshData object

        Raises:
            MeshGenerationError: If meshing fails
        """
        try:
            # Update mesher parameters
            mesher.mesh_size = params['mesh_size']

            if isinstance(mesher, TetMesher):
                # TetMesher configuration
                mesher.min_size = params.get('min_element_size', params['mesh_size'] * 0.5)
                mesher.max_size = params.get('max_element_size', params['mesh_size'] * 2.0)
                mesher.algorithm = params.get('algorithm', 'delaunay')
                mesher.optimize = params.get('optimize', True)

                # Generate tetrahedral mesh
                mesh = mesher.mesh_shape(shape)

            elif isinstance(mesher, HexMesher):
                # HexMesher configuration
                # Try box meshing first, fallback to generic if fails
                try:
                    mesh = mesher.mesh_box(shape)
                except Exception as e:
                    self.logger.debug(f"Box meshing failed, trying tet fallback: {e}")
                    # Fallback to tet meshing
                    tet_mesher = TetMesher(
                        mesh_size=params['mesh_size'],
                        min_size=params.get('min_element_size'),
                        max_size=params.get('max_element_size')
                    )
                    mesh = tet_mesher.mesh_shape(shape)

            else:
                raise MeshGenerationError(f"Unknown mesher type: {type(mesher)}")

            return mesh

        except Exception as e:
            raise MeshGenerationError(
                f"Mesh generation failed for {shape_type}: {str(e)}"
            ) from e

    def get_statistics(self, meshes: List[MeshData]) -> Dict[str, Any]:
        """
        Get statistics about generated meshes

        Args:
            meshes: List of MeshData objects

        Returns:
            Dictionary with statistics
        """
        if not meshes:
            return {
                'total_meshes': 0,
                'total_nodes': 0,
                'total_elements': 0,
                'avg_nodes_per_mesh': 0,
                'avg_elements_per_mesh': 0,
            }

        total_nodes = sum(m.num_nodes() for m in meshes)
        total_elements = sum(m.num_elements() for m in meshes)

        return {
            'total_meshes': len(meshes),
            'total_nodes': total_nodes,
            'total_elements': total_elements,
            'avg_nodes_per_mesh': total_nodes / len(meshes),
            'avg_elements_per_mesh': total_elements / len(meshes),
        }
