# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'KooMeshGenerator'
copyright = '2025, KooMeshGenerator Team'
author = 'KooMeshGenerator Team'
release = '1.0.0'
version = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',          # Auto-generate documentation from docstrings
    'sphinx.ext.napoleon',          # Support for NumPy and Google style docstrings
    'sphinx.ext.viewcode',          # Add links to source code
    'sphinx.ext.intersphinx',       # Link to other project's documentation
    'sphinx.ext.todo',              # Support for TODO items
    'sphinx.ext.coverage',          # Check documentation coverage
    'sphinx.ext.mathjax',           # Math support
    'sphinx.ext.githubpages',       # GitHub pages support
    'sphinx_autodoc_typehints',     # Type hints support
    'myst_parser',                  # Markdown support
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Type hints
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# Templates
templates_path = ['_templates']

# Exclude patterns
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # Read the Docs theme
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
}

# Logo and favicon (optional)
# html_logo = '_static/logo.png'
# html_favicon = '_static/favicon.ico'

# HTML options
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'click': ('https://click.palletsprojects.com/', None),
}

# -- Options for todo extension ----------------------------------------------

todo_include_todos = True

# -- Markdown support --------------------------------------------------------

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# MyST parser settings
myst_enable_extensions = [
    'colon_fence',      # ::: fence for directives
    'deflist',          # Definition lists
    'substitution',     # Substitution support
    'html_image',       # HTML image support
]
