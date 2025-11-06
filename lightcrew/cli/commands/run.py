"""
Run command - Execute crews from configuration files
"""

import sys
import asyncio
import click
import yaml
from pathlib import Path

from lightcrew import Agent, Task, Crew
from lightcrew.utils import get_logger

logger = get_logger(__name__)


async def execute_crew_from_config(config_path: str, query: str = None, model_override: str = None):
    """Execute a crew based on configuration file."""
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Load configuration
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get LLM settings
    llm_config = config.get('llm', {})
    llm_provider = llm_config.get('provider', 'openai')
    llm_model = model_override or llm_config.get('model', 'gpt-4o-mini')
    temperature = llm_config.get('temperature', 0.7)
    timeout = llm_config.get('timeout', 60.0)
    
    # Create agents
    agents = []
    agent_map = {}
    
    for agent_config in config.get('agents', []):
        agent = Agent(
            role=agent_config.get('role', agent_config['name']),
            goal=agent_config.get('goal', ''),
            backstory=agent_config.get('backstory', ''),
            llm=llm_provider,
            llm_model=llm_model,
            config={
                'temperature': temperature,
                'timeout': timeout
            }
        )
        agents.append(agent)
        agent_map[agent_config['name']] = agent
    
    # Create tasks
    tasks = []
    for task_config in config.get('tasks', []):
        task_description = query or task_config.get('description', '')
        agent_name = task_config.get('agent')
        
        if agent_name not in agent_map:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")
        
        task = Task(
            description=task_description,
            agent=agent_map[agent_name],
            expected_output=task_config.get('expected_output', 'Result')
        )
        tasks.append(task)
    
    # Create and execute crew
    crew = Crew(agents=agents, tasks=tasks)
    
    logger.info(f"Executing crew with {len(agents)} agent(s) and {len(tasks)} task(s)")
    result = await crew.execute()
    
    return result


def run_crew(config_file: str, interactive: bool, query: str, model: str):
    """Run crew from configuration."""
    
    click.echo(f"Loading configuration: {config_file}")
    
    if interactive:
        click.echo("Interactive mode - type 'quit' to exit\n")
        
        while True:
            try:
                user_query = input("Enter query: ").strip()
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                if not user_query:
                    continue
                
                result = asyncio.run(execute_crew_from_config(config_file, user_query, model))
                
                if result.success and result.results:
                    click.echo(f"\nResult:\n{result.results[0].output}\n")
                else:
                    error = result.results[0].error if result.results else "Unknown error"
                    click.echo(f"\nError: {error}\n", err=True)
                    
            except KeyboardInterrupt:
                click.echo("\nGoodbye!")
                break
            except Exception as e:
                click.echo(f"Error: {e}\n", err=True)
    else:
        if not query:
            click.echo("Error: --query required in non-interactive mode", err=True)
            sys.exit(1)
        
        try:
            result = asyncio.run(execute_crew_from_config(config_file, query, model))
            
            if result.success and result.results:
                click.echo(result.results[0].output)
            else:
                error = result.results[0].error if result.results else "Unknown error"
                click.echo(f"Error: {error}", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
