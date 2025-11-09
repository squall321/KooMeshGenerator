Material Assignment
===================

Automated material assignment is a key feature that intelligently assigns materials to parts based on filenames, geometry properties, and industry templates.

Overview
--------

Manual material assignment for large assemblies is time-consuming and error-prone. KooMeshGenerator automates this process using:

1. **Filename Pattern Matching**: Recognizes part names (e.g., "hood" → Aluminum)
2. **Geometry Analysis**: Analyzes thickness, volume, and area ratios
3. **Industry Templates**: Applies best practices for automotive, aerospace, etc.
4. **Material Validation**: Ensures assigned materials are suitable for simulation type

Benefits:

* **Time Savings**: Assign materials to 100+ parts in seconds
* **Consistency**: Apply industry standards automatically
* **Accuracy**: Validate materials for specific simulation types
* **Flexibility**: Mix automatic and manual assignment strategies

Assignment Strategies
---------------------

1. Filename-Based Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Matches part filenames to material rules.

**How it works:**

.. code-block:: python

   # Rules: 'hood' → 'Aluminum_5052'
   filename = 'hood_outer_left.step'
   # Match: 'hood' found in filename → Aluminum_5052

**Advantages:**

* Fast and simple
* Works with standard naming conventions
* Industry-specific templates available

**Limitations:**

* Requires consistent naming
* No geometry consideration
* May fail for generic names

**Example Usage:**

CLI::

   koomesh material assign *.step --template automotive

Python::

   from koomesh.materials.material_assigner import GeometryBasedMaterialAssigner

   assigner = GeometryBasedMaterialAssigner()
   material = assigner.assign_by_filename(
       'hood_outer.step',
       template='automotive'
   )
   # Result: 'Aluminum_5052'

2. Geometry-Based Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Analyzes geometric properties to infer material type.

**Properties analyzed:**

* **Thickness**: Thin (< 1.5mm) → sheet metal
* **Volume/Area ratio**: Large area → panels, low area → structural
* **Size**: Large bulk → castings, small bulk → brackets

**Classification rules:**

========  ==============  ===============  ==================
Type      Thickness       V/A Ratio        Typical Material
========  ==============  ===============  ==================
Sheet     < 1.5mm         High (thin)      Aluminum, Mild Steel
Structural 1.5-5mm        Medium           High-Strength Steel
Bulk      > 5mm           Low (thick)      Cast Iron, Forged Steel
========  ==============  ===============  ==================

**Example Usage:**

CLI::

   koomesh material assign *.step --by-geometry

Python::

   material = assigner.assign_by_geometry(
       thickness=0.8,   # Thin sheet
       volume=5000.0,   # cm³
       area=6000.0      # cm²
   )
   # Result: 'Aluminum_5052' or 'Steel_Mild'

3. Template-Based Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses pre-defined industry templates combining filename and geometry rules.

**Available Templates:**

**Automotive**

* ``automotive``: General automotive parts
* ``automotive_crash``: Crash simulation optimized
* ``automotive_forming``: Stamping and forming

**Aerospace**

* ``aerospace``: General aerospace
* ``aerospace_primary_structure``: Primary load-bearing
* ``aerospace_secondary_structure``: Secondary structures

**Forming**

* ``forming``: General forming operations
* ``deep_drawing``: Deep drawing specific
* ``stamping``: Stamping operations

**Example Usage:**

CLI::

   koomesh material assign *.step --template automotive_crash

Python::

   assignments = assigner.assign_by_template(
       parts,
       template='automotive_crash'
   )

4. Hybrid Strategy
^^^^^^^^^^^^^^^^^^

Combines multiple strategies with fallback logic.

**Priority order:**

1. Try filename matching (fast)
2. If no match, use geometry analysis
3. If insufficient data, use default material

**Example:**

.. code-block:: python

   material = assigner.assign_material(
       part_name='unknown_part.step',  # No filename match
       thickness=0.8,                   # → Use geometry
       volume=5000.0,
       area=6000.0,
       template='automotive',
       strategy=AssignmentStrategy.FILENAME  # Start with filename
   )
   # Falls back to geometry → 'Aluminum_5052'

Material Validation
-------------------

After assignment, validate materials for your simulation type.

Validation Checks
^^^^^^^^^^^^^^^^^

1. **Simulation Compatibility**

   * Crash: Requires failure model
   * Forming: Needs good formability (σ_y < 600 MPa)
   * Impact: Avoid brittle materials

2. **Property Completeness**

   * Essential: density, E, ν
   * Crash: yield strength, failure strain
   * Forming: yield strength, hardening model

3. **Physical Reasonableness**

   * E: 100 - 500,000 MPa
   * ρ: 0.001 - 30,000 kg/m³
   * ν: 0.0 - 0.5

4. **Practical Concerns**

   * Part weight calculation
   * Cost considerations (informational)

**Example:**

CLI::

   koomesh material validate Steel_Mild --simulation-type crash

Python::

   from koomesh.materials.material_validator import MaterialValidator

   validator = MaterialValidator()
   report = validator.validate_assignment(
       part_name='Hood',
       material_name='Aluminum_5052',
       simulation_type='crash',
       part_volume=5000.0
   )

   if not report.valid:
       for issue in report.issues:
           print(f"{issue.severity}: {issue.message}")
           print(f"  Fix: {issue.suggestion}")

Material Recommendation
-----------------------

Get material recommendations based on requirements.

**Example:**

CLI::

   koomesh material recommend \
       --simulation-type crash \
       --min-strength 400 \
       --max-density 5000 \
       --top 5

Python::

   from koomesh.materials.material_validator import MaterialRecommender

   recommender = MaterialRecommender()
   recommendations = recommender.recommend_materials(
       part_name='Structural_Beam',
       simulation_type='crash',
       constraints={
           'min_strength': 400.0,    # MPa
           'max_density': 5000.0,    # kg/m³
           'formability': 'preferred'
       },
       top_n=5
   )

   for material, score, reason in recommendations:
       print(f"{material.name} (score: {score:.2f})")
       print(f"  Density: {material.density} kg/m³")
       print(f"  Strength: {material.yield_strength} MPa")
       print(f"  Reason: {reason}")

**Output Example:**

.. code-block:: text

   Steel_HighStrength (score: 0.85)
     Density: 7850 kg/m³
     Strength: 550 MPa
     Reason: Good structural properties, Good crash energy absorption

   Aluminum_7075 (score: 0.78)
     Density: 2810 kg/m³
     Strength: 503 MPa
     Reason: Good structural properties, Lightweight

   Steel_UHSS (score: 0.75)
     Density: 7850 kg/m³
     Strength: 1200 MPa
     Reason: Good structural properties, Good crash energy absorption

Industry Templates
------------------

Automotive Template (automotive)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Part Naming Rules:**

===================  =======================  =================
Part Name Pattern    Material                 Rationale
===================  =======================  =================
hood, fender         Aluminum_5052            Lightweight, formable panels
door_outer           Steel_Mild               Cost-effective panels
door_inner           Steel_HighStrength       Structural reinforcement
pillar_a, pillar_b   Steel_UltraHighStrength  Safety cage
roof                 Steel_Mild               Non-critical panel
floor, tunnel        Steel_HighStrength       Structural platform
bumper_beam          Steel_HighStrength       Energy absorption
bumper_cover         Plastic_PP               Lightweight, impact-resistant
bracket, mount       Steel_Mild               General purpose
windshield           Glass_Laminated          Visibility, safety
===================  =======================  =================

**Thickness-Based Rules:**

* < 0.8mm: Aluminum_5052 (very thin sheet)
* 0.8-1.5mm: Steel_Mild (standard sheet)
* 1.5-3mm: Steel_HighStrength (structural)
* > 3mm: Steel_UltraHighStrength (reinforcement)

Automotive Crash Template (automotive_crash)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optimized for crash simulation accuracy.

**Key Differences:**

* Front structure: Energy-absorbing materials
* Safety cage: High-strength materials with failure models
* Deformation zones: Materials with good ductility
* All materials validated for failure strain data

Aerospace Template (aerospace)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Part Naming Rules:**

===================  =======================  =================
Part Name Pattern    Material                 Rationale
===================  =======================  =================
fuselage, skin       Aluminum_2024            High strength-to-weight
wing_skin            Aluminum_7075            Fatigue resistance
spar, rib            Aluminum_7075            Structural integrity
frame                Aluminum_2024            General structure
bulkhead             Aluminum_7075            Load distribution
fairing, cowl        Composite_CFRP           Lightweight, aerodynamic
fastener, bracket    Titanium_6Al4V           High strength, corrosion
===================  =======================  =================

Forming Template (forming)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Part Naming Rules:**

===================  =======================  =================
Part Name Pattern    Material                 Rationale
===================  =======================  =================
blank                Aluminum_5052            Excellent formability
die, punch           Steel_ToolSteel          Hardness, wear resistance
holder, pad          Steel_Mild               Cost-effective tooling
===================  =======================  =================

**Formability Check:**

* Blank materials: σ_y < 300 MPa (soft, formable)
* Die materials: σ_y > 800 MPa (hard, durable)

Examples
--------

Example 1: Automotive Assembly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assign materials to a car body assembly::

   # Directory structure:
   # body/
   #   ├── hood_outer.step
   #   ├── door_fl_outer.step
   #   ├── door_fl_inner.step
   #   ├── pillar_a_left.step
   #   ├── floor_front.step
   #   └── bumper_beam_front.step

   koomesh material assign body/*.step --template automotive

**Results:**

.. code-block:: text

   hood_outer.step → Aluminum_5052
   door_fl_outer.step → Steel_Mild
   door_fl_inner.step → Steel_HighStrength
   pillar_a_left.step → Steel_UltraHighStrength
   floor_front.step → Steel_HighStrength
   bumper_beam_front.step → Steel_HighStrength

Example 2: Forming Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assign materials for a stamping die::

   koomesh material assign \
       blank.step die_upper.step die_lower.step holder.step \
       --template forming

**Results:**

.. code-block:: text

   blank.step → Aluminum_5052 (σ_y = 193 MPa, formable)
   die_upper.step → Steel_ToolSteel (σ_y = 2000 MPa, hard)
   die_lower.step → Steel_ToolSteel
   holder.step → Steel_Mild (σ_y = 250 MPa, low cost)

Example 3: Mixed Strategy
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use filename first, fallback to geometry::

   # Parts with non-standard names
   koomesh material assign *.step \
       --template automotive \
       --fallback-to-geometry

**Behavior:**

* ``hood_outer.step`` → Filename match → Aluminum_5052
* ``unknown_part_001.step`` → No filename match → Analyze geometry (t=0.8mm) → Aluminum_5052
* ``component_xyz.step`` → No filename match → Analyze geometry (t=3.0mm) → Steel_HighStrength

Best Practices
--------------

Naming Conventions
^^^^^^^^^^^^^^^^^^

Use consistent, descriptive part names:

**Good names:**

* ``hood_outer_left.step``
* ``pillar_a_right.step``
* ``door_fl_inner.step`` (fl = front-left)

**Bad names:**

* ``part1.step``
* ``component.step``
* ``mesh_001.step``

Validation Workflow
^^^^^^^^^^^^^^^^^^^

Always validate after assignment::

   # 1. Assign materials
   koomesh material assign *.step --template automotive_crash

   # 2. Validate all assignments
   koomesh material validate-all --simulation-type crash

   # 3. Review issues
   # Fix any errors or warnings

   # 4. Export for simulation
   koomesh export assembly.k --format lsdyna

Custom Templates
^^^^^^^^^^^^^^^^

Create custom templates for your specific needs:

.. code-block:: yaml

   # my_template.yaml
   template_name: my_automotive

   rules:
     hood: Aluminum_6061        # Different aluminum alloy
     door: Steel_AHSS           # Advanced high-strength steel
     bracket: Steel_Stainless   # Corrosion-resistant

   geometry_rules:
     sheet_metal:
       thickness_max: 1.2       # Custom threshold
       material: Steel_Mild

     structural:
       thickness_min: 2.0
       material: Steel_AHSS

Usage::

   koomesh material assign *.step --template-file my_template.yaml

Troubleshooting
---------------

Problem: Wrong materials assigned
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Filename doesn't match template rules

**Solution**: Use more specific names or custom template::

   # Check what was assigned
   koomesh material list-assignments

   # Fix specific parts
   koomesh material set hood_outer.step Aluminum_5052

   # Or use custom template
   koomesh material assign *.step --template-file custom.yaml

Problem: Missing material properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Material doesn't have all required properties for simulation

**Solution**: Get recommendations for suitable materials::

   koomesh material recommend \
       --simulation-type crash \
       --formability required

Problem: Assignment too slow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Geometry analysis on large files

**Solution**: Use filename-only mode::

   koomesh material assign *.step \
       --template automotive \
       --no-geometry-analysis  # Skip geometry

See Also
--------

* :doc:`../api/materials`
* :doc:`../tutorials/automotive_crash`
* :doc:`../examples/material_automation`
