# KooMeshGenerator CLI Usage Guide

**Complete guide for using KooMeshGenerator from the command line**

Version: 2.0
Last Updated: 2025-11-07

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Commands](#basic-commands)
4. [Workflow-Based Meshing](#workflow-based-meshing)
5. [Batch Processing](#batch-processing)
6. [Geometry Preprocessing](#geometry-preprocessing)
7. [Quality Checking](#quality-checking)
8. [Contact Detection](#contact-detection)
9. [Material Management](#material-management)
10. [Visualization](#visualization)
11. [Advanced Usage](#advanced-usage)
12. [Tips & Best Practices](#tips--best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Convert a STEP file to LS-DYNA mesh

```bash
# Simple conversion with default settings
koomesh generate input.step --mesh-size 2.0 -o output.k

# Check mesh quality
koomesh quality check output.k --report html

# Visualize mesh
koomesh visualize output.k --screenshot mesh.png
```

### Batch process multiple files

```bash
# Convert all STEP files in a directory
koomesh batch-convert "cad/*.step" --output-dir meshes/ --mesh-size 2.0

# Use parameter file for custom settings
koomesh batch-mesh parts_list.csv --parallel
```

### Use configuration file

```bash
# Run complete workflow from config
koomesh run workflow_config.yaml

# Override specific settings
koomesh run workflow_config.yaml --override meshing.mesh_size=1.5
```

---

## Installation

### Requirements

- Python 3.8+
- PythonOCC (for STEP file reading)
- GMSH (for meshing)

### Install KooMeshGenerator

```bash
# Clone repository
git clone https://github.com/yourusername/KooMeshGenerator.git
cd KooMeshGenerator

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Verify installation
koomesh --version
koomesh info
```

---

## Basic Commands

### System Information

```bash
# Show version
koomesh --version

# Show system and dependency info
koomesh info

# Get help
koomesh --help
koomesh <command> --help
```

### Generate Mesh

```bash
# Basic mesh generation
koomesh generate part.step --mesh-size 2.0 -o part.k

# With hex priority
koomesh generate part.step --mesh-size 2.0 --hex-priority

# Skip quality validation
koomesh generate part.step --mesh-size 2.0 --no-validate-quality

# Verbose output
koomesh --verbose generate part.step --mesh-size 2.0
```

### Analyze STEP File

```bash
# Analyze geometry
koomesh analyze assembly.step

# Skip hierarchy parsing
koomesh analyze assembly.step --no-hierarchy

# Skip classification
koomesh analyze assembly.step --no-classify
```

---

## Workflow-Based Meshing

Configuration files allow you to define complete meshing workflows with all parameters in one place.

### Configuration File Format

Create a YAML file (e.g., `workflow.yaml`):

```yaml
project:
  name: "my_project"
  description: "Vehicle crash simulation"
  output_dir: "output/crash"

input:
  step_files:
    - "cad/body.step"
    - "cad/chassis.step"

meshing:
  algorithm: "delaunay"
  mesh_size: 2.0
  element_type: "tet4"

  boundary_layer:
    enabled: true
    thickness: 0.5
    num_layers: 3

quality:
  thresholds:
    aspect_ratio: 10.0
    jacobian: 0.1
    skewness: 0.8

  checks:
    - aspect_ratio
    - jacobian
    - min_angle

contact:
  auto_detect: true
  tolerance: 0.1
  self_contact: true

materials:
  library: "materials/automotive.json"
  assignments:
    body: "Steel_HighStrength"
    chassis: "Steel_Mild"

output:
  format: "lsdyna"
  filename: "simulation.k"
  include_contact: true

parallel:
  enabled: true
  n_jobs: -1
```

### Running Workflows

```bash
# Run workflow
koomesh run workflow.yaml

# Validate config without running
koomesh run workflow.yaml --validate-only

# Dry run (show what would happen)
koomesh run workflow.yaml --dry-run

# Override specific parameters
koomesh run workflow.yaml --override meshing.mesh_size=1.5

# Multiple overrides
koomesh run workflow.yaml \
  --override meshing.mesh_size=2.5 \
  --override quality.thresholds.aspect_ratio=15.0
```

### Template Configurations

Use pre-defined templates for common scenarios:

```bash
# Available templates are in templates/ directory:
# - crash_analysis.yaml
# - forming_simulation.yaml
# - drop_test.yaml
# - simple_part.yaml

# Copy and customize a template
cp templates/crash_analysis.yaml my_config.yaml
# Edit my_config.yaml with your settings
koomesh run my_config.yaml
```

---

## Batch Processing

Process multiple files efficiently with batch commands.

### Batch Convert (Glob Patterns)

```bash
# Convert all STEP files in directory
koomesh batch-convert "cad/*.step" --output-dir meshes/ --mesh-size 2.0

# Recursive search
koomesh batch-convert "cad/**/*.step" --output-dir meshes/ --mesh-size 2.0

# With custom settings
koomesh batch-convert "parts/*.step" \
  --output-dir output/ \
  --mesh-size 1.5 \
  --element-type hex8 \
  --parallel \
  --jobs 8

# Dry run to preview
koomesh batch-convert "cad/*.step" --output-dir meshes/ --dry-run
```

### Batch Mesh (CSV/Excel)

Create a CSV file with individual parameters for each part:

**parts_list.csv:**
```csv
id,input_file,output_file,mesh_size,element_type,material
body_01,cad/body_front.step,meshes/body_front.k,2.0,tet4,Steel_HighStrength
body_02,cad/body_rear.step,meshes/body_rear.k,2.0,tet4,Steel_HighStrength
bumper,cad/bumper.step,meshes/bumper.k,1.5,tet4,Aluminum_6061_T6
chassis,cad/chassis.step,meshes/chassis.k,2.5,hex8,Steel_Mild
```

Run batch processing:

```bash
# Process from CSV
koomesh batch-mesh parts_list.csv

# With parallel processing
koomesh batch-mesh parts_list.csv --parallel --jobs 4

# From Excel file (specify sheet)
koomesh batch-mesh parts_list.xlsx --sheet 0

# Dry run
koomesh batch-mesh parts_list.csv --dry-run

# With retry on failure
koomesh batch-mesh parts_list.csv --max-retries 3
```

### Example Batch Files

See `examples/batch/` for complete examples:
- `automotive_parts.csv` - Automotive parts with custom parameters
- `README.md` - Detailed batch processing guide

---

## Geometry Preprocessing

Clean and analyze STEP files before meshing.

### Geometry Info

```bash
# Show basic geometry information
koomesh geometry info part.step

# Verbose output with detailed metrics
koomesh geometry info part.step --verbose
```

**Output includes:**
- Volume and surface area
- Number of solids, faces, edges, vertices
- Bounding box dimensions
- Validity status

### Geometry Cleaning

```bash
# Basic cleaning (fix invalid geometry)
koomesh geometry clean input.step --output cleaned.step

# Heal surfaces (sew faces together)
koomesh geometry clean input.step --output cleaned.step --heal-surfaces

# Remove small features
koomesh geometry clean input.step --output cleaned.step \
  --remove-small-features 0.5

# Fill gaps
koomesh geometry clean input.step --output cleaned.step \
  --fill-gaps 0.1

# Full cleaning
koomesh geometry clean input.step --output cleaned.step \
  --heal-surfaces \
  --fill-gaps 0.1 \
  --remove-small-features 0.5
```

### Geometry Comparison

```bash
# Compare two geometries
koomesh geometry compare original.step cleaned.step

# Compare before and after processing
koomesh geometry compare original.step simplified.step
```

**Output shows:**
- Volume difference
- Surface area difference
- Face count changes
- Percentage changes

---

## Quality Checking

Validate mesh quality with comprehensive checks.

### Quality Check

```bash
# Basic quality check
koomesh quality check mesh.k

# Generate HTML report
koomesh quality check mesh.k --report html --output report.html

# Generate JSON report
koomesh quality check mesh.k --report json --output results.json

# Custom quality thresholds
koomesh quality check mesh.k \
  --aspect-ratio 10.0 \
  --jacobian 0.1 \
  --min-angle 15.0
```

### Quality Metrics

Available metrics:
- **Aspect Ratio**: Element elongation
- **Jacobian**: Element distortion
- **Skewness**: Element skew angle
- **Min/Max Angle**: Corner angles
- **Volume**: Element volume
- **Edge Length Ratio**: Edge length variation

---

## Contact Detection

Automatically detect contact zones between parts.

### Detect Contact

```bash
# Auto-detect contact zones
koomesh contact detect assembly.k

# With custom tolerance
koomesh contact detect assembly.k --tolerance 0.2

# Include self-contact
koomesh contact detect assembly.k --self-contact

# Export contact definitions
koomesh contact detect assembly.k --export lsdyna -o contact.k

# With angle threshold
koomesh contact detect assembly.k --min-angle 120.0
```

---

## Material Management

Manage material library and assignments.

### List Materials

```bash
# List all materials
koomesh material list

# Filter by keyword
koomesh material list --filter steel

# Show details
koomesh material list --verbose
```

### Show Material Details

```bash
# Show specific material
koomesh material show Steel_HighStrength

# Show all properties
koomesh material show Steel_HighStrength --verbose
```

### Add Material

```bash
# Add material from JSON
koomesh material add custom_material.json

# Add material interactively
koomesh material add --interactive
```

---

## Visualization

Create visualizations and screenshots.

### Visualize Mesh

```bash
# Interactive visualization
koomesh visualize mesh.k

# Save screenshot
koomesh visualize mesh.k --screenshot output.png

# Visualize specific metric
koomesh visualize mesh.k --metric aspect_ratio --screenshot quality.png

# Customize view
koomesh visualize mesh.k \
  --screenshot output.png \
  --width 1920 \
  --height 1080 \
  --camera-position 10 10 10
```

### Visualization Metrics

Available metrics for visualization:
- `aspect_ratio`
- `jacobian`
- `skewness`
- `volume`
- `edge_length`

---

## Advanced Usage

### Parallel Processing

```bash
# Use all CPU cores
koomesh batch-mesh parts.csv --parallel --jobs -1

# Limit to specific number of cores
koomesh batch-mesh parts.csv --parallel --jobs 4

# Disable parallelization
koomesh batch-mesh parts.csv --no-parallel
```

### Logging Control

```bash
# Verbose output (DEBUG level)
koomesh --verbose generate part.step --mesh-size 2.0

# Quiet mode (ERROR level only)
koomesh --quiet batch-convert "*.step" --output-dir meshes/

# Save log to file
koomesh generate part.step --mesh-size 2.0 2>&1 | tee mesh.log
```

### Pipeline Workflows

Chain commands together:

```bash
# Complete preprocessing to meshing pipeline
koomesh geometry clean input.step --output cleaned.step && \
koomesh generate cleaned.step --mesh-size 2.0 -o mesh.k && \
koomesh quality check mesh.k --report html -o report.html && \
koomesh visualize mesh.k --screenshot mesh.png
```

---

## Tips & Best Practices

### 1. Start with Geometry Analysis

```bash
# Always analyze geometry first
koomesh geometry info part.step
koomesh analyze part.step
```

### 2. Use Configuration Files for Repeatability

```bash
# Save settings in YAML for consistent results
koomesh run production_config.yaml
```

### 3. Test with Dry Runs

```bash
# Preview batch operations before execution
koomesh batch-convert "*.step" --output-dir meshes/ --dry-run
```

### 4. Validate Configs Before Running

```bash
# Check config is valid
koomesh run config.yaml --validate-only
```

### 5. Clean Geometry Before Meshing

```bash
# Fix common issues
koomesh geometry clean input.step --output cleaned.step --heal-surfaces
```

### 6. Use Appropriate Mesh Sizes

- **Coarse (5-10 mm)**: Initial testing, large parts
- **Medium (2-5 mm)**: Standard analysis
- **Fine (0.5-2 mm)**: High accuracy, small parts
- **Very Fine (< 0.5 mm)**: Critical regions only

### 7. Leverage Batch Processing

```bash
# Process related parts with consistent settings
koomesh batch-mesh parts_list.csv --parallel
```

### 8. Monitor Quality

```bash
# Always check quality after meshing
koomesh quality check mesh.k --report html
```

---

## Troubleshooting

### Common Issues

#### 1. Command Not Found

```bash
# Verify installation
koomesh --version

# If not found, reinstall
pip install -e /path/to/KooMeshGenerator
```

#### 2. PythonOCC Not Available

```bash
# Check dependencies
koomesh info

# Install PythonOCC (see build/README.md)
```

#### 3. GMSH Not Found

```bash
# Check GMSH installation
koomesh info

# Install GMSH (see build/README.md)
```

#### 4. Config Validation Fails

```bash
# Validate config separately
koomesh run config.yaml --validate-only

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

#### 5. Batch Processing Fails

```bash
# Run with dry-run first
koomesh batch-mesh parts.csv --dry-run

# Check CSV format
head -5 parts.csv

# Enable verbose logging
koomesh --verbose batch-mesh parts.csv
```

#### 6. Geometry Errors

```bash
# Clean geometry first
koomesh geometry clean input.step --output cleaned.step --heal-surfaces

# Check geometry validity
koomesh geometry info input.step
```

### Getting Help

```bash
# General help
koomesh --help

# Command-specific help
koomesh <command> --help
koomesh <command> <subcommand> --help

# Examples
koomesh geometry --help
koomesh quality check --help
```

### Reporting Issues

If you encounter bugs or have feature requests:

1. Check existing issues: https://github.com/yourusername/KooMeshGenerator/issues
2. Create new issue with:
   - Command used
   - Error message
   - System info (`koomesh info`)
   - Sample files (if possible)

---

## Examples

See the `examples/` directory for complete workflow examples:

- `examples/batch/` - Batch processing examples
- `examples/workflows/` - Complete workflow scripts
- `templates/` - Configuration templates

---

## Reference

### Command Summary

| Command | Purpose |
|---------|---------|
| `koomesh generate` | Generate mesh from STEP file |
| `koomesh analyze` | Analyze STEP file structure |
| `koomesh batch` | Batch process directory |
| `koomesh run` | Run workflow from config |
| `koomesh batch-convert` | Batch convert with glob |
| `koomesh batch-mesh` | Batch mesh from CSV |
| `koomesh geometry info` | Show geometry information |
| `koomesh geometry clean` | Clean geometry |
| `koomesh geometry compare` | Compare geometries |
| `koomesh quality check` | Check mesh quality |
| `koomesh contact detect` | Detect contact zones |
| `koomesh material list` | List materials |
| `koomesh visualize` | Visualize mesh |
| `koomesh info` | System information |
| `koomesh version` | Show version |

### Global Options

| Option | Description |
|--------|-------------|
| `--verbose, -v` | Enable verbose output |
| `--quiet, -q` | Suppress output (errors only) |
| `--help` | Show help message |
| `--version` | Show version |

---

**Happy Meshing! 🎯**

For more information, visit: https://github.com/yourusername/KooMeshGenerator
