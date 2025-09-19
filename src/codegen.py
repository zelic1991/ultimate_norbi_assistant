"""
Ultimate Norbi Assistant - Main Code Generation Engine

Orchestrates code generation with integrated quality gates and critic feedback.
Supports preview mode with warn-only gates and approval flows.
"""

import os
import sys
import yaml
import argparse
import logging
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

# Import our modules
from .critic import CodeCritic, CriticResult
from .profiles import ProfileManager, get_profile
from .templates import TemplateManager, suggest_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodegenConfig:
    """Configuration for code generation."""
    policy_file: str
    prompt_file: str
    preview_mode: bool = True
    warn_only: bool = True
    profile: str = "default"
    max_file_size: int = 10000
    require_tests: bool = True

class UltimateNorbiAssistant:
    """
    Main class for the Ultimate Norbi Assistant code generation system.
    """
    
    def __init__(self, config: CodegenConfig):
        """
        Initialize the assistant with configuration.
        
        Args:
            config: CodegenConfig object with settings
        """
        self.config = config
        self.policy = self._load_policy()
        self.system_prompt = self._load_system_prompt()
        self.critic = CodeCritic(warn_only=config.warn_only)
        self.repo_root = self._find_repo_root()
        self.profile_manager = ProfileManager()
        self.template_manager = TemplateManager()
        
        # Apply profile settings if specified
        if config.profile != "default":
            self._apply_profile_settings(config.profile)
        
    def _find_repo_root(self) -> str:
        """Find the repository root directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return str(current)
            current = current.parent
        return str(Path.cwd())
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load the code generation policy from YAML file."""
        try:
            with open(self.config.policy_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Policy file not found: {self.config.policy_file}")
            return self._get_default_policy()
        except Exception as e:
            logger.error(f"Error loading policy: {e}")
            return self._get_default_policy()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from markdown file."""
        try:
            with open(self.config.prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {self.config.prompt_file}")
            return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return self._get_default_prompt()
    
    def _get_default_policy(self) -> Dict[str, Any]:
        """Return default policy when file is not available."""
        return {
            'version': '1.0',
            'principles': ['Minimal changes only', 'Preserve functionality'],
            'quality_gates': {
                'syntax_check': 'mandatory',
                'linting': 'warn_only',
                'type_check': 'warn_only',
                'unit_tests': 'mandatory'
            },
            'preview_mode': {
                'enabled': True,
                'warn_only_gates': True
            }
        }
    
    def _get_default_prompt(self) -> str:
        """Return default system prompt when file is not available."""
        return """
You are the Ultimate Norbi Assistant. Make minimal, surgical code changes while preserving existing functionality.
Follow existing patterns and validate all changes through testing.
"""
    
    def analyze_files(self, file_paths: List[str]) -> List[CriticResult]:
        """
        Analyze multiple files using the code critic.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            List of CriticResult objects
        """
        all_results = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                logger.info(f"Analyzing {file_path}...")
                results = self.critic.analyze_file(file_path)
                all_results.extend(results)
            else:
                logger.warning(f"File not found: {file_path}")
        
        return all_results
    
    def run_quality_gates(self, file_paths: List[str]) -> bool:
        """
        Run quality gates on the specified files.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            True if all gates pass or in warn-only mode, False if blocking errors found
        """
        logger.info("Running quality gates...")
        
        # Analyze files with critic
        results = self.analyze_files(file_paths)
        
        # Check policy requirements
        policy_gates = self.policy.get('quality_gates', {})
        
        blocking_errors = []
        warnings = []
        
        for result in results:
            if not result.passed:
                if policy_gates.get(result.check_type) == 'mandatory' and not self.config.warn_only:
                    blocking_errors.extend(result.errors)
                else:
                    warnings.extend(result.errors)
            
            warnings.extend(result.warnings)
        
        # Print summary
        self.critic.print_summary()
        
        if blocking_errors and not self.config.warn_only:
            logger.error(f"Blocking errors found: {len(blocking_errors)}")
            for error in blocking_errors:
                logger.error(f"  ❌ {error}")
            return False
        
        if warnings:
            logger.warning(f"Warnings found: {len(warnings)}")
            for warning in warnings[:5]:  # Show first 5 warnings
                logger.warning(f"  ⚠️  {warning}")
            if len(warnings) > 5:
                logger.warning(f"  ... and {len(warnings) - 5} more warnings")
        
        return True
    
    def preview_changes(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Preview changes that would be made to files.
        
        Args:
            file_paths: List of file paths to preview
            
        Returns:
            Dictionary with preview information
        """
        logger.info("Running preview mode...")
        
        # In preview mode, always use warn-only
        original_warn_only = self.config.warn_only
        self.config.warn_only = True
        self.critic.warn_only = True
        
        try:
            # Run quality gates in warn-only mode
            gates_passed = self.run_quality_gates(file_paths)
            
            # Get analysis summary
            summary = self.critic.get_summary()
            
            preview_info = {
                'mode': 'preview',
                'files_analyzed': len(file_paths),
                'gates_passed': gates_passed,
                'quality_summary': summary,
                'recommendations': self._get_recommendations(summary),
                'approval_required': self._requires_approval(file_paths, summary)
            }
            
            return preview_info
            
        finally:
            # Restore original settings
            self.config.warn_only = original_warn_only
            self.critic.warn_only = original_warn_only
    
    def _get_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis summary."""
        recommendations = []
        
        if summary['total_errors'] > 0:
            recommendations.append(f"Fix {summary['total_errors']} error(s) before applying changes")
        
        if summary['total_warnings'] > 5:
            recommendations.append(f"Consider addressing {summary['total_warnings']} warning(s)")
        
        if summary['success_rate'] < 0.8:
            recommendations.append("Review failed quality checks before proceeding")
        
        if not recommendations:
            recommendations.append("Code quality looks good - ready to apply changes")
        
        return recommendations
    
    def _requires_approval(self, file_paths: List[str], summary: Dict[str, Any]) -> bool:
        """Determine if manual approval is required based on policy."""
        approval_policy = self.policy.get('approval_flow', {})
        
        # Check file count threshold
        if len(file_paths) > approval_policy.get('require_manual_approval_threshold', 100):
            return True
        
        # Check if there are critical errors
        if summary['total_errors'] > 0:
            return True
        
        # Check success rate
        if summary['success_rate'] < 0.9:
            return True
        
        return False
    
    def apply_changes(self, file_paths: List[str], force: bool = False) -> bool:
        """
        Apply changes to files after running quality gates.
        
        Args:
            file_paths: List of file paths to process
            force: Skip quality gates if True
            
        Returns:
            True if changes applied successfully, False otherwise
        """
        logger.info("Applying changes...")
        
        if not force:
            # Run quality gates first
            if not self.run_quality_gates(file_paths):
                logger.error("Quality gates failed - aborting apply")
                return False
        
        # Here you would integrate with your actual code generation logic
        # For now, we'll just report that we would apply changes
        logger.info(f"Would apply changes to {len(file_paths)} files")
        
        return True
    
    def run_tests(self, test_paths: Optional[List[str]] = None) -> bool:
        """
        Run tests to validate changes.
        
        Args:
            test_paths: Optional list of specific test paths
            
        Returns:
            True if tests pass, False otherwise
        """
        logger.info("Running tests...")
        
        # Try to find and run tests
        if not test_paths:
            test_paths = self._find_test_files()
        
        if not test_paths:
            logger.warning("No tests found")
            return True
        
        # Run pytest if available
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest'] + test_paths + ['-v'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("Tests passed ✅")
                return True
            else:
                logger.error("Tests failed ❌")
                logger.error(result.stdout)
                logger.error(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Tests timed out")
            return False
        except FileNotFoundError:
            logger.warning("pytest not available - skipping tests")
            return True
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    def _find_test_files(self) -> List[str]:
        """Find test files in the repository."""
        test_files = []
        test_dirs = ['tests', 'test']
        
        for test_dir in test_dirs:
            test_path = Path(self.repo_root) / test_dir
            if test_path.exists():
                test_files.extend([
                    str(f) for f in test_path.rglob('test_*.py')
                ])
                test_files.extend([
                    str(f) for f in test_path.rglob('*_test.py')
                ])
        
        return test_files
    
    def _apply_profile_settings(self, profile_name: str):
        """Apply settings from a performance profile."""
        try:
            profile = self.profile_manager.get_profile(profile_name)
            
            # Update policy with profile settings
            if 'quality_gates' not in self.policy:
                self.policy['quality_gates'] = {}
            
            self.policy['quality_gates'].update(profile.quality_gates)
            
            # Update config with profile settings
            self.config.max_file_size = profile.max_file_size
            
            logger.info(f"Applied profile '{profile_name}': {profile.description}")
            
        except ValueError as e:
            logger.warning(f"Profile error: {e}")
    
    def suggest_templates(self, context: str, requirements: List[str] = None) -> List[str]:
        """
        Suggest appropriate templates based on context.
        
        Args:
            context: Description of what needs to be built
            requirements: List of specific requirements
            
        Returns:
            List of suggested template names
        """
        return self.template_manager.suggest_template(context, requirements)
    
    def create_from_template(self, template_name: str, target_dir: str, 
                           replacements: Dict[str, str] = None) -> List[str]:
        """
        Create files from a template.
        
        Args:
            template_name: Name of template to use
            target_dir: Directory to create files in
            replacements: Dictionary of placeholder replacements
            
        Returns:
            List of created file paths
        """
        return self.template_manager.create_from_template(template_name, target_dir, replacements)

def create_config_from_args(args: argparse.Namespace) -> CodegenConfig:
    """Create CodegenConfig from command line arguments."""
    repo_root = Path.cwd()
    while repo_root != repo_root.parent and not (repo_root / '.git').exists():
        repo_root = repo_root.parent
    
    return CodegenConfig(
        policy_file=args.policy or str(repo_root / 'POLICIES' / 'codegen_policy.yaml'),
        prompt_file=args.prompt or str(repo_root / 'prompts' / 'system_codegen.md'),
        preview_mode=args.preview,
        warn_only=args.warn_only,
        profile=args.profile,
        max_file_size=args.max_file_size,
        require_tests=not args.skip_tests
    )

def main():
    """Main entry point for the code generation system."""
    parser = argparse.ArgumentParser(description="Ultimate Norbi Assistant Code Generator")
    
    parser.add_argument("files", nargs="*", help="Files to analyze/process")
    parser.add_argument("--policy", help="Path to policy YAML file")
    parser.add_argument("--prompt", help="Path to system prompt file")
    parser.add_argument("--preview", action="store_true", default=True,
                       help="Run in preview mode (default)")
    parser.add_argument("--apply", action="store_true",
                       help="Apply changes (exits preview mode)")
    parser.add_argument("--warn-only", action="store_true", default=True,
                       help="Only warn about issues, don't block (default)")
    parser.add_argument("--strict", action="store_true",
                       help="Block execution on quality gate failures")
    parser.add_argument("--profile", default="default",
                       help="Performance profile to use (default, fast, strict, development)")
    parser.add_argument("--max-file-size", type=int, default=10000,
                       help="Maximum file size to process (lines)")
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip running tests")
    parser.add_argument("--force", action="store_true",
                       help="Skip quality gates when applying changes")
    parser.add_argument("--list-profiles", action="store_true",
                       help="List available performance profiles")
    parser.add_argument("--list-templates", action="store_true",
                       help="List available templates")
    parser.add_argument("--suggest-template", metavar="CONTEXT",
                       help="Suggest templates based on context description")
    parser.add_argument("--create-template", nargs=2, metavar=("TEMPLATE", "DIR"),
                       help="Create files from template in specified directory")
    
    args = parser.parse_args()
    
    # Adjust settings based on arguments
    if args.strict:
        args.warn_only = False
    if args.apply:
        args.preview = False
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Handle special commands first
    if args.list_profiles:
        from .profiles import list_profiles
        profiles = list_profiles()
        print("Available performance profiles:")
        for name, desc in profiles.items():
            print(f"  {name:<12} - {desc}")
        sys.exit(0)
    
    if args.list_templates:
        from .templates import list_templates
        templates = list_templates()
        print("Available templates:")
        for name, desc in templates.items():
            print(f"  {name:<12} - {desc}")
        sys.exit(0)
    
    if args.suggest_template:
        from .templates import suggest_template
        suggestions = suggest_template(args.suggest_template)
        print(f"Suggested templates for '{args.suggest_template}':")
        for template in suggestions:
            print(f"  {template}")
        sys.exit(0)
    
    if args.create_template:
        template_name, target_dir = args.create_template
        from .templates import template_manager
        try:
            created_files = template_manager.create_from_template(template_name, target_dir)
            print(f"Created {len(created_files)} files from '{template_name}' template:")
            for file_path in created_files:
                print(f"  {file_path}")
        except ValueError as e:
            logger.error(f"Template error: {e}")
            sys.exit(1)
        sys.exit(0)
    
    # Initialize assistant
    assistant = UltimateNorbiAssistant(config)
    
    # Determine files to process
    files_to_process = args.files
    if not files_to_process:
        # Find Python files in current directory
        files_to_process = [str(f) for f in Path.cwd().rglob('*.py') if f.is_file()]
        files_to_process = files_to_process[:10]  # Limit to first 10 files
    
    if not files_to_process:
        logger.error("No files to process")
        sys.exit(1)
    
    logger.info(f"Processing {len(files_to_process)} files")
    
    try:
        if args.preview:
            # Run in preview mode
            preview_info = assistant.preview_changes(files_to_process)
            
            print(f"\n{'='*60}")
            print(f"PREVIEW MODE RESULTS")
            print(f"{'='*60}")
            print(f"Files analyzed: {preview_info['files_analyzed']}")
            print(f"Quality gates: {'PASS' if preview_info['gates_passed'] else 'FAIL'}")
            print(f"Approval required: {'YES' if preview_info['approval_required'] else 'NO'}")
            
            print(f"\nRecommendations:")
            for rec in preview_info['recommendations']:
                print(f"  💡 {rec}")
            
        else:
            # Apply mode
            success = assistant.apply_changes(files_to_process, force=args.force)
            
            if success and config.require_tests:
                success = assistant.run_tests()
            
            if success:
                logger.info("Operation completed successfully ✅")
                sys.exit(0)
            else:
                logger.error("Operation failed ❌")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()