"""
Ultimate Norbi Assistant - Performance Profiles

Manages different performance and quality configurations for various use cases.
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Profile:
    """Represents a performance/quality profile configuration."""
    name: str
    description: str
    quality_gates: Dict[str, str]
    timeouts: Dict[str, int]
    max_file_size: int
    parallel_processing: bool
    cache_enabled: bool

class ProfileManager:
    """Manages different performance profiles for the assistant."""
    
    def __init__(self):
        """Initialize with default profiles."""
        self.profiles = {
            'default': Profile(
                name='default',
                description='Balanced performance and quality',
                quality_gates={
                    'syntax_check': 'mandatory',
                    'linting': 'warn_only',
                    'type_check': 'warn_only',
                    'unit_tests': 'mandatory'
                },
                timeouts={'lint': 30, 'test': 300, 'type_check': 30},
                max_file_size=10000,
                parallel_processing=False,
                cache_enabled=True
            ),
            'fast': Profile(
                name='fast',
                description='Quick analysis with minimal checks',
                quality_gates={
                    'syntax_check': 'mandatory',
                    'linting': 'disabled',
                    'type_check': 'disabled',
                    'unit_tests': 'disabled'
                },
                timeouts={'lint': 10, 'test': 60, 'type_check': 10},
                max_file_size=5000,
                parallel_processing=True,
                cache_enabled=True
            ),
            'strict': Profile(
                name='strict',
                description='Comprehensive quality checks',
                quality_gates={
                    'syntax_check': 'mandatory',
                    'linting': 'mandatory',
                    'type_check': 'mandatory',
                    'unit_tests': 'mandatory',
                    'integration_tests': 'mandatory',
                    'security_check': 'mandatory'
                },
                timeouts={'lint': 60, 'test': 600, 'type_check': 60},
                max_file_size=20000,
                parallel_processing=False,
                cache_enabled=True
            ),
            'development': Profile(
                name='development',
                description='Developer-friendly with warnings only',
                quality_gates={
                    'syntax_check': 'mandatory',
                    'linting': 'warn_only',
                    'type_check': 'warn_only',
                    'unit_tests': 'warn_only'
                },
                timeouts={'lint': 30, 'test': 180, 'type_check': 30},
                max_file_size=15000,
                parallel_processing=True,
                cache_enabled=True
            )
        }
    
    def get_profile(self, name: str) -> Profile:
        """
        Get a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile object
            
        Raises:
            ValueError: If profile not found
        """
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found. Available: {list(self.profiles.keys())}")
        
        return self.profiles[name]
    
    def list_profiles(self) -> Dict[str, str]:
        """
        List all available profiles.
        
        Returns:
            Dictionary mapping profile names to descriptions
        """
        return {name: profile.description for name, profile in self.profiles.items()}
    
    def add_profile(self, profile: Profile):
        """
        Add a custom profile.
        
        Args:
            profile: Profile object to add
        """
        self.profiles[profile.name] = profile
    
    def get_profile_config(self, name: str) -> Dict[str, Any]:
        """
        Get profile configuration as dictionary.
        
        Args:
            name: Profile name
            
        Returns:
            Profile configuration dictionary
        """
        profile = self.get_profile(name)
        
        return {
            'name': profile.name,
            'description': profile.description,
            'quality_gates': profile.quality_gates,
            'timeouts': profile.timeouts,
            'max_file_size': profile.max_file_size,
            'parallel_processing': profile.parallel_processing,
            'cache_enabled': profile.cache_enabled
        }

# Global profile manager instance
profile_manager = ProfileManager()

def get_profile(name: str) -> Profile:
    """Convenience function to get a profile."""
    return profile_manager.get_profile(name)

def list_profiles() -> Dict[str, str]:
    """Convenience function to list profiles."""
    return profile_manager.list_profiles()