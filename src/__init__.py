"""
Ultimate Norbi Assistant - Package initialization
"""

__version__ = "1.0.0"
__author__ = "Ultimate Norbi Assistant"
__description__ = "AI-powered development assistant with integrated quality gates"

from .critic import CodeCritic, CriticResult
from .codegen import UltimateNorbiAssistant, CodegenConfig
from .profiles import ProfileManager, get_profile, list_profiles
from .templates import TemplateManager, get_template, suggest_template, list_templates

__all__ = [
    'CodeCritic',
    'CriticResult', 
    'UltimateNorbiAssistant',
    'CodegenConfig',
    'ProfileManager',
    'get_profile',
    'list_profiles',
    'TemplateManager',
    'get_template',
    'suggest_template',
    'list_templates'
]