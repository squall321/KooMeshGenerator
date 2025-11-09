Architecture Overview
=====================

KooMeshGenerator architecture and design.

Modules
-------

**Core Modules**:

- ``koomesh.meshing`` - Mesh generation
- ``koomesh.contact`` - Contact detection
- ``koomesh.materials`` - Material management
- ``koomesh.io`` - Input/output
- ``koomesh.validation`` - Mesh validation

**Design Patterns**:

- Factory pattern for mesh generators
- Strategy pattern for material assignment
- Observer pattern for progress tracking

Data Flow
---------

::

   STEP File → Geometry → Mesh → Validation → Export

See source code for implementation details.
