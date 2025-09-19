#!/usr/bin/env python3
"""
Ultimate Norbi Assistant - Usage Examples

This script demonstrates the key features of the Ultimate Norbi Assistant.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import (
    UltimateNorbiAssistant, 
    CodegenConfig,
    CodeCritic,
    list_profiles,
    list_templates,
    suggest_template
)

def demo_code_critic():
    """Demonstrate the code critic functionality."""
    print("🔍 Code Critic Demo")
    print("=" * 50)
    
    # Create a test Python file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def hello_world():
    print("Hello, World!")

def calculate_sum(a, b):
    return a + b

if __name__ == "__main__":
    hello_world()
    result = calculate_sum(5, 3)
    print(f"5 + 3 = {result}")
""")
        test_file = f.name
    
    try:
        # Analyze the file
        critic = CodeCritic(warn_only=True)
        results = critic.analyze_file(test_file)
        
        print(f"Analyzed file: {test_file}")
        print(f"Found {len(results)} checks")
        
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {result.check_type}: {status}")
        
        print()
        
    finally:
        os.unlink(test_file)

def demo_profiles():
    """Demonstrate performance profiles."""
    print("⚡ Performance Profiles Demo")
    print("=" * 50)
    
    profiles = list_profiles()
    for name, description in profiles.items():
        print(f"  {name:<12} - {description}")
    
    print()

def demo_templates():
    """Demonstrate template system."""
    print("📁 Template System Demo")
    print("=" * 50)
    
    # List available templates
    templates = list_templates()
    print("Available templates:")
    for name, description in templates.items():
        print(f"  {name:<12} - {description}")
    
    print()
    
    # Demonstrate template suggestions
    contexts = [
        "I need to build a REST API for user management",
        "Create a background worker for data processing",
        "Build a React frontend with components",
        "Create a Python utility library"
    ]
    
    print("Template suggestions:")
    for context in contexts:
        suggestions = suggest_template(context)
        print(f"  '{context[:30]}...' → {', '.join(suggestions)}")
    
    print()

def demo_preview_mode():
    """Demonstrate preview mode functionality."""
    print("👀 Preview Mode Demo")
    print("=" * 50)
    
    # Create config
    config = CodegenConfig(
        policy_file="POLICIES/codegen_policy.yaml",
        prompt_file="prompts/system_codegen.md",
        preview_mode=True,
        warn_only=True
    )
    
    # Initialize assistant
    assistant = UltimateNorbiAssistant(config)
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello from preview mode!')")
        test_file = f.name
    
    try:
        # Run preview
        preview_info = assistant.preview_changes([test_file])
        
        print(f"Files analyzed: {preview_info['files_analyzed']}")
        print(f"Quality gates: {'PASS' if preview_info['gates_passed'] else 'FAIL'}")
        print(f"Approval required: {'YES' if preview_info['approval_required'] else 'NO'}")
        
        print("Recommendations:")
        for rec in preview_info['recommendations']:
            print(f"  💡 {rec}")
        
        print()
        
    finally:
        os.unlink(test_file)

def main():
    """Run all demos."""
    print("🚀 Ultimate Norbi Assistant - Feature Demo")
    print("=" * 60)
    print()
    
    try:
        demo_code_critic()
        demo_profiles()
        demo_templates() 
        demo_preview_mode()
        
        print("✅ All demos completed successfully!")
        print()
        print("To use the Ultimate Norbi Assistant:")
        print("  python -m src.codegen --help")
        print("  python -m src.codegen --preview your_file.py")
        print("  python -m src.codegen --list-templates")
        print("  python -m src.codegen --create-template fastapi ./my-api")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())