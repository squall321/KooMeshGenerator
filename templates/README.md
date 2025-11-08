# Configuration Templates

This directory contains workflow configuration templates for common meshing scenarios.

## Available Templates

### 1. `simple_part.yaml`
**Use case**: Basic single-part meshing
**Features**:
- Minimal configuration
- Good starting point for customization
- No contact detection or materials

**Example**:
```bash
koomesh run templates/simple_part.yaml
koomesh run templates/simple_part.yaml --override input.step_files[0]=my_part.step
```

### 2. `crash_analysis.yaml`
**Use case**: Vehicle crash simulations
**Features**:
- Multi-part assembly
- Self-contact detection
- Material assignments
- Relaxed quality thresholds for high deformation
- Parallel processing enabled

**Example**:
```bash
koomesh run templates/crash_analysis.yaml
koomesh run templates/crash_analysis.yaml --override meshing.mesh_size=1.5
```

### 3. `forming_simulation.yaml`
**Use case**: Sheet metal forming
**Features**:
- Tool and blank meshing
- Strict quality requirements
- Tight contact tolerance
- Separate part files
- Material assignments for forming

**Example**:
```bash
koomesh run templates/forming_simulation.yaml
```

### 4. `drop_test.yaml`
**Use case**: Drop test simulations
**Features**:
- Product and packaging
- Impact contact detection
- JSON quality report
- Moderate mesh quality

**Example**:
```bash
koomesh run templates/drop_test.yaml
```

## Customizing Templates

### Method 1: Copy and Edit
```bash
cp templates/crash_analysis.yaml my_config.yaml
# Edit my_config.yaml
koomesh run my_config.yaml
```

### Method 2: Command-line Override
```bash
koomesh run templates/crash_analysis.yaml \
  --override meshing.mesh_size=1.5 \
  --override quality.thresholds.aspect_ratio=3.0
```

### Method 3: Multiple Overrides File
```bash
# Create overrides.yaml
echo "meshing:
  mesh_size: 1.5
quality:
  thresholds:
    aspect_ratio: 3.0" > overrides.yaml

koomesh run templates/crash_analysis.yaml --override-file overrides.yaml
```

## Configuration Structure

All templates follow this structure:

```yaml
project:              # Project metadata
  name: "..."
  output_dir: "..."

input:                # Input files
  step_files: [...]

meshing:              # Meshing parameters
  mesh_size: 2.0
  element_type: "tet4"

quality:              # Quality checking
  enabled: true
  thresholds: {...}

contact:              # Contact detection
  enabled: true
  tolerance: 0.1

materials:            # Material assignments
  library: "..."
  assignments: {...}

output:               # Output settings
  format: "lsdyna"
  filename: "..."

parallel:             # Parallel processing
  enabled: true
  n_jobs: -1

visualization:        # Screenshots
  enabled: false
```

## Best Practices

1. **Start with a template**: Choose the template closest to your use case
2. **Test with defaults**: Run the template as-is first to verify it works
3. **Customize incrementally**: Make small changes and test
4. **Use overrides for experiments**: Keep the original template intact
5. **Document your changes**: Add comments to custom configs
6. **Version control**: Track your configs in git

## Common Override Examples

### Change mesh size
```bash
--override meshing.mesh_size=1.5
```

### Change input files
```bash
--override input.step_files[0]=my_part.step
```

### Enable parallel processing
```bash
--override parallel.enabled=true --override parallel.n_jobs=8
```

### Change quality thresholds
```bash
--override quality.thresholds.aspect_ratio=5.0
```

### Enable visualization
```bash
--override visualization.enabled=true
```

## Creating Custom Templates

To create a new template:

1. Copy `simple_part.yaml` as starting point
2. Modify for your use case
3. Test thoroughly
4. Document the use case in comments
5. Share with your team

Example:
```bash
cp templates/simple_part.yaml templates/my_workflow.yaml
# Edit my_workflow.yaml
koomesh run templates/my_workflow.yaml
```

## Validation

All templates are validated against the schema on load. Common errors:

- **Missing required fields**: Add all required fields (project, input)
- **Invalid values**: Check data types and ranges (e.g., mesh_size > 0)
- **Unknown fields**: Remove fields not in schema (check for typos)
- **File not found**: Verify step_files paths are correct

To validate a config without running:
```bash
koomesh config validate my_config.yaml
```

## Need Help?

- See [CLI_GUIDE.md](../docs/CLI_GUIDE.md) for full command reference
- Check [examples/](../examples/) for complete workflow examples
- Run `koomesh run --help` for command-line options
