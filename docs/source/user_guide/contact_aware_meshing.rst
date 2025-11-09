Contact-Aware Meshing
=====================

Contact-aware meshing is an advanced technique that automatically refines the mesh at contact zones during geometry processing. This ensures better contact definition and improved simulation accuracy.

Overview
--------

Traditional meshing approaches apply a uniform mesh size across the entire geometry. Contact-aware meshing:

1. **Detects potential contact zones** during geometry analysis
2. **Refines the mesh locally** at contact interfaces
3. **Aligns nodes** across contact surfaces for better definition
4. **Optimizes mesh quality** in critical contact regions

This results in:

* Better contact force distribution
* Improved simulation stability
* Reduced initial penetration issues
* More accurate contact stress prediction

How It Works
------------

Detection Phase
^^^^^^^^^^^^^^^

The system uses a two-stage approach to detect potential contact zones:

1. **Bounding Box Pre-filtering**

   * Quickly identifies parts that are spatially close
   * Uses tolerance-based overlap detection
   * Eliminates distant parts from consideration

2. **Surface Proximity Analysis**

   * Extracts surface points from candidate geometries
   * Uses KD-tree for efficient nearest neighbor search
   * Identifies actual contact zones with precise gap measurements

Refinement Phase
^^^^^^^^^^^^^^^^

Once contact zones are detected, the mesher applies local refinement:

1. **GMSH Field Creation**

   * Creates Ball fields centered at contact zones
   * Sets refined mesh size based on gap distance
   * Applies smooth transition from refined to base mesh

2. **Adaptive Sizing**

   * Base mesh size: Global element size
   * Contact mesh size: Base size × refinement factor (e.g., 0.5)
   * Transition distance: 2-3× contact zone radius

Alignment Phase
^^^^^^^^^^^^^^^

For very close surfaces (< tolerance), the system:

* Identifies matching node pairs across surfaces
* Snaps nodes to mid-plane position
* Ensures identical coordinates for tied contacts

Usage
-----

CLI Interface
^^^^^^^^^^^^^

Enable contact-aware meshing during mesh generation::

   koomesh generate assembly.step \
       --contact-aware-meshing \
       --refinement-factor 0.5 \
       --contact-tolerance 1.0

Parameters:

* ``--contact-aware-meshing``: Enable feature (default: disabled)
* ``--refinement-factor``: Mesh size multiplier at contacts (default: 0.5)
* ``--contact-tolerance``: Maximum gap for contact detection (mm, default: 1.0)

Python API
^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.contact_aware_mesher import ContactAwareMesher
   import gmsh

   # Initialize mesher
   mesher = ContactAwareMesher()

   # Load geometries (shapes is list of TopoDS_Shape)
   shapes = load_step_files(['part1.step', 'part2.step'])

   # Detect contact zones
   contact_zones = mesher.detect_potential_contact_zones(
       shapes,
       tolerance=1.0  # mm
   )

   print(f"Detected {len(contact_zones)} contact zones")
   for zone in contact_zones:
       print(f"  Parts {zone.part1_index}-{zone.part2_index}: "
             f"gap={zone.gap_distance:.3f}mm, radius={zone.radius:.1f}mm")

   # Generate mesh with refinement
   gmsh.initialize()
   gmsh.model.add("assembly")

   # ... add geometries to GMSH ...

   # Apply contact refinement
   mesher.apply_contact_refinement(
       gmsh.model,
       contact_zones,
       base_mesh_size=2.0,
       refinement_factor=0.5
   )

   # Generate mesh
   gmsh.model.mesh.generate(3)
   gmsh.write("assembly_refined.msh")
   gmsh.finalize()

Examples
--------

Example 1: Automotive Assembly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Problem: Mesh a car door assembly with weatherstrip seal.

.. code-block:: python

   # Parts: door_outer.step, door_inner.step, weatherstrip.step
   mesher = ContactAwareMesher()

   # Detect contacts
   contact_zones = mesher.detect_potential_contact_zones(
       [door_outer, door_inner, weatherstrip],
       tolerance=2.0  # 2mm gap tolerance
   )

   # Expected contacts:
   # - door_outer <-> weatherstrip (gap ~1mm)
   # - door_inner <-> weatherstrip (gap ~0.5mm)
   # - door_outer <-> door_inner (gap ~0.1mm, spot welds)

   # Apply refinement
   # Base mesh: 5mm
   # Contact mesh: 2.5mm (refinement_factor=0.5)
   mesher.apply_contact_refinement(
       gmsh_model,
       contact_zones,
       base_mesh_size=5.0,
       refinement_factor=0.5
   )

Result:

* Base mesh size: 5mm
* Contact zone mesh: 2.5mm
* Smooth transition over 5-7.5mm distance
* Better seal compression simulation

Example 2: Forming Die Assembly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Problem: Mesh punch-die-blank assembly for stamping simulation.

.. code-block:: python

   # Parts: punch.step, die.step, blank.step
   mesher = ContactAwareMesher()

   # Very small gaps (< 0.5mm clearance)
   contact_zones = mesher.detect_potential_contact_zones(
       [punch, die, blank],
       tolerance=0.5
   )

   # Aggressive refinement for accurate forming
   mesher.apply_contact_refinement(
       gmsh_model,
       contact_zones,
       base_mesh_size=3.0,
       refinement_factor=0.3  # 0.9mm at contacts
   )

   # Also align nodes for tied contacts
   for zone in contact_zones:
       if zone.gap_distance < 0.1:  # Tied contact
           mesh1, mesh2 = aligned_meshes[zone.part1_index], aligned_meshes[zone.part2_index]
           aligned1, aligned2 = mesher.align_contact_nodes(
               mesh1, mesh2, zone, tolerance=0.1
           )

Result:

* Punch-die contact: 0.9mm mesh, perfectly aligned nodes
* Blank contact: 0.9mm mesh, smooth tool surface representation
* Accurate material flow prediction

Best Practices
--------------

Choosing Tolerance
^^^^^^^^^^^^^^^^^^

**Automotive Crash** (0.5 - 2.0 mm)
   * Typical panel gaps: 1-2mm
   * Weatherstrip compression: up to 5mm
   * Spot weld spacing: 30-50mm

**Forming** (0.1 - 0.5 mm)
   * Die clearance: 0.1-0.3mm
   * Punch-blank contact: ~0.05mm
   * Very tight tolerances

**Assembly** (1.0 - 5.0 mm)
   * General fitting: 1-3mm
   * Bolted joints: 2-5mm
   * Press fits: < 0.5mm

Choosing Refinement Factor
^^^^^^^^^^^^^^^^^^^^^^^^^^^

========  ==================  ==================
Factor    Base → Contact      Use Case
========  ==================  ==================
0.3       10mm → 3mm          Fine detail (forming, tight fits)
0.5       10mm → 5mm          Standard (most simulations)
0.7       10mm → 7mm          Light refinement (large assemblies)
========  ==================  ==================

**Trade-offs:**

* Smaller factor → Better accuracy, more elements, longer solve time
* Larger factor → Faster meshing, fewer elements, less accuracy

Mesh Transition
^^^^^^^^^^^^^^^

Good transition::

   |  Base   |Transition|Contact|Transition|  Base   |
   | 10mm    |  7mm 5mm | 3mm   | 5mm  7mm | 10mm    |
   |---------|----------|-------|----------|---------|
              ← smooth →        ← smooth →

Bad transition (too abrupt)::

   |  Base   | Contact |  Base   |
   | 10mm    | 3mm     | 10mm    |  ← Poor quality transition!
   |---------|---------|---------|

**Rule of Thumb:**
   Transition distance ≥ 2× contact zone radius

Element Quality at Contacts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check quality metrics after meshing::

   koomesh quality check assembly.k --report detailed.html

Target metrics at contact zones:

* Aspect ratio: < 5.0
* Jacobian: > 0.3
* Warpage: < 15°
* Skewness: < 0.7

Limitations
-----------

**Geometric Limitations**

* Complex CAD models may have many false positives
* Self-contact detection is limited
* Very small features (< mesh size) may be missed

**Performance Limitations**

* Detection is O(n log n) with KD-tree (efficient)
* Refinement increases element count (expect 2-5× more elements)
* Very large assemblies (>100 parts) may be slow

**Accuracy Limitations**

* Gap detection accuracy: ±10% of tolerance
* Surface sampling may miss small contact patches
* Node alignment only for very close surfaces (< tolerance)

Troubleshooting
---------------

Problem: Too many contact zones detected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution:**
   Reduce tolerance::

      --contact-tolerance 0.5  # Instead of 2.0

Problem: Missing contact zones
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution:**
   Increase tolerance and check geometry::

      --contact-tolerance 2.0  # Larger search radius
      koomesh geometry check assembly.step  # Verify CAD quality

Problem: Poor mesh quality at contacts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution:**
   Adjust refinement factor and transition::

      --refinement-factor 0.5  # Less aggressive
      --base-mesh-size 3.0     # Smaller base size

Problem: Very slow meshing
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Solution:**
   Disable for large assemblies or use coarser settings::

      --no-contact-aware-meshing  # Disable feature
      # OR
      --refinement-factor 0.8     # Less refinement

See Also
--------

* :doc:`../tutorials/assembly_meshing`
* :doc:`../api/contact`
* :doc:`cli_reference`
