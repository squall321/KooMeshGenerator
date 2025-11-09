# KooMeshGenerator Documentation

This directory contains the Sphinx documentation for KooMeshGenerator.

## Building the Documentation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
cd docs
make html
```

The generated documentation will be in `build/html/index.html`.

### Build PDF Documentation (requires LaTeX)

```bash
make latexpdf
```

### Clean Build Files

```bash
make clean
```

## Documentation Structure

```
docs/
├── source/
│   ├── index.rst                 # Main documentation index
│   ├── conf.py                   # Sphinx configuration
│   ├── api/                      # API reference
│   │   ├── contact.rst           # Contact detection API
│   │   ├── materials.rst         # Material assignment API
│   │   ├── meshing.rst           # Meshing API
│   │   └── ...
│   ├── user_guide/               # User guides
│   │   ├── installation.rst
│   │   ├── quickstart.rst
│   │   ├── contact_aware_meshing.rst
│   │   ├── material_assignment.rst
│   │   └── ...
│   ├── tutorials/                # Step-by-step tutorials
│   │   ├── automotive_crash.rst
│   │   ├── forming_simulation.rst
│   │   └── ...
│   └── examples/                 # Code examples
│       ├── basic_meshing.rst
│       ├── contact_detection.rst
│       └── ...
├── build/                        # Generated documentation (git-ignored)
├── Makefile                      # Build automation
└── requirements.txt              # Documentation dependencies
```

## Contributing to Documentation

### Adding New Pages

1. Create new `.rst` file in appropriate directory
2. Add to `toctree` in `index.rst` or parent page
3. Build and verify: `make html`

### Docstring Style

Use Google-style docstrings:

```python
def my_function(param1: int, param2: str) -> bool:
    """
    Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is negative

    Example:
        >>> my_function(5, "test")
        True
    """
    pass
```

### Live Preview

For live documentation preview during development:

```bash
pip install sphinx-autobuild
sphinx-autobuild source build/html
```

Open http://localhost:8000 in your browser.

## Deployment

### GitHub Pages

```bash
# Build documentation
make html

# Deploy to gh-pages branch
# (Assuming gh-pages branch exists)
cp -r build/html/* /path/to/gh-pages/
cd /path/to/gh-pages/
git add .
git commit -m "Update documentation"
git push origin gh-pages
```

### Read the Docs

The project is configured for Read the Docs automatic building.
Simply push to the repository and RTD will build automatically.

## Troubleshooting

### Import Errors

If you get import errors when building:

```bash
# Ensure koomesh is installed
pip install -e ..

# Or add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
```

### Missing Extensions

```bash
pip install -r requirements.txt
```

### Build Warnings

Fix all warnings for clean documentation:

```bash
make clean html SPHINXOPTS="-W"  # Treat warnings as errors
```
