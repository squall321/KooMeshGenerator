"""
Shape Functions Module
======================

This module provides shape functions and their derivatives for various element types.

Shape functions are used for:
- Interpolation within elements
- Jacobian calculation
- Quality metrics
- Integration

Supported element types:
- HEX8: 8-node hexahedron (linear)
- HEX20: 20-node hexahedron (quadratic, serendipity)
- HEX27: 27-node hexahedron (quadratic, full)
- TET4: 4-node tetrahedron (linear)
- TET10: 10-node tetrahedron (quadratic)

Usage:
    >>> from koomesh.meshing.shape_functions import hex20_shape_functions
    >>> xi, eta, zeta = 0.0, 0.0, 0.0  # Natural coordinates
    >>> N = hex20_shape_functions(xi, eta, zeta)
    >>> print(f"Shape functions at origin: {N}")
"""

import numpy as np
from typing import Tuple


# ============================================================================
# HEX8 - 8-node hexahedron (linear)
# ============================================================================

def hex8_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX8 shape functions

    Args:
        xi, eta, zeta: Natural coordinates (-1 to 1)

    Returns:
        Array of 8 shape function values

    Node numbering (LS-DYNA convention):
        Bottom face (-Z): 0,1,2,3
        Top face (+Z): 4,5,6,7
    """
    N = np.zeros(8)

    # Corner nodes (trilinear interpolation)
    N[0] = 0.125 * (1 - xi) * (1 - eta) * (1 - zeta)
    N[1] = 0.125 * (1 + xi) * (1 - eta) * (1 - zeta)
    N[2] = 0.125 * (1 + xi) * (1 + eta) * (1 - zeta)
    N[3] = 0.125 * (1 - xi) * (1 + eta) * (1 - zeta)
    N[4] = 0.125 * (1 - xi) * (1 - eta) * (1 + zeta)
    N[5] = 0.125 * (1 + xi) * (1 - eta) * (1 + zeta)
    N[6] = 0.125 * (1 + xi) * (1 + eta) * (1 + zeta)
    N[7] = 0.125 * (1 - xi) * (1 + eta) * (1 + zeta)

    return N


def hex8_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX8 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 8) with derivatives [dN/dxi, dN/deta, dN/dzeta]
    """
    dN = np.zeros((3, 8))

    # dN/dxi
    dN[0, 0] = -0.125 * (1 - eta) * (1 - zeta)
    dN[0, 1] =  0.125 * (1 - eta) * (1 - zeta)
    dN[0, 2] =  0.125 * (1 + eta) * (1 - zeta)
    dN[0, 3] = -0.125 * (1 + eta) * (1 - zeta)
    dN[0, 4] = -0.125 * (1 - eta) * (1 + zeta)
    dN[0, 5] =  0.125 * (1 - eta) * (1 + zeta)
    dN[0, 6] =  0.125 * (1 + eta) * (1 + zeta)
    dN[0, 7] = -0.125 * (1 + eta) * (1 + zeta)

    # dN/deta
    dN[1, 0] = -0.125 * (1 - xi) * (1 - zeta)
    dN[1, 1] = -0.125 * (1 + xi) * (1 - zeta)
    dN[1, 2] =  0.125 * (1 + xi) * (1 - zeta)
    dN[1, 3] =  0.125 * (1 - xi) * (1 - zeta)
    dN[1, 4] = -0.125 * (1 - xi) * (1 + zeta)
    dN[1, 5] = -0.125 * (1 + xi) * (1 + zeta)
    dN[1, 6] =  0.125 * (1 + xi) * (1 + zeta)
    dN[1, 7] =  0.125 * (1 - xi) * (1 + zeta)

    # dN/dzeta
    dN[2, 0] = -0.125 * (1 - xi) * (1 - eta)
    dN[2, 1] = -0.125 * (1 + xi) * (1 - eta)
    dN[2, 2] = -0.125 * (1 + xi) * (1 + eta)
    dN[2, 3] = -0.125 * (1 - xi) * (1 + eta)
    dN[2, 4] =  0.125 * (1 - xi) * (1 - eta)
    dN[2, 5] =  0.125 * (1 + xi) * (1 - eta)
    dN[2, 6] =  0.125 * (1 + xi) * (1 + eta)
    dN[2, 7] =  0.125 * (1 - xi) * (1 + eta)

    return dN


# ============================================================================
# HEX20 - 20-node hexahedron (quadratic, serendipity)
# ============================================================================

def hex20_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX20 shape functions

    Args:
        xi, eta, zeta: Natural coordinates (-1 to 1)

    Returns:
        Array of 20 shape function values

    Node numbering:
        Corner nodes: 0-7
        Edge nodes: 8-19
    """
    N = np.zeros(20)

    # Corner nodes (modified to account for mid-side nodes)
    N[0] = 0.125 * (1 - xi) * (1 - eta) * (1 - zeta) * (-xi - eta - zeta - 2)
    N[1] = 0.125 * (1 + xi) * (1 - eta) * (1 - zeta) * (xi - eta - zeta - 2)
    N[2] = 0.125 * (1 + xi) * (1 + eta) * (1 - zeta) * (xi + eta - zeta - 2)
    N[3] = 0.125 * (1 - xi) * (1 + eta) * (1 - zeta) * (-xi + eta - zeta - 2)
    N[4] = 0.125 * (1 - xi) * (1 - eta) * (1 + zeta) * (-xi - eta + zeta - 2)
    N[5] = 0.125 * (1 + xi) * (1 - eta) * (1 + zeta) * (xi - eta + zeta - 2)
    N[6] = 0.125 * (1 + xi) * (1 + eta) * (1 + zeta) * (xi + eta + zeta - 2)
    N[7] = 0.125 * (1 - xi) * (1 + eta) * (1 + zeta) * (-xi + eta + zeta - 2)

    # Mid-side nodes on bottom face edges
    N[8]  = 0.25 * (1 - xi**2) * (1 - eta) * (1 - zeta)  # Between 0-1
    N[9]  = 0.25 * (1 + xi) * (1 - eta**2) * (1 - zeta)  # Between 1-2
    N[10] = 0.25 * (1 - xi**2) * (1 + eta) * (1 - zeta)  # Between 2-3
    N[11] = 0.25 * (1 - xi) * (1 - eta**2) * (1 - zeta)  # Between 3-0

    # Mid-side nodes on top face edges
    N[12] = 0.25 * (1 - xi**2) * (1 - eta) * (1 + zeta)  # Between 4-5
    N[13] = 0.25 * (1 + xi) * (1 - eta**2) * (1 + zeta)  # Between 5-6
    N[14] = 0.25 * (1 - xi**2) * (1 + eta) * (1 + zeta)  # Between 6-7
    N[15] = 0.25 * (1 - xi) * (1 - eta**2) * (1 + zeta)  # Between 7-4

    # Mid-side nodes on vertical edges
    N[16] = 0.25 * (1 - xi) * (1 - eta) * (1 - zeta**2)  # Between 0-4
    N[17] = 0.25 * (1 + xi) * (1 - eta) * (1 - zeta**2)  # Between 1-5
    N[18] = 0.25 * (1 + xi) * (1 + eta) * (1 - zeta**2)  # Between 2-6
    N[19] = 0.25 * (1 - xi) * (1 + eta) * (1 - zeta**2)  # Between 3-7

    return N


def hex20_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX20 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 20) with derivatives
    """
    dN = np.zeros((3, 20))

    # dN/dxi for corner nodes
    dN[0, 0] = -0.125 * (1 - eta) * (1 - zeta) * (-xi - eta - zeta - 2) - 0.125 * (1 - xi) * (1 - eta) * (1 - zeta)
    dN[0, 1] =  0.125 * (1 - eta) * (1 - zeta) * (xi - eta - zeta - 2) + 0.125 * (1 + xi) * (1 - eta) * (1 - zeta)
    dN[0, 2] =  0.125 * (1 + eta) * (1 - zeta) * (xi + eta - zeta - 2) + 0.125 * (1 + xi) * (1 + eta) * (1 - zeta)
    dN[0, 3] = -0.125 * (1 + eta) * (1 - zeta) * (-xi + eta - zeta - 2) - 0.125 * (1 - xi) * (1 + eta) * (1 - zeta)
    dN[0, 4] = -0.125 * (1 - eta) * (1 + zeta) * (-xi - eta + zeta - 2) - 0.125 * (1 - xi) * (1 - eta) * (1 + zeta)
    dN[0, 5] =  0.125 * (1 - eta) * (1 + zeta) * (xi - eta + zeta - 2) + 0.125 * (1 + xi) * (1 - eta) * (1 + zeta)
    dN[0, 6] =  0.125 * (1 + eta) * (1 + zeta) * (xi + eta + zeta - 2) + 0.125 * (1 + xi) * (1 + eta) * (1 + zeta)
    dN[0, 7] = -0.125 * (1 + eta) * (1 + zeta) * (-xi + eta + zeta - 2) - 0.125 * (1 - xi) * (1 + eta) * (1 + zeta)

    # dN/dxi for mid-side nodes
    dN[0, 8]  = -0.5 * xi * (1 - eta) * (1 - zeta)
    dN[0, 9]  =  0.25 * (1 - eta**2) * (1 - zeta)
    dN[0, 10] = -0.5 * xi * (1 + eta) * (1 - zeta)
    dN[0, 11] = -0.25 * (1 - eta**2) * (1 - zeta)
    dN[0, 12] = -0.5 * xi * (1 - eta) * (1 + zeta)
    dN[0, 13] =  0.25 * (1 - eta**2) * (1 + zeta)
    dN[0, 14] = -0.5 * xi * (1 + eta) * (1 + zeta)
    dN[0, 15] = -0.25 * (1 - eta**2) * (1 + zeta)
    dN[0, 16] = -0.25 * (1 - eta) * (1 - zeta**2)
    dN[0, 17] =  0.25 * (1 - eta) * (1 - zeta**2)
    dN[0, 18] =  0.25 * (1 + eta) * (1 - zeta**2)
    dN[0, 19] = -0.25 * (1 + eta) * (1 - zeta**2)

    # dN/deta for corner nodes
    dN[1, 0] = -0.125 * (1 - xi) * (1 - zeta) * (-xi - eta - zeta - 2) - 0.125 * (1 - xi) * (1 - eta) * (1 - zeta)
    dN[1, 1] = -0.125 * (1 + xi) * (1 - zeta) * (xi - eta - zeta - 2) - 0.125 * (1 + xi) * (1 - eta) * (1 - zeta)
    dN[1, 2] =  0.125 * (1 + xi) * (1 - zeta) * (xi + eta - zeta - 2) + 0.125 * (1 + xi) * (1 + eta) * (1 - zeta)
    dN[1, 3] =  0.125 * (1 - xi) * (1 - zeta) * (-xi + eta - zeta - 2) + 0.125 * (1 - xi) * (1 + eta) * (1 - zeta)
    dN[1, 4] = -0.125 * (1 - xi) * (1 + zeta) * (-xi - eta + zeta - 2) - 0.125 * (1 - xi) * (1 - eta) * (1 + zeta)
    dN[1, 5] = -0.125 * (1 + xi) * (1 + zeta) * (xi - eta + zeta - 2) - 0.125 * (1 + xi) * (1 - eta) * (1 + zeta)
    dN[1, 6] =  0.125 * (1 + xi) * (1 + zeta) * (xi + eta + zeta - 2) + 0.125 * (1 + xi) * (1 + eta) * (1 + zeta)
    dN[1, 7] =  0.125 * (1 - xi) * (1 + zeta) * (-xi + eta + zeta - 2) + 0.125 * (1 - xi) * (1 + eta) * (1 + zeta)

    # dN/deta for mid-side nodes
    dN[1, 8]  = -0.25 * (1 - xi**2) * (1 - zeta)
    dN[1, 9]  = -0.5 * (1 + xi) * eta * (1 - zeta)
    dN[1, 10] =  0.25 * (1 - xi**2) * (1 - zeta)
    dN[1, 11] = -0.5 * (1 - xi) * eta * (1 - zeta)
    dN[1, 12] = -0.25 * (1 - xi**2) * (1 + zeta)
    dN[1, 13] = -0.5 * (1 + xi) * eta * (1 + zeta)
    dN[1, 14] =  0.25 * (1 - xi**2) * (1 + zeta)
    dN[1, 15] = -0.5 * (1 - xi) * eta * (1 + zeta)
    dN[1, 16] = -0.25 * (1 - xi) * (1 - zeta**2)
    dN[1, 17] = -0.25 * (1 + xi) * (1 - zeta**2)
    dN[1, 18] =  0.25 * (1 + xi) * (1 - zeta**2)
    dN[1, 19] =  0.25 * (1 - xi) * (1 - zeta**2)

    # dN/dzeta for corner nodes
    dN[2, 0] = -0.125 * (1 - xi) * (1 - eta) * (-xi - eta - zeta - 2) - 0.125 * (1 - xi) * (1 - eta) * (1 - zeta)
    dN[2, 1] = -0.125 * (1 + xi) * (1 - eta) * (xi - eta - zeta - 2) - 0.125 * (1 + xi) * (1 - eta) * (1 - zeta)
    dN[2, 2] = -0.125 * (1 + xi) * (1 + eta) * (xi + eta - zeta - 2) - 0.125 * (1 + xi) * (1 + eta) * (1 - zeta)
    dN[2, 3] = -0.125 * (1 - xi) * (1 + eta) * (-xi + eta - zeta - 2) - 0.125 * (1 - xi) * (1 + eta) * (1 - zeta)
    dN[2, 4] =  0.125 * (1 - xi) * (1 - eta) * (-xi - eta + zeta - 2) + 0.125 * (1 - xi) * (1 - eta) * (1 + zeta)
    dN[2, 5] =  0.125 * (1 + xi) * (1 - eta) * (xi - eta + zeta - 2) + 0.125 * (1 + xi) * (1 - eta) * (1 + zeta)
    dN[2, 6] =  0.125 * (1 + xi) * (1 + eta) * (xi + eta + zeta - 2) + 0.125 * (1 + xi) * (1 + eta) * (1 + zeta)
    dN[2, 7] =  0.125 * (1 - xi) * (1 + eta) * (-xi + eta + zeta - 2) + 0.125 * (1 - xi) * (1 + eta) * (1 + zeta)

    # dN/dzeta for mid-side nodes
    dN[2, 8]  = -0.25 * (1 - xi**2) * (1 - eta)
    dN[2, 9]  = -0.25 * (1 + xi) * (1 - eta**2)
    dN[2, 10] = -0.25 * (1 - xi**2) * (1 + eta)
    dN[2, 11] = -0.25 * (1 - xi) * (1 - eta**2)
    dN[2, 12] =  0.25 * (1 - xi**2) * (1 - eta)
    dN[2, 13] =  0.25 * (1 + xi) * (1 - eta**2)
    dN[2, 14] =  0.25 * (1 - xi**2) * (1 + eta)
    dN[2, 15] =  0.25 * (1 - xi) * (1 - eta**2)
    dN[2, 16] = -0.5 * (1 - xi) * (1 - eta) * zeta
    dN[2, 17] = -0.5 * (1 + xi) * (1 - eta) * zeta
    dN[2, 18] = -0.5 * (1 + xi) * (1 + eta) * zeta
    dN[2, 19] = -0.5 * (1 - xi) * (1 + eta) * zeta

    return dN


# ============================================================================
# HEX27 - 27-node hexahedron (quadratic, full)
# ============================================================================

def hex27_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX27 shape functions

    Args:
        xi, eta, zeta: Natural coordinates (-1 to 1)

    Returns:
        Array of 27 shape function values

    Node numbering:
        Corner nodes: 0-7
        Edge nodes: 8-19
        Face center nodes: 20-25
        Volume center node: 26
    """
    N = np.zeros(27)

    # Helper functions
    xi_m = 0.5 * xi * (xi - 1)
    xi_0 = (1 - xi**2)
    xi_p = 0.5 * xi * (xi + 1)

    eta_m = 0.5 * eta * (eta - 1)
    eta_0 = (1 - eta**2)
    eta_p = 0.5 * eta * (eta + 1)

    zeta_m = 0.5 * zeta * (zeta - 1)
    zeta_0 = (1 - zeta**2)
    zeta_p = 0.5 * zeta * (zeta + 1)

    # Corner nodes
    N[0] = xi_m * eta_m * zeta_m
    N[1] = xi_p * eta_m * zeta_m
    N[2] = xi_p * eta_p * zeta_m
    N[3] = xi_m * eta_p * zeta_m
    N[4] = xi_m * eta_m * zeta_p
    N[5] = xi_p * eta_m * zeta_p
    N[6] = xi_p * eta_p * zeta_p
    N[7] = xi_m * eta_p * zeta_p

    # Edge nodes on bottom face
    N[8]  = xi_0 * eta_m * zeta_m  # Between 0-1
    N[9]  = xi_p * eta_0 * zeta_m  # Between 1-2
    N[10] = xi_0 * eta_p * zeta_m  # Between 2-3
    N[11] = xi_m * eta_0 * zeta_m  # Between 3-0

    # Edge nodes on top face
    N[12] = xi_0 * eta_m * zeta_p  # Between 4-5
    N[13] = xi_p * eta_0 * zeta_p  # Between 5-6
    N[14] = xi_0 * eta_p * zeta_p  # Between 6-7
    N[15] = xi_m * eta_0 * zeta_p  # Between 7-4

    # Edge nodes on vertical edges
    N[16] = xi_m * eta_m * zeta_0  # Between 0-4
    N[17] = xi_p * eta_m * zeta_0  # Between 1-5
    N[18] = xi_p * eta_p * zeta_0  # Between 2-6
    N[19] = xi_m * eta_p * zeta_0  # Between 3-7

    # Face center nodes
    N[20] = xi_0 * eta_0 * zeta_m  # Bottom face (-Z)
    N[21] = xi_0 * eta_0 * zeta_p  # Top face (+Z)
    N[22] = xi_0 * eta_m * zeta_0  # Front face (-Y)
    N[23] = xi_0 * eta_p * zeta_0  # Back face (+Y)
    N[24] = xi_m * eta_0 * zeta_0  # Left face (-X)
    N[25] = xi_p * eta_0 * zeta_0  # Right face (+X)

    # Volume center node
    N[26] = xi_0 * eta_0 * zeta_0

    return N


def hex27_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    HEX27 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 27) with derivatives
    """
    dN = np.zeros((3, 27))

    # Helper functions and derivatives
    xi_m = 0.5 * xi * (xi - 1)
    xi_0 = (1 - xi**2)
    xi_p = 0.5 * xi * (xi + 1)
    dxi_m = xi - 0.5
    dxi_0 = -2 * xi
    dxi_p = xi + 0.5

    eta_m = 0.5 * eta * (eta - 1)
    eta_0 = (1 - eta**2)
    eta_p = 0.5 * eta * (eta + 1)
    deta_m = eta - 0.5
    deta_0 = -2 * eta
    deta_p = eta + 0.5

    zeta_m = 0.5 * zeta * (zeta - 1)
    zeta_0 = (1 - zeta**2)
    zeta_p = 0.5 * zeta * (zeta + 1)
    dzeta_m = zeta - 0.5
    dzeta_0 = -2 * zeta
    dzeta_p = zeta + 0.5

    # dN/dxi
    # Corner nodes
    dN[0, 0] = dxi_m * eta_m * zeta_m
    dN[0, 1] = dxi_p * eta_m * zeta_m
    dN[0, 2] = dxi_p * eta_p * zeta_m
    dN[0, 3] = dxi_m * eta_p * zeta_m
    dN[0, 4] = dxi_m * eta_m * zeta_p
    dN[0, 5] = dxi_p * eta_m * zeta_p
    dN[0, 6] = dxi_p * eta_p * zeta_p
    dN[0, 7] = dxi_m * eta_p * zeta_p
    # Edge and face nodes
    dN[0, 8]  = dxi_0 * eta_m * zeta_m
    dN[0, 9]  = dxi_p * eta_0 * zeta_m
    dN[0, 10] = dxi_0 * eta_p * zeta_m
    dN[0, 11] = dxi_m * eta_0 * zeta_m
    dN[0, 12] = dxi_0 * eta_m * zeta_p
    dN[0, 13] = dxi_p * eta_0 * zeta_p
    dN[0, 14] = dxi_0 * eta_p * zeta_p
    dN[0, 15] = dxi_m * eta_0 * zeta_p
    dN[0, 16] = dxi_m * eta_m * zeta_0
    dN[0, 17] = dxi_p * eta_m * zeta_0
    dN[0, 18] = dxi_p * eta_p * zeta_0
    dN[0, 19] = dxi_m * eta_p * zeta_0
    dN[0, 20] = dxi_0 * eta_0 * zeta_m
    dN[0, 21] = dxi_0 * eta_0 * zeta_p
    dN[0, 22] = dxi_0 * eta_m * zeta_0
    dN[0, 23] = dxi_0 * eta_p * zeta_0
    dN[0, 24] = dxi_m * eta_0 * zeta_0
    dN[0, 25] = dxi_p * eta_0 * zeta_0
    dN[0, 26] = dxi_0 * eta_0 * zeta_0

    # dN/deta
    # Corner nodes
    dN[1, 0] = xi_m * deta_m * zeta_m
    dN[1, 1] = xi_p * deta_m * zeta_m
    dN[1, 2] = xi_p * deta_p * zeta_m
    dN[1, 3] = xi_m * deta_p * zeta_m
    dN[1, 4] = xi_m * deta_m * zeta_p
    dN[1, 5] = xi_p * deta_m * zeta_p
    dN[1, 6] = xi_p * deta_p * zeta_p
    dN[1, 7] = xi_m * deta_p * zeta_p
    # Edge and face nodes
    dN[1, 8]  = xi_0 * deta_m * zeta_m
    dN[1, 9]  = xi_p * deta_0 * zeta_m
    dN[1, 10] = xi_0 * deta_p * zeta_m
    dN[1, 11] = xi_m * deta_0 * zeta_m
    dN[1, 12] = xi_0 * deta_m * zeta_p
    dN[1, 13] = xi_p * deta_0 * zeta_p
    dN[1, 14] = xi_0 * deta_p * zeta_p
    dN[1, 15] = xi_m * deta_0 * zeta_p
    dN[1, 16] = xi_m * deta_m * zeta_0
    dN[1, 17] = xi_p * deta_m * zeta_0
    dN[1, 18] = xi_p * deta_p * zeta_0
    dN[1, 19] = xi_m * deta_p * zeta_0
    dN[1, 20] = xi_0 * deta_0 * zeta_m
    dN[1, 21] = xi_0 * deta_0 * zeta_p
    dN[1, 22] = xi_0 * deta_m * zeta_0
    dN[1, 23] = xi_0 * deta_p * zeta_0
    dN[1, 24] = xi_m * deta_0 * zeta_0
    dN[1, 25] = xi_p * deta_0 * zeta_0
    dN[1, 26] = xi_0 * deta_0 * zeta_0

    # dN/dzeta
    # Corner nodes
    dN[2, 0] = xi_m * eta_m * dzeta_m
    dN[2, 1] = xi_p * eta_m * dzeta_m
    dN[2, 2] = xi_p * eta_p * dzeta_m
    dN[2, 3] = xi_m * eta_p * dzeta_m
    dN[2, 4] = xi_m * eta_m * dzeta_p
    dN[2, 5] = xi_p * eta_m * dzeta_p
    dN[2, 6] = xi_p * eta_p * dzeta_p
    dN[2, 7] = xi_m * eta_p * dzeta_p
    # Edge and face nodes
    dN[2, 8]  = xi_0 * eta_m * dzeta_m
    dN[2, 9]  = xi_p * eta_0 * dzeta_m
    dN[2, 10] = xi_0 * eta_p * dzeta_m
    dN[2, 11] = xi_m * eta_0 * dzeta_m
    dN[2, 12] = xi_0 * eta_m * dzeta_p
    dN[2, 13] = xi_p * eta_0 * dzeta_p
    dN[2, 14] = xi_0 * eta_p * dzeta_p
    dN[2, 15] = xi_m * eta_0 * dzeta_p
    dN[2, 16] = xi_m * eta_m * dzeta_0
    dN[2, 17] = xi_p * eta_m * dzeta_0
    dN[2, 18] = xi_p * eta_p * dzeta_0
    dN[2, 19] = xi_m * eta_p * dzeta_0
    dN[2, 20] = xi_0 * eta_0 * dzeta_m
    dN[2, 21] = xi_0 * eta_0 * dzeta_p
    dN[2, 22] = xi_0 * eta_m * dzeta_0
    dN[2, 23] = xi_0 * eta_p * dzeta_0
    dN[2, 24] = xi_m * eta_0 * dzeta_0
    dN[2, 25] = xi_p * eta_0 * dzeta_0
    dN[2, 26] = xi_0 * eta_0 * dzeta_0

    return dN


# ============================================================================
# TET4 - 4-node tetrahedron (linear)
# ============================================================================

def tet4_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    TET4 shape functions

    Args:
        xi, eta, zeta: Natural coordinates (0 to 1, xi+eta+zeta <= 1)

    Returns:
        Array of 4 shape function values
    """
    N = np.zeros(4)

    N[0] = 1 - xi - eta - zeta
    N[1] = xi
    N[2] = eta
    N[3] = zeta

    return N


def tet4_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    TET4 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 4) with derivatives
    """
    dN = np.zeros((3, 4))

    # dN/dxi
    dN[0, 0] = -1.0
    dN[0, 1] =  1.0
    dN[0, 2] =  0.0
    dN[0, 3] =  0.0

    # dN/deta
    dN[1, 0] = -1.0
    dN[1, 1] =  0.0
    dN[1, 2] =  1.0
    dN[1, 3] =  0.0

    # dN/dzeta
    dN[2, 0] = -1.0
    dN[2, 1] =  0.0
    dN[2, 2] =  0.0
    dN[2, 3] =  1.0

    return dN


# ============================================================================
# TET10 - 10-node tetrahedron (quadratic)
# ============================================================================

def tet10_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    TET10 shape functions

    Args:
        xi, eta, zeta: Natural coordinates (0 to 1, xi+eta+zeta <= 1)

    Returns:
        Array of 10 shape function values

    Node numbering:
        Corner nodes: 0-3
        Edge nodes: 4-9
    """
    N = np.zeros(10)

    lambda1 = 1 - xi - eta - zeta
    lambda2 = xi
    lambda3 = eta
    lambda4 = zeta

    # Corner nodes
    N[0] = lambda1 * (2 * lambda1 - 1)
    N[1] = lambda2 * (2 * lambda2 - 1)
    N[2] = lambda3 * (2 * lambda3 - 1)
    N[3] = lambda4 * (2 * lambda4 - 1)

    # Edge nodes
    N[4] = 4 * lambda1 * lambda2  # Between 0-1
    N[5] = 4 * lambda2 * lambda3  # Between 1-2
    N[6] = 4 * lambda3 * lambda1  # Between 2-0
    N[7] = 4 * lambda1 * lambda4  # Between 0-3
    N[8] = 4 * lambda2 * lambda4  # Between 1-3
    N[9] = 4 * lambda3 * lambda4  # Between 2-3

    return N


def tet10_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    TET10 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 10) with derivatives
    """
    dN = np.zeros((3, 10))

    lambda1 = 1 - xi - eta - zeta
    lambda2 = xi
    lambda3 = eta
    lambda4 = zeta

    # dN/dxi
    dN[0, 0] = -4 * lambda1 + 1
    dN[0, 1] =  4 * lambda2 - 1
    dN[0, 2] =  0.0
    dN[0, 3] =  0.0
    dN[0, 4] =  4 * (lambda1 - lambda2)
    dN[0, 5] =  4 * lambda3
    dN[0, 6] = -4 * lambda3
    dN[0, 7] = -4 * lambda4
    dN[0, 8] =  4 * lambda4
    dN[0, 9] =  0.0

    # dN/deta
    dN[1, 0] = -4 * lambda1 + 1
    dN[1, 1] =  0.0
    dN[1, 2] =  4 * lambda3 - 1
    dN[1, 3] =  0.0
    dN[1, 4] = -4 * lambda2
    dN[1, 5] =  4 * lambda2
    dN[1, 6] =  4 * (lambda1 - lambda3)
    dN[1, 7] = -4 * lambda4
    dN[1, 8] =  0.0
    dN[1, 9] =  4 * lambda4

    # dN/dzeta
    dN[2, 0] = -4 * lambda1 + 1
    dN[2, 1] =  0.0
    dN[2, 2] =  0.0
    dN[2, 3] =  4 * lambda4 - 1
    dN[2, 4] = -4 * lambda2
    dN[2, 5] =  0.0
    dN[2, 6] = -4 * lambda3
    dN[2, 7] =  4 * (lambda1 - lambda4)
    dN[2, 8] =  4 * lambda2
    dN[2, 9] =  4 * lambda3

    return dN


# ============================================================================
# PRISM6 - 6-node prism/wedge (linear)
# ============================================================================

def prism6_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    PRISM6 shape functions

    Args:
        xi, eta: Natural coordinates for triangular base (0 to 1, xi+eta <= 1)
        zeta: Natural coordinate for height (-1 to 1)

    Returns:
        Array of 6 shape function values

    Node numbering:
        Bottom triangle: 0, 1, 2
        Top triangle: 3, 4, 5
    """
    N = np.zeros(6)

    # Bottom triangle nodes
    N[0] = 0.5 * (1 - xi - eta) * (1 - zeta)
    N[1] = 0.5 * xi * (1 - zeta)
    N[2] = 0.5 * eta * (1 - zeta)

    # Top triangle nodes
    N[3] = 0.5 * (1 - xi - eta) * (1 + zeta)
    N[4] = 0.5 * xi * (1 + zeta)
    N[5] = 0.5 * eta * (1 + zeta)

    return N


def prism6_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    PRISM6 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 6) with derivatives
    """
    dN = np.zeros((3, 6))

    # dN/dxi
    dN[0, 0] = -0.5 * (1 - zeta)
    dN[0, 1] =  0.5 * (1 - zeta)
    dN[0, 2] =  0.0
    dN[0, 3] = -0.5 * (1 + zeta)
    dN[0, 4] =  0.5 * (1 + zeta)
    dN[0, 5] =  0.0

    # dN/deta
    dN[1, 0] = -0.5 * (1 - zeta)
    dN[1, 1] =  0.0
    dN[1, 2] =  0.5 * (1 - zeta)
    dN[1, 3] = -0.5 * (1 + zeta)
    dN[1, 4] =  0.0
    dN[1, 5] =  0.5 * (1 + zeta)

    # dN/dzeta
    dN[2, 0] = -0.5 * (1 - xi - eta)
    dN[2, 1] = -0.5 * xi
    dN[2, 2] = -0.5 * eta
    dN[2, 3] =  0.5 * (1 - xi - eta)
    dN[2, 4] =  0.5 * xi
    dN[2, 5] =  0.5 * eta

    return dN


# ============================================================================
# PYRAMID5 - 5-node pyramid (linear)
# ============================================================================

def pyramid5_shape_functions(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    PYRAMID5 shape functions

    Args:
        xi, eta: Natural coordinates for base (-1 to 1)
        zeta: Natural coordinate for height (0 to 1, apex at zeta=1)

    Returns:
        Array of 5 shape function values

    Node numbering:
        Base nodes: 0, 1, 2, 3 (counter-clockwise)
        Apex node: 4
    """
    N = np.zeros(5)

    # Special handling at apex (zeta = 1)
    if abs(zeta - 1.0) < 1e-10:
        N[0] = N[1] = N[2] = N[3] = 0.0
        N[4] = 1.0
        return N

    # Base nodes (bilinear interpolation scaled by (1-zeta))
    N[0] = 0.25 * (1 - xi) * (1 - eta) * (1 - zeta)
    N[1] = 0.25 * (1 + xi) * (1 - eta) * (1 - zeta)
    N[2] = 0.25 * (1 + xi) * (1 + eta) * (1 - zeta)
    N[3] = 0.25 * (1 - xi) * (1 + eta) * (1 - zeta)

    # Apex node
    N[4] = zeta

    return N


def pyramid5_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """
    PYRAMID5 shape function derivatives

    Args:
        xi, eta, zeta: Natural coordinates

    Returns:
        Array of shape (3, 5) with derivatives
    """
    dN = np.zeros((3, 5))

    # Special handling at apex
    if abs(zeta - 1.0) < 1e-10:
        # Derivatives are undefined at apex, return zeros
        return dN

    # dN/dxi
    dN[0, 0] = -0.125 * (1 - eta) * (1 - zeta)
    dN[0, 1] =  0.125 * (1 - eta) * (1 - zeta)
    dN[0, 2] =  0.125 * (1 + eta) * (1 - zeta)
    dN[0, 3] = -0.125 * (1 + eta) * (1 - zeta)
    dN[0, 4] =  0.0

    # dN/deta
    dN[1, 0] = -0.125 * (1 - xi) * (1 - zeta)
    dN[1, 1] = -0.125 * (1 + xi) * (1 - zeta)
    dN[1, 2] =  0.125 * (1 + xi) * (1 - zeta)
    dN[1, 3] =  0.125 * (1 - xi) * (1 - zeta)
    dN[1, 4] =  0.0

    # dN/dzeta
    dN[2, 0] = -0.125 * (1 - xi) * (1 - eta)
    dN[2, 1] = -0.125 * (1 + xi) * (1 - eta)
    dN[2, 2] = -0.125 * (1 + xi) * (1 + eta)
    dN[2, 3] = -0.125 * (1 - xi) * (1 + eta)
    dN[2, 4] =  1.0

    return dN


# ============================================================================
# Utility functions
# ============================================================================

def get_shape_functions(element_type: str):
    """
    Get shape functions for a given element type

    Args:
        element_type: Element type code (e.g., 'hex8', 'hex20', 'tet10', 'prism6', 'pyramid5')

    Returns:
        Tuple of (shape_function, shape_derivatives) callables
    """
    shape_funcs = {
        'hex8': (hex8_shape_functions, hex8_shape_derivatives),
        'hex20': (hex20_shape_functions, hex20_shape_derivatives),
        'hex27': (hex27_shape_functions, hex27_shape_derivatives),
        'tet4': (tet4_shape_functions, tet4_shape_derivatives),
        'tet10': (tet10_shape_functions, tet10_shape_derivatives),
        'prism6': (prism6_shape_functions, prism6_shape_derivatives),
        'pyramid5': (pyramid5_shape_functions, pyramid5_shape_derivatives),
    }

    if element_type.lower() not in shape_funcs:
        raise ValueError(f"Unsupported element type: {element_type}")

    return shape_funcs[element_type.lower()]


def compute_jacobian(coords: np.ndarray, dN_dxi: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Compute Jacobian matrix and determinant

    Args:
        coords: Element node coordinates, shape (num_nodes, 3)
        dN_dxi: Shape function derivatives, shape (3, num_nodes)

    Returns:
        Tuple of (Jacobian matrix, determinant)
    """
    # J = dN/dxi @ coords
    J = dN_dxi @ coords  # Shape (3, 3)
    det_J = np.linalg.det(J)

    return J, det_J
