"""
Test module for Ultimate Norbi Assistant core functionality
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from critic import CodeCritic, CriticResult
from codegen import UltimateNorbiAssistant, CodegenConfig

class TestCodeCritic:
    """Test the code critic functionality."""
    
    def test_critic_initialization(self):
        """Test that critic initializes correctly."""
        critic = CodeCritic(warn_only=True)
        assert critic.warn_only is True
        assert critic.results == []
    
    def test_python_syntax_check_valid(self):
        """Test syntax checking with valid Python code."""
        critic = CodeCritic()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')\n")
            temp_file = f.name
        
        try:
            results = critic.analyze_file(temp_file)
            
            # Should have at least syntax check result
            syntax_results = [r for r in results if r.check_type == 'python_syntax']
            assert len(syntax_results) > 0
            assert syntax_results[0].passed is True
            
        finally:
            os.unlink(temp_file)
    
    def test_python_syntax_check_invalid(self):
        """Test syntax checking with invalid Python code."""
        critic = CodeCritic()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!'\n")  # Missing closing parenthesis
            temp_file = f.name
        
        try:
            results = critic.analyze_file(temp_file)
            
            # Should have syntax check result that failed
            syntax_results = [r for r in results if r.check_type == 'python_syntax']
            assert len(syntax_results) > 0
            assert syntax_results[0].passed is False
            assert len(syntax_results[0].errors) > 0
            
        finally:
            os.unlink(temp_file)
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        critic = CodeCritic()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Some text content\n")
            temp_file = f.name
        
        try:
            results = critic.analyze_file(temp_file)
            # Should return empty list for unsupported types
            assert len(results) == 0
            
        finally:
            os.unlink(temp_file)
    
    def test_summary_generation(self):
        """Test summary generation with mock results."""
        critic = CodeCritic()
        
        # Add some mock results
        critic.results = [
            CriticResult("test1", True, [], [], [], 0.1),
            CriticResult("test2", False, ["warning"], ["error"], [], 0.2),
            CriticResult("test3", True, ["warning"], [], [], 0.1)
        ]
        
        summary = critic.get_summary()
        
        assert summary['total_checks'] == 3
        assert summary['passed_checks'] == 2
        assert summary['failed_checks'] == 1
        assert summary['total_warnings'] == 2
        assert summary['total_errors'] == 1
        assert summary['success_rate'] == 2/3

class TestCodegenConfig:
    """Test the codegen configuration."""
    
    def test_config_creation(self):
        """Test creating a configuration object."""
        config = CodegenConfig(
            policy_file="test_policy.yaml",
            prompt_file="test_prompt.md",
            preview_mode=True,
            warn_only=True
        )
        
        assert config.policy_file == "test_policy.yaml"
        assert config.prompt_file == "test_prompt.md"
        assert config.preview_mode is True
        assert config.warn_only is True

class TestUltimateNorbiAssistant:
    """Test the main assistant functionality."""
    
    def test_assistant_initialization(self):
        """Test that assistant initializes with config."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md"
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        assert assistant.config == config
        assert assistant.critic is not None
        assert assistant.policy is not None  # Should use default policy
        assert assistant.system_prompt is not None  # Should use default prompt
    
    def test_default_policy_loading(self):
        """Test loading default policy when file doesn't exist."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md"
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        # Should have loaded default policy
        assert 'version' in assistant.policy
        assert 'principles' in assistant.policy
        assert 'quality_gates' in assistant.policy
    
    def test_analyze_files_with_valid_file(self):
        """Test analyzing files with the assistant."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md"
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')\n")
            temp_file = f.name
        
        try:
            results = assistant.analyze_files([temp_file])
            assert len(results) > 0
            
        finally:
            os.unlink(temp_file)
    
    def test_analyze_files_with_nonexistent_file(self):
        """Test analyzing nonexistent files."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md"
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        # Should handle nonexistent files gracefully
        results = assistant.analyze_files(["nonexistent_file.py"])
        assert len(results) == 0
    
    def test_preview_mode(self):
        """Test preview mode functionality."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md",
            preview_mode=True
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, world!')\n")
            temp_file = f.name
        
        try:
            preview_info = assistant.preview_changes([temp_file])
            
            assert preview_info['mode'] == 'preview'
            assert preview_info['files_analyzed'] == 1
            assert 'quality_summary' in preview_info
            assert 'recommendations' in preview_info
            assert 'approval_required' in preview_info
            
        finally:
            os.unlink(temp_file)
    
    def test_recommendations_generation(self):
        """Test recommendation generation based on analysis."""
        config = CodegenConfig(
            policy_file="nonexistent_policy.yaml",
            prompt_file="nonexistent_prompt.md"
        )
        
        assistant = UltimateNorbiAssistant(config)
        
        # Test with good quality summary
        good_summary = {
            'total_errors': 0,
            'total_warnings': 2,
            'success_rate': 0.9
        }
        
        recommendations = assistant._get_recommendations(good_summary)
        assert any("ready to apply" in rec.lower() for rec in recommendations)
        
        # Test with poor quality summary
        poor_summary = {
            'total_errors': 5,
            'total_warnings': 10,
            'success_rate': 0.5
        }
        
        recommendations = assistant._get_recommendations(poor_summary)
        assert any("fix" in rec.lower() and "error" in rec.lower() for rec in recommendations)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])