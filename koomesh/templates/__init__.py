"""
Template System
===============

Industry-specific mesh generation templates for FEA simulations.
"""

from .template_manager import (
    TemplateManager,
    SimulationTemplate,
    TemplateCategory,
    load_template,
    list_templates,
)

__all__ = [
    'TemplateManager',
    'SimulationTemplate',
    'TemplateCategory',
    'load_template',
    'list_templates',
]
