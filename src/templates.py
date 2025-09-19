"""
Ultimate Norbi Assistant - Template System

Provides intelligent template selection and scaffolding for different project types.
"""

from typing import Dict, List, Optional
from pathlib import Path
import os

class Template:
    """Represents a code template."""
    
    def __init__(self, name: str, description: str, files: Dict[str, str], 
                 dependencies: List[str] = None, tags: List[str] = None):
        """
        Initialize a template.
        
        Args:
            name: Template name
            description: Template description
            files: Dictionary mapping file paths to content
            dependencies: List of required dependencies
            tags: List of template tags for categorization
        """
        self.name = name
        self.description = description
        self.files = files
        self.dependencies = dependencies or []
        self.tags = tags or []

class TemplateManager:
    """Manages code templates for different project types."""
    
    def __init__(self):
        """Initialize with built-in templates."""
        self.templates = {
            'fastapi': Template(
                name='fastapi',
                description='FastAPI REST API service',
                files={
                    'main.py': self._get_fastapi_main_template(),
                    'requirements.txt': 'fastapi>=0.100.0\nuvicorn>=0.23.0\npydantic>=2.0.0',
                    'Dockerfile': self._get_fastapi_dockerfile_template(),
                    'README.md': self._get_fastapi_readme_template()
                },
                dependencies=['fastapi', 'uvicorn', 'pydantic'],
                tags=['web', 'api', 'rest', 'backend']
            ),
            'worker': Template(
                name='worker',
                description='Background worker/CLI application',
                files={
                    'worker.py': self._get_worker_template(),
                    'cli.py': self._get_cli_template(),
                    'requirements.txt': 'click>=8.0.0\ncelery>=5.0.0\nredis>=4.0.0',
                    'README.md': self._get_worker_readme_template()
                },
                dependencies=['click', 'celery', 'redis'],
                tags=['worker', 'cli', 'background', 'queue']
            ),
            'react': Template(
                name='react',
                description='React frontend component',
                files={
                    'package.json': self._get_react_package_template(),
                    'src/App.js': self._get_react_app_template(),
                    'src/index.js': self._get_react_index_template(),
                    'public/index.html': self._get_react_html_template(),
                    'README.md': self._get_react_readme_template()
                },
                dependencies=['react', 'react-dom'],
                tags=['frontend', 'react', 'javascript', 'web']
            ),
            'python_lib': Template(
                name='python_lib',
                description='Python library package',
                files={
                    'src/__init__.py': self._get_python_lib_init_template(),
                    'src/core.py': self._get_python_lib_core_template(),
                    'tests/test_core.py': self._get_python_lib_test_template(),
                    'setup.py': self._get_python_lib_setup_template(),
                    'requirements.txt': 'pytest>=7.0.0\nblack>=23.0.0\nflake8>=6.0.0',
                    'README.md': self._get_python_lib_readme_template()
                },
                dependencies=['pytest', 'black', 'flake8'],
                tags=['python', 'library', 'package']
            )
        }
    
    def get_template(self, name: str) -> Template:
        """Get a template by name."""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found. Available: {list(self.templates.keys())}")
        return self.templates[name]
    
    def list_templates(self) -> Dict[str, str]:
        """List all available templates."""
        return {name: template.description for name, template in self.templates.items()}
    
    def suggest_template(self, context: str, requirements: List[str] = None) -> List[str]:
        """
        Suggest appropriate templates based on context and requirements.
        
        Args:
            context: Description of what needs to be built
            requirements: List of specific requirements
            
        Returns:
            List of suggested template names, ordered by relevance
        """
        context_lower = context.lower()
        requirements = requirements or []
        
        suggestions = []
        
        # Check for API/web service indicators
        if any(word in context_lower for word in ['api', 'rest', 'web', 'service', 'endpoint']):
            suggestions.append('fastapi')
        
        # Check for worker/CLI indicators
        if any(word in context_lower for word in ['worker', 'cli', 'command', 'background', 'task']):
            suggestions.append('worker')
        
        # Check for frontend indicators
        if any(word in context_lower for word in ['frontend', 'ui', 'react', 'component', 'web app']):
            suggestions.append('react')
        
        # Check for library indicators
        if any(word in context_lower for word in ['library', 'package', 'module', 'utility']):
            suggestions.append('python_lib')
        
        # Check requirements for specific technologies
        for req in requirements:
            req_lower = req.lower()
            if 'fastapi' in req_lower or 'api' in req_lower:
                if 'fastapi' not in suggestions:
                    suggestions.append('fastapi')
            elif 'react' in req_lower or 'frontend' in req_lower:
                if 'react' not in suggestions:
                    suggestions.append('react')
            elif 'worker' in req_lower or 'cli' in req_lower:
                if 'worker' not in suggestions:
                    suggestions.append('worker')
        
        # If no specific suggestions, suggest python_lib as default
        if not suggestions:
            suggestions.append('python_lib')
        
        return suggestions
    
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
        template = self.get_template(template_name)
        replacements = replacements or {}
        
        # Add default replacements
        replacements.setdefault('{{PROJECT_NAME}}', Path(target_dir).name)
        replacements.setdefault('{{DESCRIPTION}}', f'Generated from {template_name} template')
        
        created_files = []
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in template.files.items():
            # Apply replacements to content
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)
            
            # Create file
            full_path = target_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(str(full_path))
        
        return created_files
    
    # Template content methods
    def _get_fastapi_main_template(self) -> str:
        return '''"""
{{DESCRIPTION}}
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{{PROJECT_NAME}}", description="{{DESCRIPTION}}")

class Item(BaseModel):
    """Example data model."""
    name: str
    description: str = None
    price: float
    tax: float = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello, World!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/items/")
async def create_item(item: Item):
    """Create an item."""
    return {"item": item}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _get_fastapi_dockerfile_template(self) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _get_fastapi_readme_template(self) -> str:
        return '''# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.
'''
    
    def _get_worker_template(self) -> str:
        return '''"""
{{DESCRIPTION}} - Worker module
"""

import logging
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery('{{PROJECT_NAME}}', broker='redis://localhost:6379')

@app.task
def process_task(data):
    """
    Process a background task.
    
    Args:
        data: Task data to process
        
    Returns:
        Processing result
    """
    logger.info(f"Processing task with data: {data}")
    
    # Your processing logic here
    result = f"Processed: {data}"
    
    logger.info(f"Task completed: {result}")
    return result

if __name__ == "__main__":
    # Start worker
    app.start()
'''
    
    def _get_cli_template(self) -> str:
        return '''"""
{{DESCRIPTION}} - CLI interface
"""

import click
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """{{PROJECT_NAME}} command line interface."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

@cli.command()
@click.argument('name')
def hello(name):
    """Say hello to someone."""
    click.echo(f'Hello, {name}!')

@cli.command()
@click.option('--count', default=1, help='Number of greetings')
@click.argument('name')
def repeat(count, name):
    """Repeat a greeting."""
    for i in range(count):
        click.echo(f'{i+1}: Hello, {name}!')

if __name__ == '__main__':
    cli()
'''
    
    def _get_worker_readme_template(self) -> str:
        return '''# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Worker Usage

```bash
# Start worker
celery -A worker worker --loglevel=info

# Send task
python -c "from worker import process_task; process_task.delay('test data')"
```

## CLI Usage

```bash
python cli.py --help
python cli.py hello World
python cli.py repeat --count 3 World
```
'''
    
    def _get_react_package_template(self) -> str:
        return '''{
  "name": "{{PROJECT_NAME}}",
  "version": "1.0.0",
  "description": "{{DESCRIPTION}}",
  "main": "src/index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
'''
    
    def _get_react_app_template(self) -> str:
        return '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>{{PROJECT_NAME}}</h1>
        <p>{{DESCRIPTION}}</p>
      </header>
    </div>
  );
}

export default App;
'''
    
    def _get_react_index_template(self) -> str:
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    def _get_react_html_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{{DESCRIPTION}}" />
    <title>{{PROJECT_NAME}}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''
    
    def _get_react_readme_template(self) -> str:
        return '''# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Getting Started

```bash
npm install
npm start
```

The app will run at http://localhost:3000

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm build` - Builds the app for production
- `npm test` - Launches the test runner
'''
    
    def _get_python_lib_init_template(self) -> str:
        return '''"""
{{PROJECT_NAME}} - {{DESCRIPTION}}
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "{{DESCRIPTION}}"

from .core import *

__all__ = ['main_function', 'UtilityClass']
'''
    
    def _get_python_lib_core_template(self) -> str:
        return '''"""
{{PROJECT_NAME}} core functionality
"""

def main_function(data):
    """
    Main function of the library.
    
    Args:
        data: Input data to process
        
    Returns:
        Processed result
    """
    return f"Processed: {data}"

class UtilityClass:
    """Utility class for {{PROJECT_NAME}}."""
    
    def __init__(self, config=None):
        """Initialize with optional configuration."""
        self.config = config or {}
    
    def process(self, input_data):
        """Process input data."""
        return main_function(input_data)
'''
    
    def _get_python_lib_test_template(self) -> str:
        return '''"""
Tests for {{PROJECT_NAME}}
"""

import pytest
from src.core import main_function, UtilityClass

def test_main_function():
    """Test the main function."""
    result = main_function("test")
    assert result == "Processed: test"

def test_utility_class():
    """Test the utility class."""
    util = UtilityClass()
    result = util.process("test")
    assert result == "Processed: test"

def test_utility_class_with_config():
    """Test utility class with configuration."""
    config = {"key": "value"}
    util = UtilityClass(config)
    assert util.config == config
'''
    
    def _get_python_lib_setup_template(self) -> str:
        return '''from setuptools import setup, find_packages

setup(
    name="{{PROJECT_NAME}}",
    version="1.0.0",
    description="{{DESCRIPTION}}",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
'''
    
    def _get_python_lib_readme_template(self) -> str:
        return '''# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Installation

```bash
pip install -e .
```

## Usage

```python
from {{PROJECT_NAME}} import main_function, UtilityClass

# Use main function
result = main_function("data")

# Use utility class
util = UtilityClass()
result = util.process("data")
```

## Testing

```bash
pytest tests/
```
'''

# Global template manager instance
template_manager = TemplateManager()

def get_template(name: str) -> Template:
    """Convenience function to get a template."""
    return template_manager.get_template(name)

def suggest_template(context: str, requirements: List[str] = None) -> List[str]:
    """Convenience function to suggest templates."""
    return template_manager.suggest_template(context, requirements)

def list_templates() -> Dict[str, str]:
    """Convenience function to list templates."""
    return template_manager.list_templates()