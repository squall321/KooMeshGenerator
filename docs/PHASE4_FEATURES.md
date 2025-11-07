# Phase 4: Production-Ready Features Guide

Complete guide to Phase 4 features in KooMeshGenerator.

## Table of Contents

1. [Error Handling & Logging](#error-handling--logging)
2. [Performance Optimization](#performance-optimization)
3. [Material Database](#material-database)
4. [Simulation Templates](#simulation-templates)
5. [Quality-Driven Remeshing](#quality-driven-remeshing)
6. [CI/CD Pipeline](#cicd-pipeline)

---

## Error Handling & Logging

### Custom Exception Hierarchy

Phase 4 introduces 14 custom exception classes with helpful error messages and suggestions.

#### Exception Categories

```python
from koomesh.utils.exceptions import (
    # Input/Output
    FileNotFoundError,
    FileFormatError,
    FilePermissionError,

    # Geometry
    GeometryError,
    InvalidGeometryError,
    UnsupportedGeometryError,

    # Meshing
    MeshingError,
    MeshQualityError,
    InvalidMeshError,

    # Configuration
    ConfigurationError,
    InvalidParameterError,

    # Materials
    MaterialError,
    MaterialNotFoundError,

    # Runtime
    ExecutionError,
)
```

#### Usage Example

```python
from koomesh.utils.exceptions import InvalidGeometryError

try:
    # Process geometry
    process_geometry(geometry_file)
except InvalidGeometryError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")
    print(f"Context: {e.context}")
```

#### Example Output

```
ERROR [KOOMESH_201]: Invalid geometry detected: self-intersecting surfaces found

Suggestion:
  1. Run 'koomesh geometry clean --heal-surfaces'
  2. Check CAD software for geometry repair tools
  3. Simplify the geometry to avoid self-intersections

Context:
  file: model.step
  geometry_type: surface
  issue: self_intersection
```

### Enhanced Logging

```python
from koomesh.utils.logging import setup_logging

# Configure logging
setup_logging(level='INFO', color=True)

# Logs are color-coded:
# ERROR - Red
# WARNING - Yellow
# INFO - Blue
# DEBUG - Gray
```

---

## Performance Optimization

### Performance Profiling

Track execution time and memory usage:

```python
from koomesh.utils.performance import PerformanceProfiler, MemoryMonitor

# Profile execution time
profiler = PerformanceProfiler()

with profiler.profile("mesh_generation"):
    generate_mesh(geometry)

# Get metrics
metrics = profiler.get_metrics("mesh_generation")
print(f"Execution time: {metrics.execution_time_s:.2f}s")

# Monitor memory usage
with MemoryMonitor() as monitor:
    process_large_file(filepath)

print(f"Peak memory: {monitor.peak_memory_mb:.1f} MB")
print(f"Memory delta: {monitor.memory_delta_mb:.1f} MB")
```

### Caching System

#### Geometry Cache

Cache expensive geometry analysis:

```python
from koomesh.utils.cache import geometry_cache

# Cache automatically based on file hash
result = geometry_cache.get_or_compute(
    filepath,
    lambda f: expensive_geometry_analysis(f)
)

# Second call returns cached result
result2 = geometry_cache.get_or_compute(filepath, analyzer.analyze)  # Fast!
```

#### Config Cache

Cache config validation results:

```python
from koomesh.utils.cache import config_cache

# Cache validation
is_valid = config_cache.get_or_compute(
    config_path,
    lambda p: validate_config(p)
)
```

#### Memory Cache

In-memory LRU cache for frequently accessed data:

```python
from koomesh.utils.cache import MemoryCache

cache = MemoryCache(max_size=1000)

# Store data
cache.set("key", data)

# Retrieve data
data = cache.get("key")  # Returns None if not found

# Clear cache
cache.clear()
```

### Streaming Processor

Process large meshes without loading entire file into memory:

```python
from koomesh.core.streaming import StreamingMeshProcessor

processor = StreamingMeshProcessor(chunk_size_mb=100)

# Process file in chunks
for chunk in processor.process_mesh_file(large_file, process_chunk):
    # Process each chunk
    results.append(chunk)
```

### Performance Benchmarks

```bash
# Run benchmark suite
python benchmarks/performance_benchmark.py --output results.json

# Example output:
# Geometry Cache:
#   Write (100 items):  199.42 ms (1.994 ms/item)
#   Read Hit (100):     288.14 ms (2.881 ms/item)
#
# Memory Cache:
#   Write (10k items):  7.66 ms (0.0008 ms/item)
#   Read Recent (1k):   0.95 ms (0.0009 ms/item)
```

---

## Material Database

### Overview

74+ engineering materials across 13 categories.

### Categories

- **Steels** (14): Carbon, stainless, tool, spring, AHSS
- **Aluminum** (7): 6061, 7075, 2024, cast alloys
- **Titanium** (5): CP titanium, Ti-6Al-4V, ELI grade
- **Copper** (4): Brass, bronze, beryllium copper
- **Nickel** (4): Inconel, Hastelloy, Monel
- **Plastics** (11): ABS, PC, Nylon, PEEK, PTFE
- **Composites** (4): Carbon fiber, glass fiber, Kevlar
- **Foams** (4): PU, EPS, aluminum foam
- **Elastomers** (4): Natural rubber, neoprene, silicone
- **Concrete** (4): 20-60 MPa grades
- **Ceramics** (3): Alumina, SiC, zirconia
- **Glass** (2): Soda-lime, borosilicate
- **Wood** (3): Oak, pine, plywood

### Usage

```python
from koomesh.materials.material_library import MaterialLibrary

# Load material database
library = MaterialLibrary()
library.load_default_materials()

print(f"Loaded {len(library.materials)} materials")

# Get material
steel = library.get_material("Steel_DP600")
print(f"Density: {steel.density} kg/m³")
print(f"Young's Modulus: {steel.elastic_modulus / 1e9} GPa")
print(f"Yield Stress: {steel.yield_stress / 1e6} MPa")

# Search materials
steels = library.search_materials("steel")
print(f"Found {len(steels)} steel materials")

# Calculate derived properties
bulk_modulus = steel.get_bulk_modulus()
shear_modulus = steel.get_shear_modulus()
```

### Material Properties

Each material includes:
- Name and description
- Material type (elastic, plastic, elastic_plastic, hyperelastic, rigid, foam, composite)
- Density
- Elastic modulus (Young's modulus)
- Poisson's ratio
- Yield stress (for plastic materials)
- Tangent modulus (for plastic hardening)
- Failure strain
- Unit system
- Metadata (applications, grade, special properties)

---

## Simulation Templates

### Overview

21+ industry-specific simulation templates with predefined parameters.

### Categories

- **Automotive** (5): Frontal crash, side impact, roof crush, NVH, suspension
- **Aerospace** (4): Bird strike, wing structural, engine mount, landing gear
- **Biomedical** (3): Hip implant, dental implant, stent expansion
- **Construction** (2): Building seismic, bridge load
- **Manufacturing** (2): Sheet forming, package drop
- **Marine** (1): Propeller fatigue
- **Energy** (1): Wind turbine blade
- **Electronics** (1): PCB drop
- **Defense** (1): Ballistic impact
- **Consumer** (1): Product compression

### Loading Templates

```python
from koomesh.templates import TemplateManager, load_template, list_templates

# Load built-in templates
manager = TemplateManager()
manager.load_builtin_templates()

# List all templates
templates = list_templates()
print(f"Available templates: {len(templates)}")

# List by category
from koomesh.templates.template_manager import TemplateCategory
automotive = list_templates(TemplateCategory.AUTOMOTIVE)
print(f"Automotive templates: {', '.join(automotive)}")

# Load specific template
template = load_template("automotive_crash_frontal")

print(f"Description: {template.description}")
print(f"Element size: {template.target_element_size} mm")
print(f"Materials: {', '.join(template.materials)}")
```

### Template Validation

```python
from koomesh.templates.template_validator import TemplateValidator
from koomesh.materials.material_library import MaterialLibrary

# Create validator
library = MaterialLibrary()
library.load_default_materials()
validator = TemplateValidator(library)

# Validate template
result = validator.validate(template)

print(result.get_summary())

# Example output:
# ✓ Template validation PASSED
#
# Info (6):
#   ℹ Element type: solid (hex8)
#   ℹ Element size: 2.0-15.0 mm (target: 5.0 mm)
#   ℹ Recommended materials: 3
#   ℹ Analysis: crash (explicit)
#   ℹ Contact: penalty (μ=0.3)
#   ℹ Output: 3 variables every 100 steps
```

### Template Customization

```python
from koomesh.templates.template_customizer import TemplateCustomizer

customizer = TemplateCustomizer(library)

# Refine mesh (smaller elements)
refined = customizer.refine_mesh(template, factor=2.0)
print(f"Element size: {template.target_element_size} → {refined.target_element_size}")

# Coarsen mesh (larger elements)
coarse = customizer.coarsen_mesh(template, factor=2.0)

# Optimize for speed
fast = customizer.optimize_for_speed(template)

# Optimize for accuracy
accurate = customizer.optimize_for_accuracy(template)

# Substitute materials
lightweight = customizer.substitute_material(
    template,
    "Steel_Mild_A36",
    "Aluminum_6061_T6"
)

# Create parametric study
variants = customizer.create_parametric_study(
    template,
    "target_element_size",
    [2.0, 3.0, 5.0, 10.0]
)
```

### Predefined Customization Profiles

```python
from koomesh.templates.template_customizer import get_profile

# Quick preview (coarse, fast)
preview_profile = get_profile("quick_preview")

# Production quality (refined, accurate)
production_profile = get_profile("production_quality")

# Lightweight materials
lightweight_profile = get_profile("lightweight_materials")

# High strength materials
high_strength_profile = get_profile("high_strength")

# Apply profile
customized = customizer.apply_profile(template, preview_profile)
```

---

## Quality-Driven Remeshing

### Quality Metrics

Six quality metrics for mesh elements:

1. **Jacobian** (0-1): Normalized determinant, measures element validity
2. **Aspect Ratio**: Ratio of longest to shortest edge
3. **Skewness** (0-1): Angle deviation from ideal
4. **Warping** (degrees): Face planarity for hex/shell elements
5. **Edge Ratio**: Maximum edge length ratio
6. **Orthogonality**: Angle between edges

### Quality Analysis

```python
from koomesh.quality import QualityAnalyzer
import numpy as np

# Create analyzer
analyzer = QualityAnalyzer(quality_thresholds={
    'min_jacobian': 0.3,
    'max_aspect_ratio': 10.0,
    'max_skewness': 0.7,
    'overall_quality': 0.4,
})

# Analyze single element
nodes = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
])

quality = analyzer.analyze_element(0, "hex8", nodes)

print(f"Jacobian:      {quality.jacobian:.4f}")
print(f"Aspect Ratio:  {quality.max_aspect_ratio:.2f}")
print(f"Skewness:      {quality.max_skewness:.4f}")
print(f"Overall:       {quality.overall_quality:.4f}")
print(f"Acceptable:    {quality.is_acceptable}")
```

### Mesh Quality Metrics

```python
# Analyze entire mesh
element_qualities = []
for i in range(num_elements):
    quality = analyzer.analyze_element(i, "hex8", element_nodes[i])
    element_qualities.append(quality)

# Compute mesh metrics
metrics = analyzer.compute_mesh_metrics(element_qualities)

print(metrics.get_summary())

# Example output:
# ======================================================================
# MESH QUALITY SUMMARY
# ======================================================================
# Total elements: 1,000
#
# Jacobian:
#   Min: 0.3215
#   Max: 1.0000
#   Avg: 0.8542 ± 0.1234
#
# Aspect Ratio:
#   Min: 1.00
#   Max: 8.45
#   Avg: 2.34 ± 1.56
#
# Quality Distribution:
#   Excellent (>0.8): 75.3% (753)
#   Good (0.6-0.8):  18.2% (182)
#   Fair (0.4-0.6):  5.1% (51)
#   Poor (0.2-0.4):  1.2% (12)
#   Bad  (<0.2):     0.2% (2)
#
# Elements needing refinement: 14
# ======================================================================
```

### Auto-Remeshing

```python
from koomesh.quality import AutoRemesher, RefinementStrategy, QualityThreshold

# Create remesher with strategy
remesher = AutoRemesher(
    strategy=RefinementStrategy.ADAPTIVE,
    quality_thresholds=QualityThreshold(
        min_jacobian=0.3,
        target_jacobian=0.6,
    ),
    max_iterations=3
)

# Estimate refinement impact
impact = remesher.estimate_refinement_impact(element_qualities)

print(f"Elements to refine: {impact['elements_to_refine']}")
print(f"Est. new element count: {impact['estimated_new_element_count']:,}")
print(f"Expected quality improvement: {impact['quality_improvement']:+.4f}")

# Perform remeshing
result = remesher.remesh(nodes, elements, element_qualities)

print(result.get_summary())

# Example output:
# ======================================================================
# AUTO-REMESHING RESULT
# ======================================================================
# Success: ✓
# Iterations: 2
#
# Quality Improvement:
#   Initial overall quality: 0.7543
#   Final overall quality:   0.8821
#   Improvement:             +0.1278
#
# Metric Improvements:
#   Jacobian:      +0.0856
#   Aspect Ratio:  -1.234
#   Skewness:      -0.0342
#
# Element Counts:
#   Elements refined: 147
#   New element count: 1,324
#
# Refinement regions: 18
# ======================================================================
```

### Refinement Strategies

```python
# UNIFORM: Refine all elements equally
remesher = AutoRemesher(strategy=RefinementStrategy.UNIFORM)

# ADAPTIVE: Refine only poor-quality elements
remesher = AutoRemesher(strategy=RefinementStrategy.ADAPTIVE)

# GRADUAL: Gradual refinement with transition zones
remesher = AutoRemesher(strategy=RefinementStrategy.GRADUAL)

# AGGRESSIVE: Strict quality enforcement
remesher = AutoRemesher(strategy=RefinementStrategy.AGGRESSIVE)

# CONSERVATIVE: Only refine very poor elements
remesher = AutoRemesher(strategy=RefinementStrategy.CONSERVATIVE)
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

Three automated workflows:

#### 1. Test Workflow (`.github/workflows/test.yml`)

Runs on every push and pull request:
- Tests across Python 3.9, 3.10, 3.11
- Unit tests with pytest
- Coverage report to Codecov
- Test report artifacts

#### 2. Lint Workflow (`.github/workflows/lint.yml`)

Code quality checks:
- Black (code formatting)
- Flake8 (linting)
- Mypy (type checking)
- Bandit (security)
- Interrogate (docstring coverage)

#### 3. Build Container (`.github/workflows/build-container.yml`)

Apptainer container build:
- Builds on push to main
- Uploads container as artifact
- Creates release on tags

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically before each commit:
- black: Code formatting
- isort: Import sorting
- flake8: Linting
- mypy: Type checking
- bandit: Security scanning
- interrogate: Docstring coverage

Manual run:

```bash
pre-commit run --all-files
```

### Apptainer Container

Build and use:

```bash
# Build container
cd apptainer
./build.sh

# Run commands
apptainer run koomesh.sif --help

# Execute Python scripts
apptainer exec koomesh.sif python my_script.py
```

---

## Complete Example Workflow

```python
#!/usr/bin/env python3
"""
Complete Phase 4 workflow example
"""

from koomesh.materials.material_library import MaterialLibrary
from koomesh.templates import load_template
from koomesh.templates.template_customizer import TemplateCustomizer
from koomesh.templates.template_validator import TemplateValidator
from koomesh.quality import QualityAnalyzer, AutoRemesher, RefinementStrategy
from koomesh.utils.performance import PerformanceProfiler
from koomesh.utils.cache import geometry_cache

# 1. Load materials
library = MaterialLibrary()
library.load_default_materials()
print(f"✓ Loaded {len(library.materials)} materials")

# 2. Load and customize template
template = load_template("automotive_crash_frontal")
print(f"✓ Loaded template: {template.name}")

customizer = TemplateCustomizer(library)
refined_template = customizer.refine_mesh(template, factor=1.5)
print(f"✓ Refined mesh: {refined_template.target_element_size} mm")

# 3. Validate template
validator = TemplateValidator(library)
result = validator.validate(refined_template)
print(f"✓ Validation: {'PASSED' if result.is_valid else 'FAILED'}")

# 4. Generate mesh (with profiling)
profiler = PerformanceProfiler()

with profiler.profile("mesh_generation"):
    # Use cached geometry analysis
    geometry_data = geometry_cache.get_or_compute(
        geometry_file,
        analyze_geometry
    )

    # Generate mesh
    mesh = generate_mesh(geometry_data, refined_template)

metrics = profiler.get_metrics("mesh_generation")
print(f"✓ Mesh generated in {metrics.execution_time_s:.2f}s")

# 5. Analyze quality
analyzer = QualityAnalyzer()
element_qualities = []

for i in range(len(mesh.elements)):
    quality = analyzer.analyze_element(i, "hex8", mesh.get_element_nodes(i))
    element_qualities.append(quality)

mesh_metrics = analyzer.compute_mesh_metrics(element_qualities)
print(f"✓ Average quality: {mesh_metrics.avg_overall_quality:.4f}")

# 6. Auto-remesh if needed
if mesh_metrics.avg_overall_quality < 0.7:
    remesher = AutoRemesher(strategy=RefinementStrategy.ADAPTIVE)
    remesh_result = remesher.remesh(
        mesh.nodes,
        mesh.elements,
        element_qualities
    )
    print(f"✓ Remeshed: quality improved by {remesh_result.final_quality - remesh_result.initial_quality:+.4f}")

# 7. Export
mesh.export("output.k", format="lsdyna")
print("✓ Exported to output.k")

print("\n🎉 Workflow complete!")
```

---

## Performance Tips

1. **Use Caching**: Enable caching for repeated geometry analysis
2. **Streaming for Large Files**: Use `StreamingMeshProcessor` for files > 1GB
3. **Profile Critical Sections**: Use `PerformanceProfiler` to identify bottlenecks
4. **Choose Right Strategy**: Use ADAPTIVE refinement for most cases
5. **Batch Processing**: Use parallel processing for multiple files
6. **Template Presets**: Start with templates instead of configuring from scratch

---

## Troubleshooting

### Common Issues

**Q: Material database not loading**
```python
# Check if JSON exists
from pathlib import Path
db_path = Path("koomesh/materials/material_database.json")
print(f"Database exists: {db_path.exists()}")

# Fallback to legacy
library._load_legacy_materials()
```

**Q: Template validation failing**
```python
# Get detailed validation result
result = validator.validate(template)
for error in result.errors:
    print(f"ERROR: {error}")
for warning in result.warnings:
    print(f"WARNING: {warning}")
```

**Q: Quality metrics showing poor results**
```python
# Check specific elements
poor_elements = [eq for eq in element_qualities if not eq.is_acceptable]
for eq in poor_elements[:5]:  # Show first 5
    print(f"Element {eq.element_id}:")
    print(f"  Jacobian: {eq.jacobian:.4f}")
    print(f"  Aspect Ratio: {eq.max_aspect_ratio:.2f}")
    print(f"  Skewness: {eq.max_skewness:.4f}")
```

---

## API Reference

Full API documentation available at: [API Documentation](API.md)

---

## Support

- **Issues**: https://github.com/yourorg/KooMeshGenerator/issues
- **Discussions**: https://github.com/yourorg/KooMeshGenerator/discussions
- **Email**: support@koomesh.org
