Material Assignment and Validation
===================================

This module provides intelligent material assignment, validation, and recommendation for finite element simulations.

Material Assignment
-------------------

.. automodule:: koomesh.materials.material_assigner
   :members:
   :undoc-members:
   :show-inheritance:

Material Validation
-------------------

.. automodule:: koomesh.materials.material_validator
   :members:
   :undoc-members:
   :show-inheritance:

Material Library
----------------

.. automodule:: koomesh.materials.material_library
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Automatic Material Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.materials.material_assigner import GeometryBasedMaterialAssigner

   # Assign materials by template
   assigner = GeometryBasedMaterialAssigner()

   parts = [
       {'name': 'hood_outer.step', 'thickness': 0.8, 'volume': 5000.0, 'area': 6000.0},
       {'name': 'pillar_a.step', 'thickness': 2.5, 'volume': 15000.0, 'area': 6000.0}
   ]

   assignments = assigner.batch_assign(
       parts,
       template='automotive',
       strategy=AssignmentStrategy.TEMPLATE
   )

   for assignment in assignments:
       print(f"{assignment['part_name']}: {assignment['material']}")

Assignment Strategies
^^^^^^^^^^^^^^^^^^^^^

**Filename-Based**::

   # Matches part names to materials
   material = assigner.assign_by_filename(
       'hood_outer.step',
       template='automotive'
   )
   # Result: 'Aluminum_5052'

**Geometry-Based**::

   # Analyzes geometry properties
   material = assigner.assign_by_geometry(
       thickness=0.8,  # Thin sheet
       volume=5000.0,
       area=6000.0
   )
   # Result: 'Aluminum_5052' or 'Steel_Mild'

**Template-Based**::

   # Uses industry templates
   assignments = assigner.assign_by_template(
       parts,
       template='automotive_crash'
   )

Material Validation
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.materials.material_validator import MaterialValidator

   # Validate material assignment
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
           print(f"  Suggestion: {issue.suggestion}")

Validation Checks
^^^^^^^^^^^^^^^^^

The validator performs:

1. **Simulation Compatibility**: Checks if material is suitable for simulation type
2. **Property Completeness**: Verifies all required properties are present
3. **Physical Reasonableness**: Validates property values are realistic
4. **Practical Concerns**: Checks weight, cost, and manufacturability

Material Recommendation
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.materials.material_validator import MaterialRecommender

   # Get material recommendations
   recommender = MaterialRecommender()

   recommendations = recommender.recommend_materials(
       part_name='Structural_Beam',
       simulation_type='crash',
       constraints={
           'min_strength': 400.0,    # MPa
           'max_density': 8000.0,    # kg/m³
           'formability': 'preferred'
       },
       top_n=5
   )

   for material, score, reason in recommendations:
       print(f"{material.name} (score: {score:.2f})")
       print(f"  Reason: {reason}")

Material Templates
------------------

Automotive Templates
^^^^^^^^^^^^^^^^^^^^

**automotive**
   Standard automotive parts (body panels, structures)

**automotive_crash**
   Crash simulation (energy absorption, structural integrity)

**automotive_forming**
   Stamping and forming operations

Aerospace Templates
^^^^^^^^^^^^^^^^^^^

**aerospace**
   General aerospace parts (fuselage, wings)

**aerospace_primary_structure**
   Primary load-bearing structures

**aerospace_secondary_structure**
   Secondary structures and fairings

Forming Templates
^^^^^^^^^^^^^^^^^

**forming**
   General forming operations

**deep_drawing**
   Deep drawing specific materials

**stamping**
   Stamping operations

CLI Usage
---------

Material Assignment::

   # Auto-assign materials
   koomesh material assign *.step --template automotive

   # Use geometry analysis
   koomesh material assign *.step --by-geometry

   # Custom rules file
   koomesh material assign *.step --rules my_rules.yaml

Material Validation::

   # Validate assignment
   koomesh material validate Steel_Mild --simulation-type crash

   # With part volume
   koomesh material validate Aluminum_6061 --simulation-type forming --volume 5000

Material Recommendation::

   # Get recommendations
   koomesh material recommend --simulation-type crash

   # With constraints
   koomesh material recommend --simulation-type forming \
       --min-strength 200 --max-density 5000 \
       --formability required

Material Library::

   # List all materials
   koomesh material list

   # Search materials
   koomesh material search --category steel --strength-min 400

   # Show material details
   koomesh material info Steel_HighStrength

See Also
--------

* :doc:`../user_guide/material_assignment`
* :doc:`../tutorials/automotive_crash`
* :doc:`../examples/material_automation`
