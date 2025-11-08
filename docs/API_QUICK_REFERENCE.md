# API Quick Reference

## Core Classes

### MeshGenerationPipeline

Main pipeline for STEP → K file conversion.

```python
from koomesh.pipeline import MeshGenerationPipeline, PipelineConfig

config = PipelineConfig(input_files=['input.step'], output_file='output.k')
pipeline = MeshGenerationPipeline(config)
result = pipeline.run()
```

### PipelineConfig

Configuration for mesh generation.

**Key Parameters**:
- `input_files`: List of STEP files
- `output_file`: Output K file path
- `mesh_size`: Element size (mm)
- `element_type`: 'tet4' or 'hex8'
- `enable_contact_detection`: Enable contact detection
- `enable_auto_remesh`: Enable quality-based remeshing

### PipelineResult

Results from pipeline execution.

**Attributes**:
- `success`: Whether pipeline succeeded
- `num_nodes`: Number of nodes generated
- `num_elements`: Number of elements
- `num_contacts`: Number of contacts detected
- `avg_quality`: Average element quality
- `execution_time`: Total execution time

## Validation

### LSDynaValidator

Validate LS-DYNA K files.

```python
from koomesh.validation import LSDynaValidator

validator = LSDynaValidator()
result = validator.validate('output.k')

if result.success:
    print(f"✓ Valid K file with {result.statistics['node_count']} nodes")
```

## Geometry Processing

### GeometryCleaner

Clean and repair geometry.

```python
from koomesh.preprocessing.geometry_cleaner import GeometryCleaner

cleaner = GeometryCleaner()
result = cleaner.clean(
    input_file='input.step',
    output_file='cleaned.step',
    remove_small_features=1.0,  # Remove features < 1mm
    heal_surfaces=True
)
```

## For More Information

- See `examples/` for complete workflows
- See `SESSION_SUMMARY.md` for implementation details
