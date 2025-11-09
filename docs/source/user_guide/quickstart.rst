Quick Start Guide
=================

Get started with KooMeshGenerator in 5 minutes!

Your First Mesh
---------------

1. **Install** KooMeshGenerator:

.. code-block:: bash

   pip install koomesh

2. **Generate** a mesh from a STEP file:

.. code-block:: bash

   koomesh generate input.step --mesh-size 2.0

3. **Done**! Your mesh is saved as ``input.k``

Basic Workflow
--------------

Step 1: Prepare Geometry
^^^^^^^^^^^^^^^^^^^^^^^^^

KooMeshGenerator accepts CAD geometry in STEP format:

.. code-block:: bash

   # Single file
   koomesh generate part.step

   # Multiple files (assembly)
   koomesh generate part1.step part2.step part3.step

Step 2: Generate Mesh
^^^^^^^^^^^^^^^^^^^^^^

Control mesh size and quality:

.. code-block:: bash

   # Coarse mesh (fast)
   koomesh generate input.step --mesh-size 5.0

   # Medium mesh (balanced)
   koomesh generate input.step --mesh-size 2.0

   # Fine mesh (high quality)
   koomesh generate input.step --mesh-size 1.0

Step 3: Check Quality
^^^^^^^^^^^^^^^^^^^^^^

Verify mesh quality:

.. code-block:: bash

   koomesh quality check output.k

Expected output::

   ✓ Mesh quality check passed

   Quality Metrics:
     Aspect Ratio:  min=1.2, avg=2.1, max=4.5
     Jacobian:      min=0.42, avg=0.78, max=0.98
     Warpage:       min=0.0°, avg=2.5°, max=8.2°

   Elements: 15,234
   Poor quality: 12 (0.08%)

Step 4: Export
^^^^^^^^^^^^^^

Export to your target format:

.. code-block:: bash

   # Already in LS-DYNA format (.k)
   koomesh export output.k final.k

   # Or convert to other formats
   koomesh export output.k final.inp   # Abaqus
   koomesh export output.k final.bdf   # NASTRAN
   koomesh export output.k final.vtu   # VTK

Common Tasks
------------

Task 1: Mesh an Assembly
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Generate meshes for all parts
   koomesh generate assembly/*.step

   # Detect contacts between parts
   koomesh contact assembly.k --auto-classify

   # Validate
   koomesh validate assembly.k --solver lsdyna

Task 2: Contact-Aware Meshing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For better contact definition:

.. code-block:: bash

   koomesh generate assembly.step \
       --contact-aware-meshing \
       --refinement-factor 0.5

This automatically:
- Detects contact zones
- Refines mesh at contacts
- Aligns nodes across surfaces

Task 3: Material Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Automatically assign materials:

.. code-block:: bash

   # Using template
   koomesh material assign *.step --template automotive

   # Validate assignments
   koomesh material validate Steel_Mild --simulation-type crash

   # Get recommendations
   koomesh material recommend \
       --simulation-type crash \
       --min-strength 400

Task 4: Complete Crash Simulation Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Full workflow for automotive crash:

.. code-block:: bash

   # 1. Generate mesh with contact refinement
   koomesh generate assembly.step \
       --contact-aware-meshing \
       --mesh-size 2.0

   # 2. Assign materials
   koomesh material assign assembly/*.step \
       --template automotive_crash

   # 3. Detect contacts
   koomesh contact assembly.k \
       --auto-classify \
       --validate

   # 4. Check quality
   koomesh quality check assembly.k --report quality.html

   # 5. Validate for LS-DYNA
   koomesh validate assembly.k \
       --solver lsdyna \
       --simulation-type crash

   # 6. Export
   koomesh export assembly.k final_model.k \
       --include-materials \
       --include-contacts

Python API Quick Start
-----------------------

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from koomesh import MeshGenerator

   # Initialize
   generator = MeshGenerator()

   # Generate mesh
   mesh = generator.generate_from_step(
       'input.step',
       mesh_size=2.0
   )

   # Access mesh data
   print(f"Nodes: {len(mesh.nodes)}")
   print(f"Elements: {len(mesh.elements)}")

   # Export
   mesh.export('output.k', format='lsdyna')

Contact Detection
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.contact import AssemblyContactManager

   # Load parts
   parts = [
       ('Body', body_mesh),
       ('Door', door_mesh),
       ('Hood', hood_mesh)
   ]

   # Detect contacts
   manager = AssemblyContactManager()
   contacts = manager.detect_contacts(
       parts,
       tolerance=1.0,
       auto_classify=True
   )

   # Review
   for pair in contacts:
       print(f"{pair.master_part} <-> {pair.slave_part}")
       print(f"  Type: {pair.contact_type}")
       print(f"  Friction: {pair.parameters.fs}")

Material Assignment
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.materials import GeometryBasedMaterialAssigner

   # Initialize
   assigner = GeometryBasedMaterialAssigner()

   # Assign materials
   parts = [
       {'name': 'hood_outer.step', 'thickness': 0.8},
       {'name': 'pillar_a.step', 'thickness': 2.5}
   ]

   assignments = assigner.assign_by_template(
       parts,
       template='automotive'
   )

   # Review
   for item in assignments:
       print(f"{item['part_name']}: {item['material']}")

Configuration File
------------------

Save commonly used settings:

.. code-block:: yaml

   # koomesh_config.yaml
   meshing:
     mesh_size: 2.0
     element_type: tet4
     contact_aware: true

   contact:
     auto_classify: true
     tolerance: 1.0

   material:
     template: automotive_crash

   export:
     format: lsdyna
     include_materials: true
     include_contacts: true

Use config file:

.. code-block:: bash

   koomesh generate input.step --config koomesh_config.yaml

Tips & Best Practices
----------------------

Choosing Mesh Size
^^^^^^^^^^^^^^^^^^

**General guidelines**:

- **Coarse** (5-10mm): Initial testing, large structures
- **Medium** (2-5mm): Standard simulations
- **Fine** (1-2mm): High-accuracy requirements
- **Very fine** (<1mm): Local refinement, small features

**Rule of thumb**: Use 3-5 elements across smallest critical dimension.

Contact Tolerance
^^^^^^^^^^^^^^^^^

**Recommended values**:

- **Automotive crash**: 0.5-2.0 mm
- **Forming**: 0.1-0.5 mm
- **Assembly**: 1.0-5.0 mm

Element Type Selection
^^^^^^^^^^^^^^^^^^^^^^

**tet4** (Tetrahedral 4-node):
- Fast generation
- Good for complex geometry
- LS-DYNA compatible

**tet10** (Tetrahedral 10-node):
- Better accuracy
- Curved geometries
- Longer solve time

**hex8** (Hexahedral 8-node):
- Best for structured meshes
- Preferred for crash
- More difficult to generate

Quality Thresholds
^^^^^^^^^^^^^^^^^^

Minimum acceptable quality for LS-DYNA:

- **Aspect Ratio**: < 5.0
- **Jacobian**: > 0.3
- **Warpage**: < 15°
- **Skewness**: < 0.7

Common Issues
-------------

Issue: Poor mesh quality
^^^^^^^^^^^^^^^^^^^^^^^^

**Solution 1**: Reduce mesh size::

   koomesh generate input.step --mesh-size 1.5

**Solution 2**: Apply smoothing::

   koomesh smooth output.k --iterations 5

**Solution 3**: Fix geometry first::

   koomesh repair input.step --fix-gaps

Issue: No contacts detected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution**: Increase tolerance::

   koomesh contact assembly.k --tolerance 2.0

Issue: Meshing takes too long
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution 1**: Increase mesh size::

   koomesh generate input.step --mesh-size 5.0

**Solution 2**: Simplify geometry::

   koomesh simplify input.step --tolerance 0.1

**Solution 3**: Use coarser element type::

   koomesh generate input.step --element-type tet4

Next Steps
----------

Now that you know the basics:

1. **Learn more**: :doc:`cli_reference` - Complete CLI reference
2. **Follow tutorials**: :doc:`../tutorials/automotive_crash` - Step-by-step guides
3. **Explore examples**: See ``examples/`` directory
4. **Advanced features**: :doc:`contact_aware_meshing`, :doc:`material_assignment`

Getting Help
------------

**Built-in help**::

   koomesh --help
   koomesh generate --help
   koomesh contact --help

**Documentation**: https://koomesh.readthedocs.io/

**Community**:
- GitHub Discussions
- Stack Overflow (tag: koomesh)

**Support**: support@koomesh.dev

Examples
--------

More quick examples:

.. code-block:: bash

   # Generate with specific element type
   koomesh generate box.step --element-type hex8

   # Check quality with custom thresholds
   koomesh quality check mesh.k --min-aspect-ratio 3.0

   # Export to multiple formats
   koomesh export mesh.k output.{k,inp,bdf}

   # Batch processing
   for file in parts/*.step; do
       koomesh generate "$file"
   done

   # Using pipes
   koomesh generate input.step | koomesh quality check -

   # Verbose output
   koomesh generate input.step -v

.. tip::

   Start simple! Generate a basic mesh first, then add complexity:

   1. Basic mesh
   2. Add quality checks
   3. Enable contact detection
   4. Add material assignment
   5. Full validation

.. warning::

   Always validate your mesh before running simulations!

   ``koomesh validate output.k --solver lsdyna``
