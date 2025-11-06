"""
Create command - Generate new components
"""

import click
from pathlib import Path


AGENT_TEMPLATE = '''"""
{name} Agent
"""

from lightcrew import Agent


def create_{name_lower}_agent(llm_model: str = "gpt-4o-mini"):
    """Create {name} agent."""
    
    agent = Agent(
        role="{role}",
        goal="TODO: Define the agent's goal",
        backstory="TODO: Add agent backstory",
        llm="openai",
        llm_model=llm_model
    )
    
    return agent


if __name__ == "__main__":
    agent = create_{name_lower}_agent()
    print(f"Created agent: {{agent.role}}")
'''


TOOL_TEMPLATE = '''"""
{name} Tool
"""

from lightcrew.tools import tool


@tool(name="{name_lower}", description="TODO: Describe what this tool does")
def {name_lower}_tool(input_param: str) -> dict:
    """
    TODO: Implement your tool logic here.
    
    Args:
        input_param: Description of the parameter
        
    Returns:
        Dictionary with results
    """
    
    # Your implementation here
    result = f"Processed: {{input_param}}"
    
    return {{
        "success": True,
        "result": result
    }}


if __name__ == "__main__":
    # Test the tool
    result = {name_lower}_tool("test input")
    print(result)
'''


CREW_TEMPLATE = '''# {name} Crew Configuration

# LLM Settings
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  timeout: 60.0

# Agents
agents:
{agent_definitions}

# Tasks
tasks:
  - description: TODO: Define the first task
    agent: {first_agent}
    expected_output: Description of expected output
'''


def create_agent_template(name: str, role: str, output: str):
    """Create a new agent template file."""
    
    name_clean = name.replace('-', '_').replace(' ', '_')
    name_lower = name_clean.lower()
    role = role or name
    
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = Path(f"{name_lower}_agent.py")
    
    # Check if file exists
    if output_path.exists():
        if not click.confirm(f"File {output_path} already exists. Overwrite?"):
            click.echo("Cancelled.")
            return
    
    # Generate content
    content = AGENT_TEMPLATE.format(
        name=name,
        name_lower=name_lower,
        role=role
    )
    
    # Write file
    output_path.write_text(content)
    click.echo(f"✓ Created agent: {output_path}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Edit {output_path} and customize the agent")
    click.echo(f"  2. Import and use: from {name_lower}_agent import create_{name_lower}_agent")


def create_tool_template(name: str, output: str):
    """Create a new tool template file."""
    
    name_clean = name.replace('-', '_').replace(' ', '_')
    name_lower = name_clean.lower()
    
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = Path(f"{name_lower}_tool.py")
    
    # Check if file exists
    if output_path.exists():
        if not click.confirm(f"File {output_path} already exists. Overwrite?"):
            click.echo("Cancelled.")
            return
    
    # Generate content
    content = TOOL_TEMPLATE.format(
        name=name,
        name_lower=name_lower
    )
    
    # Write file
    output_path.write_text(content)
    click.echo(f"✓ Created tool: {output_path}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Edit {output_path} and implement your tool logic")
    click.echo(f"  2. Import and use: from {name_lower}_tool import {name_lower}_tool")


def create_crew_template(name: str, agents: list, output: str):
    """Create a new crew configuration file."""
    
    name_clean = name.replace('-', '_').replace(' ', '_')
    name_lower = name_clean.lower()
    
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = Path(f"{name_lower}_crew.yaml")
    
    # Check if file exists
    if output_path.exists():
        if not click.confirm(f"File {output_path} already exists. Overwrite?"):
            click.echo("Cancelled.")
            return
    
    # Generate agent definitions
    if agents:
        agent_defs = []
        for agent in agents:
            agent_defs.append(f"  - name: {agent}")
            agent_defs.append(f"    role: {agent.title()}")
            agent_defs.append(f"    goal: TODO: Define {agent}'s goal")
            agent_defs.append(f"    backstory: TODO: Add {agent}'s backstory")
        agent_definitions = '\n'.join(agent_defs)
        first_agent = agents[0]
    else:
        agent_definitions = "  - name: assistant\n    role: Assistant\n    goal: Help with tasks\n    backstory: I am a helpful assistant"
        first_agent = "assistant"
    
    # Generate content
    content = CREW_TEMPLATE.format(
        name=name,
        agent_definitions=agent_definitions,
        first_agent=first_agent
    )
    
    # Write file
    output_path.write_text(content)
    click.echo(f"✓ Created crew configuration: {output_path}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Edit {output_path} and customize agents and tasks")
    click.echo(f"  2. Run: lightcrew run {output_path} --interactive")
