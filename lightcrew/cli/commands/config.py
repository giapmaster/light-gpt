"""
Config command - Manage LightCrew configuration
"""

import os
import click
from pathlib import Path


def get_config_file():
    """Get the configuration file path."""
    config_dir = Path.home() / '.lightcrew'
    config_dir.mkdir(exist_ok=True)
    return config_dir / 'config.env'


def manage_config(list_config: bool, set_key: tuple):
    """Manage configuration."""
    
    config_file = get_config_file()
    
    if list_config:
        # List current configuration
        click.echo("LightCrew Configuration:\n")
        
        # Show environment variables
        env_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'LIGHTCREW_LOG_LEVEL',
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask API keys
                if 'KEY' in var:
                    masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                    click.echo(f"{var}={masked}")
                else:
                    click.echo(f"{var}={value}")
            else:
                click.echo(f"{var}=<not set>")
        
        click.echo(f"\nConfig file: {config_file}")
        
        if config_file.exists():
            click.echo("\nStored configuration:")
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Mask values
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if 'KEY' in key:
                                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                                click.echo(f"{key}={masked}")
                            else:
                                click.echo(line)
        
    elif set_key:
        # Set a configuration key-value pair
        key, value = set_key
        
        click.echo(f"Setting {key}...")
        
        # Read existing config
        config_lines = []
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_lines = f.readlines()
        
        # Update or add the key
        key_found = False
        for i, line in enumerate(config_lines):
            if line.strip().startswith(f"{key}="):
                config_lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        if not key_found:
            config_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(config_file, 'w') as f:
            f.writelines(config_lines)
        
        click.echo(f"✓ Configuration saved to {config_file}")
        click.echo(f"\nTo use this config, run:")
        click.echo(f"  export $(cat {config_file} | xargs)")
        
    else:
        # Show help
        click.echo("LightCrew Configuration Management\n")
        click.echo("Usage:")
        click.echo("  lightcrew config --list              # Show current config")
        click.echo("  lightcrew config --set KEY VALUE     # Set a config value")
        click.echo("\nExamples:")
        click.echo("  lightcrew config --set OPENAI_API_KEY sk-...")
        click.echo("  lightcrew config --set LIGHTCREW_LOG_LEVEL DEBUG")
