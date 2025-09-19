"""
Ultimate Norbi Assistant - Code Critic Module

Provides code quality analysis and feedback in warn-only mode for preview flows.
Integrates with quality gates for linting, type checking, and testing.
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CriticResult:
    """Represents the result of a code quality check."""
    check_type: str
    passed: bool
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]
    execution_time: float

class CodeCritic:
    """
    Main code critic class that performs quality analysis on code changes.
    Operates in warn-only mode for preview flows.
    """
    
    def __init__(self, warn_only: bool = True, repo_root: Optional[str] = None):
        """
        Initialize the code critic.
        
        Args:
            warn_only: If True, only warn about issues without blocking
            repo_root: Root directory of the repository
        """
        self.warn_only = warn_only
        self.repo_root = repo_root or os.getcwd()
        self.results: List[CriticResult] = []
    
    def analyze_file(self, file_path: str) -> List[CriticResult]:
        """
        Analyze a single file for code quality issues.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of CriticResult objects
        """
        results = []
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.py':
            results.extend(self._analyze_python_file(file_path))
        elif file_ext == '.ps1':
            results.extend(self._analyze_powershell_file(file_path))
        elif file_ext in ['.js', '.ts']:
            results.extend(self._analyze_javascript_file(file_path))
        else:
            logger.info(f"No specific analysis available for {file_ext} files")
        
        self.results.extend(results)
        return results
    
    def _analyze_python_file(self, file_path: str) -> List[CriticResult]:
        """Analyze a Python file for quality issues."""
        results = []
        
        # Syntax check
        syntax_result = self._check_python_syntax(file_path)
        results.append(syntax_result)
        
        # Linting with flake8 if available
        lint_result = self._run_python_linter(file_path)
        if lint_result:
            results.append(lint_result)
        
        # Type checking with mypy if available
        type_result = self._run_python_type_check(file_path)
        if type_result:
            results.append(type_result)
        
        return results
    
    def _analyze_powershell_file(self, file_path: str) -> List[CriticResult]:
        """Analyze a PowerShell file for quality issues."""
        results = []
        
        # Basic syntax check
        syntax_result = self._check_powershell_syntax(file_path)
        results.append(syntax_result)
        
        # PSScriptAnalyzer if available
        lint_result = self._run_powershell_analyzer(file_path)
        if lint_result:
            results.append(lint_result)
        
        return results
    
    def _analyze_javascript_file(self, file_path: str) -> List[CriticResult]:
        """Analyze a JavaScript/TypeScript file for quality issues."""
        results = []
        
        # ESLint if available
        lint_result = self._run_eslint(file_path)
        if lint_result:
            results.append(lint_result)
        
        return results
    
    def _check_python_syntax(self, file_path: str) -> CriticResult:
        """Check Python file syntax."""
        import time
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
            
            return CriticResult(
                check_type="python_syntax",
                passed=True,
                warnings=[],
                errors=[],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except SyntaxError as e:
            return CriticResult(
                check_type="python_syntax",
                passed=False,
                warnings=[],
                errors=[f"Syntax error at line {e.lineno}: {e.msg}"],
                suggestions=["Fix syntax errors before proceeding"],
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return CriticResult(
                check_type="python_syntax",
                passed=False,
                warnings=[],
                errors=[f"Error checking syntax: {str(e)}"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
    
    def _run_python_linter(self, file_path: str) -> Optional[CriticResult]:
        """Run Python linter (flake8) if available."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['flake8', '--max-line-length=120', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            warnings = []
            errors = []
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        if 'error' in line.lower():
                            errors.append(line)
                        else:
                            warnings.append(line)
            
            return CriticResult(
                check_type="python_lint",
                passed=result.returncode == 0,
                warnings=warnings,
                errors=errors,
                suggestions=["Consider fixing linting issues for better code quality"],
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return CriticResult(
                check_type="python_lint",
                passed=False,
                warnings=[],
                errors=["Linting timed out"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            logger.debug("flake8 not found, skipping Python linting")
            return None
        except Exception as e:
            logger.debug(f"Error running flake8: {e}")
            return None
    
    def _run_python_type_check(self, file_path: str) -> Optional[CriticResult]:
        """Run Python type checker (mypy) if available."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['mypy', '--ignore-missing-imports', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            warnings = []
            errors = []
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and ':' in line:
                        if 'error' in line.lower():
                            errors.append(line)
                        else:
                            warnings.append(line)
            
            return CriticResult(
                check_type="python_types",
                passed=result.returncode == 0,
                warnings=warnings,
                errors=errors,
                suggestions=["Consider adding type hints for better code clarity"],
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return CriticResult(
                check_type="python_types",
                passed=False,
                warnings=[],
                errors=["Type checking timed out"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            logger.debug("mypy not found, skipping Python type checking")
            return None
        except Exception as e:
            logger.debug(f"Error running mypy: {e}")
            return None
    
    def _check_powershell_syntax(self, file_path: str) -> CriticResult:
        """Check PowerShell file syntax."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['pwsh', '-NoProfile', '-Command', f'$null = Get-Command -Syntax (Get-Content "{file_path}" -Raw)'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return CriticResult(
                check_type="powershell_syntax",
                passed=result.returncode == 0,
                warnings=[],
                errors=[] if result.returncode == 0 else [result.stderr.strip()],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return CriticResult(
                check_type="powershell_syntax",
                passed=False,
                warnings=[],
                errors=["Syntax check timed out"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            logger.debug("PowerShell not found, skipping syntax check")
            return CriticResult(
                check_type="powershell_syntax",
                passed=False,
                warnings=["PowerShell not available for syntax checking"],
                errors=[],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return CriticResult(
                check_type="powershell_syntax",
                passed=False,
                warnings=[],
                errors=[f"Error checking PowerShell syntax: {str(e)}"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
    
    def _run_powershell_analyzer(self, file_path: str) -> Optional[CriticResult]:
        """Run PSScriptAnalyzer if available."""
        import time
        start_time = time.time()
        
        try:
            cmd = f'Invoke-ScriptAnalyzer -Path "{file_path}" | ConvertTo-Json'
            result = subprocess.run(
                ['pwsh', '-NoProfile', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            warnings = []
            errors = []
            
            if result.stdout and result.stdout.strip():
                # Parse JSON output if available
                import json
                try:
                    issues = json.loads(result.stdout)
                    if isinstance(issues, list):
                        for issue in issues:
                            severity = issue.get('Severity', '').lower()
                            message = f"Line {issue.get('Line', '?')}: {issue.get('Message', '')}"
                            
                            if severity in ['error', 'parseerror']:
                                errors.append(message)
                            else:
                                warnings.append(message)
                except json.JSONDecodeError:
                    pass
            
            return CriticResult(
                check_type="powershell_analyzer",
                passed=len(errors) == 0,
                warnings=warnings,
                errors=errors,
                suggestions=["Consider fixing PowerShell analyzer issues"],
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return CriticResult(
                check_type="powershell_analyzer",
                passed=False,
                warnings=[],
                errors=["PowerShell analysis timed out"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            logger.debug("PowerShell not found, skipping PSScriptAnalyzer")
            return None
        except Exception as e:
            logger.debug(f"Error running PSScriptAnalyzer: {e}")
            return None
    
    def _run_eslint(self, file_path: str) -> Optional[CriticResult]:
        """Run ESLint if available."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['eslint', '--format=json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            warnings = []
            errors = []
            
            if result.stdout:
                import json
                try:
                    data = json.loads(result.stdout)
                    if data and len(data) > 0:
                        for message in data[0].get('messages', []):
                            severity = message.get('severity', 1)
                            text = f"Line {message.get('line', '?')}: {message.get('message', '')}"
                            
                            if severity >= 2:
                                errors.append(text)
                            else:
                                warnings.append(text)
                except json.JSONDecodeError:
                    pass
            
            return CriticResult(
                check_type="javascript_lint",
                passed=len(errors) == 0,
                warnings=warnings,
                errors=errors,
                suggestions=["Consider fixing ESLint issues"],
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return CriticResult(
                check_type="javascript_lint",
                passed=False,
                warnings=[],
                errors=["ESLint analysis timed out"],
                suggestions=[],
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            logger.debug("ESLint not found, skipping JavaScript linting")
            return None
        except Exception as e:
            logger.debug(f"Error running ESLint: {e}")
            return None
    
    def get_summary(self) -> Dict[str, any]:
        """Get a summary of all analysis results."""
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results if r.passed])
        total_warnings = sum(len(r.warnings) for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        
        return {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'total_warnings': total_warnings,
            'total_errors': total_errors,
            'success_rate': passed_checks / total_checks if total_checks > 0 else 1.0,
            'results': self.results
        }
    
    def print_summary(self):
        """Print a formatted summary of the analysis."""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"CODE CRITIC ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed_checks']}")
        print(f"Failed: {summary['failed_checks']}")
        print(f"Warnings: {summary['total_warnings']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        
        if self.warn_only:
            print(f"\nMode: WARN-ONLY (Issues will not block execution)")
        else:
            print(f"\nMode: BLOCKING (Errors will block execution)")
        
        # Print detailed results
        for result in self.results:
            print(f"\n{'-'*40}")
            print(f"Check: {result.check_type}")
            print(f"Status: {'PASS' if result.passed else 'FAIL'}")
            print(f"Time: {result.execution_time:.2f}s")
            
            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  ❌ {error}")
            
            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")
            
            if result.suggestions:
                print("Suggestions:")
                for suggestion in result.suggestions:
                    print(f"  💡 {suggestion}")

def main():
    """Main entry point for the critic module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultimate Norbi Assistant Code Critic")
    parser.add_argument("files", nargs="+", help="Files to analyze")
    parser.add_argument("--warn-only", action="store_true", default=True,
                       help="Only warn about issues, don't block (default)")
    parser.add_argument("--strict", action="store_true",
                       help="Block execution on errors")
    
    args = parser.parse_args()
    
    critic = CodeCritic(warn_only=not args.strict)
    
    for file_path in args.files:
        if os.path.exists(file_path):
            print(f"Analyzing {file_path}...")
            critic.analyze_file(file_path)
        else:
            print(f"Warning: File {file_path} not found")
    
    critic.print_summary()
    
    # Exit with error code if in strict mode and there are errors
    if not args.warn_only:
        summary = critic.get_summary()
        if summary['total_errors'] > 0:
            sys.exit(1)

if __name__ == "__main__":
    main()