"""
Examples command - Manage and run example projects
"""

import os
import sys
import click
import subprocess
from pathlib import Path


def get_examples_dir():
    """Get the examples directory path."""
    
    # Try to find examples directory relative to lightcrew package
    try:
        import lightcrew
        package_dir = Path(lightcrew.__file__).parent.parent
        examples_dir = package_dir / 'examples'
        
        if examples_dir.exists():
            return examples_dir
    except:
        pass
    
    # Try current working directory
    cwd_examples = Path.cwd() / 'examples'
    if cwd_examples.exists():
        return cwd_examples
    
    return None


def list_available_examples():
    """List all available examples."""
    
    examples_dir = get_examples_dir()
    
    if not examples_dir:
        click.echo("No examples directory found.", err=True)
        click.echo("Make sure you're running from the LightCrew project root.")
        return
    
    click.echo("Available LightCrew Examples:\n")
    
    # Find all example directories
    examples = []
    for item in examples_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            readme = item / 'README.md'
            main_py = item / 'main.py'
            
            if main_py.exists():
                examples.append({
                    'name': item.name,
                    'path': item,
                    'has_readme': readme.exists()
                })
    
    if not examples:
        click.echo("No examples found.")
        return
    
    # Display examples
    for i, example in enumerate(examples, 1):
        click.echo(f"{i}. {example['name']}")
        
        # Try to get description from README
        if example['has_readme']:
            readme_path = example['path'] / 'README.md'
            try:
                with open(readme_path, 'r') as f:
                    lines = f.readlines()
                    # Get first non-empty, non-heading line
                    for line in lines[1:6]:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            click.echo(f"   {line[:80]}")
                            break
            except:
                pass
        
        click.echo(f"   Path: {example['path']}")
        click.echo()
    
    click.echo(f"Total: {len(examples)} example(s)")
    click.echo("\nTo run an example:")
    click.echo("  lightcrew examples run <example_name> --interactive")


def run_specific_example(example_name: str, interactive: bool):
    """Run a specific example."""
    
    examples_dir = get_examples_dir()
    
    if not examples_dir:
        click.echo("No examples directory found.", err=True)
        return
    
    # Find the example
    example_path = examples_dir / example_name
    
    if not example_path.exists() or not example_path.is_dir():
        click.echo(f"Example '{example_name}' not found.", err=True)
        click.echo("\nAvailable examples:")
        list_available_examples()
        return
    
    # Check for main.py
    main_file = example_path / 'main.py'
    if not main_file.exists():
        click.echo(f"No main.py found in {example_name}", err=True)
        return
    
    # Check for requirements
    req_file = example_path / 'requirements.txt'
    if req_file.exists():
        click.echo(f"Note: This example has additional requirements.")
        click.echo(f"Install them with: pip install -r {req_file}")
        click.echo()
    
    # Build command
    cmd = [sys.executable, str(main_file)]
    if interactive:
        cmd.append('--interactive')
    
    click.echo(f"Running example: {example_name}")
    click.echo(f"Command: {' '.join(cmd)}\n")
    
    # Run the example
    try:
        subprocess.run(cmd, cwd=str(example_path))
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user")
    except Exception as e:
        click.echo(f"Error running example: {e}", err=True)
