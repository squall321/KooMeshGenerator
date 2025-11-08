"""
Visualization Module
===================

Interactive mesh visualization using PyVista/VTK.

Features:
---------
- Interactive 3D mesh viewing
- Quality metric visualization with color mapping
- Multiple camera views (isometric, front, side, top)
- Screenshot and export capabilities
- Boundary condition visualization
- Material property display

Classes:
--------
- MeshViewer: Main interactive mesh viewer class

Example:
--------
```python
from koomesh.visualization import MeshViewer
from koomesh.meshing import TetMesher

# Create mesh
mesher = TetMesher(mesh_size=1.0)
mesh_data = mesher.mesh_shape(shape)

# Visualize
viewer = MeshViewer()
viewer.show_mesh(mesh_data)
viewer.show()
```
"""

from koomesh.visualization.mesh_viewer import MeshViewer, quick_view

__all__ = ['MeshViewer', 'quick_view']
