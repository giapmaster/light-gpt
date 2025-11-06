#!/usr/bin/env python3
"""
LightCrew CLI - Main entry point
"""

import click
import sys
from pathlib import Path

from lightcrew import __version__


@click.group()
@click.version_option(version=__version__, prog_name="lightcrew")
@click.pass_context
def cli(ctx):
    """
    LightCrew - Lightweight AI Agent Framework CLI
    
    Build, manage, and run AI agent crews with ease.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.argument('project_name', required=False, default='.')
@click.option('--template', '-t', type=click.Choice(['minimal', 'basic', 'full']), 
              default='basic', help='Project template to use')
def init(project_name, template):
    """Initialize a new LightCrew project."""
    from lightcrew.cli.commands.init import init_project
    init_project(project_name, template)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
@click.option('--query', '-q', help='Single query to run')
@click.option('--model', '-m', help='LLM model to use')
def run(config_file, interactive, query, model):
    """Run a crew from a configuration file."""
    from lightcrew.cli.commands.run import run_crew
    run_crew(config_file, interactive, query, model)


@cli.group()
def create():
    """Create new LightCrew components."""
    pass


@create.command('agent')
@click.argument('name')
@click.option('--role', '-r', help='Agent role')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def create_agent(name, role, output):
    """Create a new agent template."""
    from lightcrew.cli.commands.create import create_agent_template
    create_agent_template(name, role, output)


@create.command('tool')
@click.argument('name')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def create_tool(name, output):
    """Create a new tool template."""
    from lightcrew.cli.commands.create import create_tool_template
    create_tool_template(name, output)


@create.command('crew')
@click.argument('name')
@click.option('--agents', '-a', multiple=True, help='Agent names to include')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def create_crew(name, agents, output):
    """Create a new crew configuration."""
    from lightcrew.cli.commands.create import create_crew_template
    create_crew_template(name, list(agents), output)


@cli.group()
def examples():
    """Manage and run example projects."""
    pass


@examples.command('list')
def list_examples():
    """List available examples."""
    from lightcrew.cli.commands.examples import list_available_examples
    list_available_examples()


@examples.command('run')
@click.argument('example_name')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
def run_example(example_name, interactive):
    """Run a specific example."""
    from lightcrew.cli.commands.examples import run_specific_example
    run_specific_example(example_name, interactive)


@cli.command()
@click.option('--list', '-l', 'list_config', is_flag=True, help='List current configuration')
@click.option('--set', '-s', 'set_key', nargs=2, type=str, help='Set a configuration key-value pair')
def config(list_config, set_key):
    """Manage LightCrew configuration."""
    from lightcrew.cli.commands.config import manage_config
    manage_config(list_config, set_key)


def main():
    """Main entry point for CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
