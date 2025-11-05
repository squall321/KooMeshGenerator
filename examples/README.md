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

## Next Steps

- Review [API Documentation](../docs/api.md)
- See [User Guide](../docs/user_guide.md)
- Check [Configuration Reference](../docs/configuration.md)
