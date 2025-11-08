# KooMeshGenerator CLI Examples

Complete collection of CLI command examples for KooMeshGenerator with Phase 4 features.

## Table of Contents

1. [Basic Mesh Generation](#basic-mesh-generation)
2. [Template-Based Workflows](#template-based-workflows)
3. [Material Management](#material-management)
4. [Quality Analysis](#quality-analysis)
5. [Batch Processing](#batch-processing)
6. [Performance Optimization](#performance-optimization)

---

## Basic Mesh Generation

### Simple mesh generation
```bash
koomesh generate input.step --mesh-size 2.0 -o output.k
```

### With specific element type
```bash
koomesh generate model.step --mesh-size 2.0 --element-type hex -o mesh.k
```

### With quality target
```bash
koomesh generate part.step --mesh-size 1.5 --min-quality 0.4 -o output.k
```

---

## Template-Based Workflows

### List available templates
```bash
koomesh template list
koomesh template list --category automotive
koomesh template list --category aerospace
```

### Use automotive crash template
```bash
koomesh template apply automotive_crash_frontal \
  --geometry model.step \
  --output crash_mesh.k
```

### Customize template parameters
```bash
koomesh template apply aerospace_bird_strike \
  --geometry engine_inlet.step \
  --mesh-size 1.0 \
  --override "materials=['Titanium_Ti6Al4V']" \
  --output bird_strike.k
```

### Create refined variant
```bash
koomesh template refine automotive_crash_frontal \
  --factor 2.0 \
  --output-template crash_refined.yaml
```

### Validate template
```bash
koomesh template validate my_template.yaml
koomesh template validate --template automotive_crash_frontal
```

---

## Material Management

### List all materials
```bash
koomesh material list
```

### Search materials
```bash
koomesh material search steel
koomesh material search titanium
koomesh material search biocompatible
```

### Show material properties
```bash
koomesh material info Steel_DP600
koomesh material info Titanium_Ti6Al4V
```

### Compare materials
```bash
koomesh material compare Steel_DP600 Steel_DP980 Aluminum_6061_T6
```

### Export material database
```bash
koomesh material export --format json -o my_materials.json
koomesh material export --format yaml -o my_materials.yaml
```

### Add custom material
```bash
koomesh material add \
  --name "Custom_Steel" \
  --type elastic_plastic \
  --density 7850 \
  --elastic-modulus 200e9 \
  --poisson-ratio 0.29 \
  --yield-stress 400e6
```

---

## Quality Analysis

### Check mesh quality
```bash
koomesh quality check mesh.k
```

### Generate HTML quality report
```bash
koomesh quality check mesh.k --report html -o quality_report.html
```

### Check with custom thresholds
```bash
koomesh quality check mesh.k \
  --min-jacobian 0.4 \
  --max-aspect-ratio 5.0 \
  --max-skewness 0.5
```

### Auto-remesh based on quality
```bash
koomesh quality remesh mesh.k \
  --strategy adaptive \
  --max-iterations 3 \
  --output mesh_refined.k
```

### Quality distribution analysis
```bash
koomesh quality analyze mesh.k --distribution --histogram
```

### Compare mesh quality
```bash
koomesh quality compare mesh_v1.k mesh_v2.k mesh_v3.k
```

---

## Batch Processing

### Batch process from CSV
```bash
koomesh batch-mesh parts_list.csv \
  --output-dir meshes/ \
  --parallel \
  --jobs 8
```

Example CSV (`parts_list.csv`):
```csv
geometry_file,mesh_size,output_file,template
part1.step,2.0,part1.k,automotive_crash_frontal
part2.step,3.0,part2.k,automotive_bumper_impact
part3.step,1.5,part3.k,biomedical_hip_implant
```

### Batch convert with glob pattern
```bash
koomesh batch-convert "cad/*.step" \
  --output-dir meshes/ \
  --mesh-size 2.0 \
  --format lsdyna \
  --parallel
```

### Batch process with template
```bash
koomesh batch-convert "parts/*.step" \
  --template automotive_crash_frontal \
  --output-dir crash_meshes/ \
  --jobs 4
```

### Batch quality check
```bash
koomesh batch-quality "meshes/*.k" \
  --report-dir quality_reports/ \
  --threshold 0.4 \
  --parallel
```

---

## Performance Optimization

### Generate with caching enabled
```bash
koomesh generate model.step \
  --mesh-size 2.0 \
  --cache \
  -o output.k
```

### Use streaming for large files
```bash
koomesh generate large_model.step \
  --mesh-size 5.0 \
  --streaming \
  --chunk-size 100MB \
  -o output.k
```

### Profile performance
```bash
koomesh generate model.step \
  --mesh-size 2.0 \
  --profile \
  --profile-output profile.json \
  -o output.k
```

### Run benchmark
```bash
koomesh benchmark \
  --geometry model.step \
  --mesh-sizes 1.0,2.0,5.0,10.0 \
  --output benchmark_results.json
```

### Clear caches
```bash
koomesh cache clear
koomesh cache clear --geometry
koomesh cache clear --config
```

---

## Advanced Workflows

### Complete crash analysis workflow
```bash
# 1. Analyze geometry
koomesh geometry info model.step

# 2. Apply template
koomesh template apply automotive_crash_frontal \
  --geometry model.step \
  --output crash_base.k

# 3. Check quality
koomesh quality check crash_base.k --report html -o quality.html

# 4. Refine if needed
koomesh quality remesh crash_base.k \
  --strategy adaptive \
  --output crash_refined.k

# 5. Detect contacts
koomesh contact detect crash_refined.k \
  --tolerance 0.1 \
  --export lsdyna \
  --output contacts.inc

# 6. Visualize
koomesh visualize crash_refined.k --output preview.png
```

### Parametric study
```bash
# Create variants with different element sizes
for size in 1.0 2.0 3.0 5.0; do
  koomesh generate model.step \
    --mesh-size $size \
    --template automotive_crash_frontal \
    -o "mesh_${size}mm.k"

  koomesh quality check "mesh_${size}mm.k" \
    --report html \
    -o "quality_${size}mm.html"
done
```

### Material sensitivity study
```bash
# Test different materials
for material in Steel_DP600 Steel_DP980 Aluminum_6061_T6; do
  koomesh template apply automotive_bumper_impact \
    --geometry bumper.step \
    --override "materials=['$material']" \
    --output "bumper_${material}.k"
done
```

---

## Configuration File Examples

### YAML configuration for batch processing
```yaml
# crash_analysis.yaml
workflow:
  name: "Crash Analysis Pipeline"

geometry:
  file: "vehicle_model.step"

meshing:
  template: "automotive_crash_frontal"
  mesh_size: 2.0
  element_type: "hex8"
  quality_threshold: 0.4

materials:
  - Steel_DP600
  - Aluminum_6061_T6
  - Foam_PU_Rigid_100

quality:
  auto_remesh: true
  strategy: "adaptive"
  max_iterations: 3

output:
  mesh_file: "crash_mesh.k"
  quality_report: "quality.html"
  format: "lsdyna"
```

Run with:
```bash
koomesh run crash_analysis.yaml
```

### Template customization YAML
```yaml
# custom_crash_template.yaml
name: "custom_frontal_crash"
base_template: "automotive_crash_frontal"

overrides:
  target_element_size: 3.0
  min_element_size: 1.0
  max_element_size: 10.0
  materials:
    - Steel_DP980
    - Aluminum_7075_T6
  analysis_duration: 0.120

validation:
  min_jacobian: 0.35
  max_aspect_ratio: 8.0
```

Apply custom template:
```bash
koomesh template apply custom_crash_template.yaml \
  --geometry model.step \
  --output mesh.k
```

---

## Environment Variables

```bash
# Set cache directory
export KOOMESH_CACHE_DIR=/path/to/cache

# Set number of parallel jobs
export KOOMESH_NUM_JOBS=8

# Enable debug logging
export KOOMESH_LOG_LEVEL=DEBUG

# Set default template directory
export KOOMESH_TEMPLATE_DIR=/path/to/templates

# Set material database path
export KOOMESH_MATERIAL_DB=/path/to/materials.json
```

---

## Tips and Best Practices

### 1. Use Templates for Consistency
```bash
# Define once, use everywhere
koomesh template apply automotive_crash_frontal --geometry part.step -o mesh.k
```

### 2. Enable Caching for Large Projects
```bash
# First run: slow
koomesh generate large_model.step --cache -o mesh1.k

# Subsequent runs: fast (uses cache)
koomesh generate large_model.step --cache -o mesh2.k
```

### 3. Always Check Quality
```bash
# Generate mesh
koomesh generate model.step --mesh-size 2.0 -o mesh.k

# Immediately check quality
koomesh quality check mesh.k --report html -o quality.html
```

### 4. Use Parallel Processing
```bash
# Single-threaded: slow
koomesh batch-convert "parts/*.step" -o meshes/

# Parallel: fast
koomesh batch-convert "parts/*.step" -o meshes/ --jobs 8
```

### 5. Profile Performance
```bash
# Identify bottlenecks
koomesh generate model.step --profile --mesh-size 2.0 -o mesh.k

# Review profile.json for timing information
cat profile.json
```

---

## Troubleshooting

### Mesh quality too low
```bash
# Try smaller element size
koomesh generate model.step --mesh-size 1.0 -o mesh.k

# Or use auto-remeshing
koomesh quality remesh mesh.k --strategy aggressive -o refined.k
```

### Out of memory
```bash
# Use streaming mode
koomesh generate large_model.step --streaming --chunk-size 50MB -o mesh.k
```

### Template validation fails
```bash
# Check template details
koomesh template validate my_template.yaml --verbose

# Fix issues and retry
koomesh template validate my_template.yaml
```

### Material not found
```bash
# List available materials
koomesh material list | grep steel

# Search for alternatives
koomesh material search "high strength"
```

---

## Getting Help

```bash
# General help
koomesh --help

# Command-specific help
koomesh generate --help
koomesh template --help
koomesh quality --help
koomesh batch-mesh --help

# Show version
koomesh --version

# Show configuration
koomesh config show
```

---

## Additional Resources

- [Complete CLI Guide](../docs/CLI_GUIDE.md)
- [Phase 4 Features Guide](../docs/PHASE4_FEATURES.md)
- [Template Reference](../docs/TEMPLATES.md)
- [Material Database](../docs/MATERIALS.md)
- [Quality Metrics](../docs/QUALITY.md)
