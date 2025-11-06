# KooMeshGenerator Examples

This directory contains practical examples demonstrating KooMeshGenerator usage.

## Quick Start Examples

### Example 1: Simple Box Mesh

Generate a basic hexahedral mesh for a box geometry:

```python
from koomesh.core.pipeline import MeshPipeline

# Create pipeline
pipeline = MeshPipeline()

# Generate mesh
result = pipeline.run(
    step_file='box.step',
    output_file='box.k',
    mesh_size=2.0,
    hex_priority=True
)

# Check results
if result.success:
    print(f"✓ Generated {result.statistics['total_elements']} elements")
    print(f"  Output: {result.output_path}")
else:
    print(f"✗ Failed: {result.errors}")
```

### Example 2: Batch Processing

Process multiple STEP files in parallel:

```python
from koomesh.core.batch_processor import BatchProcessor

# Create batch processor with 4 workers
processor = BatchProcessor(num_workers=4)

# Process entire directory
result = processor.process_directory(
    input_dir='step_files/',
    output_dir='lsdyna_output/',
    mesh_size=1.0,
    recursive=True,
    parallel=True
)

# Print summary
result.print_summary()
print(f"Success rate: {result.success_rate:.1f}%")
```

### Example 3: Custom Configuration

Use custom configuration for specific requirements:

```python
from koomesh.config import KooMeshConfig
from koomesh.core.pipeline import MeshPipeline

# Create custom config
config = KooMeshConfig()
config.mesh.default_size = 0.5
config.mesh.hex_priority = True
config.mesh.min_jacobian = 0.2
config.contact.tolerance = 0.01
config.contact.auto_detect = True

# Use config in pipeline
pipeline = MeshPipeline(config=config)
result = pipeline.run('model.step', 'output.k')
```

### Example 4: Quality Validation

Generate mesh with strict quality requirements:

```python
from koomesh.core.pipeline import MeshPipeline

pipeline = MeshPipeline()

result = pipeline.run(
    step_file='complex_part.step',
    output_file='output.k',
    mesh_size=1.5,
    validate_quality=True
)

# Check quality report
if result.quality_report:
    print(f"Min Jacobian: {result.quality_report.min_jacobian:.4f}")
    print(f"Avg Jacobian: {result.quality_report.avg_jacobian:.4f}")
    print(f"Failed elements: {result.quality_report.num_failed}")

    if result.quality_report.num_failed > 0:
        print("⚠ Warning: Some elements failed quality check")
```

### Example 5: Progress Tracking

Monitor pipeline progress with callbacks:

```python
from koomesh.core.pipeline import MeshPipeline, PipelineProgress

def show_progress(progress: PipelineProgress):
    """Custom progress display"""
    elapsed = progress.format_time(progress.elapsed_seconds)
    remaining = progress.estimated_remaining

    msg = f"[{progress.progress:3.0f}%] {progress.stage.value}: {progress.message}"
    msg += f" (elapsed: {elapsed}"

    if remaining:
        msg += f", remaining: {progress.format_time(remaining)}"

    msg += ")"
    print(msg)

# Create pipeline with progress callback
pipeline = MeshPipeline(progress_callback=show_progress)

result = pipeline.run('model.step', 'output.k', mesh_size=2.0)
```

### Example 6: Programmatic Mesh Creation

Create meshes programmatically without STEP files:

```python
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.export.lsdyna_writer import LSDynaWriter

# Create structured hex mesh
mesh = create_structured_box_mesh(
    length=100.0,  # mm
    width=50.0,
    height=20.0,
    nx=10,  # elements in X
    ny=5,   # elements in Y
    nz=2    # elements in Z
)

print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

# Export to LS-DYNA
with LSDynaWriter('box_mesh.k') as writer:
    writer.write_header()
    writer.write_nodes(mesh)
    writer.write_elements(mesh, part_id=1)

print("✓ Exported to box_mesh.k")
```

### Example 7: Contact Detection

Detect and configure contacts between parts:

```python
from koomesh.core.pipeline import MeshPipeline
from koomesh.config import KooMeshConfig

# Configure contact detection
config = KooMeshConfig()
config.contact.enabled = True
config.contact.tolerance = 0.5  # mm
config.contact.auto_detect = True

pipeline = MeshPipeline(config=config)

# Generate mesh with automatic contact detection
result = pipeline.run('assembly.step', 'assembly.k', mesh_size=2.0)

# Review detected contacts
print(f"Detected {len(result.contacts)} contact pairs:")
for i, contact in enumerate(result.contacts, 1):
    print(f"  {i}. {contact.master_surface.part_name} <-> "
          f"{contact.slave_surface.part_name}")
    print(f"     Type: {contact.contact_type.value}")
    print(f"     Friction: {contact.friction}")
```

### Example 8: Hierarchy Analysis

Analyze STEP file hierarchy before meshing:

```python
from koomesh.io.hierarchy_parser import HierarchyParser

# Parse STEP file hierarchy
parser = HierarchyParser()
root = parser.parse_step_file('assembly.step')

# Print hierarchy tree
def print_tree(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}- {node.name} (level {node.level})")
    for child in node.children:
        print_tree(child, indent + 1)

print("Assembly hierarchy:")
print_tree(root)

# Get statistics
all_nodes = root.get_all_descendants()
print(f"\nTotal parts: {len(all_nodes)}")
print(f"Max depth: {max(n.level for n in all_nodes)}")
```

### Example 9: Element Type Selection

Control element type selection:

```python
from koomesh.core.pipeline import MeshPipeline
from koomesh.config import KooMeshConfig

# Force tetrahedral meshing
config = KooMeshConfig()
config.mesh.hex_priority = False
config.mesh.hex_enabled = False
config.mesh.tet_enabled = True
config.mesh.tet_algorithm = "delaunay"

pipeline = MeshPipeline(config=config)
result = pipeline.run('complex_shape.step', 'output.k', mesh_size=1.0)

print(f"Element types used:")
for elem_type, count in result.statistics.get('element_types', {}).items():
    print(f"  {elem_type}: {count}")
```

### Example 10: Error Handling

Robust error handling in production:

```python
from koomesh.core.pipeline import MeshPipeline
from koomesh.config import KooMeshConfig
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_mesh_generation(step_file, output_file):
    """Generate mesh with comprehensive error handling"""
    try:
        pipeline = MeshPipeline()

        result = pipeline.run(
            step_file=step_file,
            output_file=output_file,
            mesh_size=2.0,
            validate_quality=True
        )

        if not result.success:
            logger.error(f"Meshing failed for {step_file}")
            for error in result.errors:
                logger.error(f"  - {error}")
            return False

        # Check for warnings
        if result.warnings:
            logger.warning(f"Generated with warnings:")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")

        # Verify output
        if not result.output_path.exists():
            logger.error("Output file was not created")
            return False

        logger.info(f"✓ Successfully generated {result.output_path}")
        logger.info(f"  Nodes: {result.statistics['total_nodes']}")
        logger.info(f"  Elements: {result.statistics['total_elements']}")

        return True

    except FileNotFoundError:
        logger.error(f"STEP file not found: {step_file}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False

# Use in production
success = safe_mesh_generation('model.step', 'output.k')
if success:
    print("Mesh generation completed successfully")
else:
    print("Mesh generation failed - see logs")
```

## Command Line Examples

### Basic Usage

```bash
# Generate mesh from STEP file
koomesh generate model.step --mesh-size 2.0 -o output.k

# Analyze STEP file before meshing
koomesh analyze assembly.step --hierarchy --classify

# Batch process directory
koomesh batch input_dir/ output_dir/ --mesh-size 1.0 -w 4

# Show system information
koomesh info
```

### Advanced Options

```bash
# Disable hex priority (force tetrahedral)
koomesh generate complex.step -s 1.5 --no-hex-priority

# Verbose output with progress
koomesh generate -v model.step -s 2.0

# Batch with recursive search
koomesh batch input/ output/ -s 1.0 -w 8 --recursive

# Sequential processing (no parallelization)
koomesh batch input/ output/ -s 2.0 --sequential
```

## Performance Tips

1. **Mesh Size**: Start with larger mesh size (5-10mm) for testing, then refine
2. **Parallel Processing**: Use `num_workers=CPU_count-1` for batch processing
3. **Hex Priority**: Enable for simple geometries, disable for complex shapes
4. **Quality Validation**: Disable during initial testing to save time
5. **Contact Tolerance**: Adjust based on model scale (0.1-1% of typical dimension)

## Troubleshooting

### Issue: Mesh generation fails
**Solution**: Check STEP file validity, try disabling hex priority

### Issue: Poor mesh quality
**Solution**: Reduce mesh size, adjust quality thresholds

### Issue: Missing contacts
**Solution**: Increase contact tolerance, verify part proximity

### Issue: Long processing time
**Solution**: Increase mesh size, reduce number of elements

## New Utility Examples

### Example 11: Mesh Coarsening

Reduce mesh density for faster simulation:

```python
from koomesh.meshing.tet_mesher import TetMesher

# Load or generate a fine mesh
mesher = TetMesher(mesh_size=0.5)
fine_mesh = mesher.mesh_shape(shape)

# Coarsen the mesh
coarsened = mesher.coarsen_mesh(fine_mesh, coarsening_factor=0.5)

print(f"Original: {fine_mesh.num_nodes()} nodes, {fine_mesh.num_elements()} elements")
print(f"Coarsened: {coarsened.num_nodes()} nodes, {coarsened.num_elements()} elements")
```

Run demo: `python mesh_coarsening_demo.py`

### Example 12: Mesh Copy and Merge

Copy and merge meshes for complex assemblies:

```python
from koomesh.utils.mesh_copy import copy_mesh
from koomesh.utils.mesh_merge import merge_meshes, merge_meshes_with_tolerance
from koomesh.utils.mesh_transform import translate_mesh

# Create copies of a part
part1 = original_mesh
part2 = copy_mesh(part1)
part3 = copy_mesh(part1)

# Position copies
translate_mesh(part2, dx=100.0)
translate_mesh(part3, dx=200.0)

# Merge all parts
assembly = merge_meshes([part1, part2, part3], preserve_parts=True)

# Or merge with tolerance to eliminate duplicate nodes at interfaces
assembly = merge_meshes_with_tolerance([part1, part2, part3], tolerance=1e-6)
```

Run demo: `python mesh_utilities_demo.py`

### Example 13: Contact Surface Detection

Automatically detect contact surfaces between parts:

```python
from koomesh.utils.contact_detection import ContactSurfaceDetector

# Create detector
detector = ContactSurfaceDetector()

# Detect contacts (parts within 0.1 mm)
contacts = detector.detect_contacts(mesh, tolerance=0.1, min_faces=1)

# Report detected contacts
for i, contact in enumerate(contacts):
    print(f"Contact {i+1}:")
    print(f"  Parts: {contact.part1_id} <-> {contact.part2_id}")
    print(f"  Faces: {len(contact.part1_faces)} <-> {len(contact.part2_faces)}")
    print(f"  Distance: {contact.avg_distance:.4f}")

# Export contact definitions
detector.export_contact_pairs(contacts, "contacts.inp", format="abaqus")
detector.export_contact_pairs(contacts, "contacts.k", format="lsdyna")
```

Run demo: `python contact_detection_demo.py`

### Example 14: Format Conversion

Convert meshes between different file formats:

```python
from koomesh.io.format_converter import MeshFormatConverter

# Create converter
converter = MeshFormatConverter()

# Export to various formats
converter.export_vtk(mesh, "mesh.vtk")          # Paraview/VTK
converter.export_abaqus(mesh, "mesh.inp")       # Abaqus
converter.export_nastran(mesh, "mesh.bdf")      # Nastran

# Import from VTK
imported_mesh = converter.import_from_vtk("mesh.vtk")

# Round-trip conversion
converter.export_vtk(imported_mesh, "mesh_roundtrip.vtk")
```

Run demo: `python format_converter_demo.py`

### Example 15: Mesh Transformation

Transform mesh geometry:

```python
from koomesh.utils.mesh_transform import (
    translate_mesh, scale_mesh, rotate_mesh_z,
    center_mesh, mirror_mesh
)

# Translate mesh
translate_mesh(mesh, dx=10.0, dy=5.0, dz=2.0)

# Scale mesh (2x in all directions)
scale_mesh(mesh, sx=2.0, sy=2.0, sz=2.0)

# Rotate around Z axis
rotate_mesh_z(mesh, angle_degrees=45.0)

# Center mesh at origin
center_mesh(mesh)

# Mirror across YZ plane
mirror_mesh(mesh, axis='x')
```

## Available Demo Scripts

The following demo scripts are available in this directory:

- `mesh_coarsening_demo.py` - Demonstrates mesh coarsening with different factors
- `mesh_utilities_demo.py` - Shows copy, merge, and transform operations
- `contact_detection_demo.py` - Detects and exports contact surfaces
- `format_converter_demo.py` - Converts between VTK, Abaqus, and Nastran formats
- `mesh_smoothing_demo.py` - Mesh smoothing operations
- `mesh_repair_demo.py` - Mesh repair utilities
- `mesh_partition_demo.py` - Mesh partitioning for parallel computing
- `mesh_reporter_demo.py` - Comprehensive mesh quality reporting

Run any demo with:
```bash
python <demo_name>.py
```

## Next Steps

- Review [API Documentation](../docs/api.md)
- See [User Guide](../docs/user_guide.md)
- Check [Configuration Reference](../docs/configuration.md)
