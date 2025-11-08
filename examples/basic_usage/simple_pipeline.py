"""
Simple Pipeline Example
=======================

Minimal example showing basic mesh generation from STEP to K file.

Author: KooMeshGenerator Team
"""

from pathlib import Path
from koomesh.pipeline import MeshGenerationPipeline, PipelineConfig

# Configure pipeline
config = PipelineConfig(
    input_files=['input.step'],  # Your STEP file
    output_file='output.k',      # Output K file
    mesh_size=10.0,              # 10mm elements
    element_type='tet4'          # Tetrahedral elements
)

# Run pipeline
pipeline = MeshGenerationPipeline(config)
result = pipeline.run()

# Check results
if result.success:
    print(f"✓ Success! Generated {result.num_elements:,} elements")
else:
    print(f"✗ Failed with {len(result.errors)} errors")
