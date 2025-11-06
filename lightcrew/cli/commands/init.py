"""
Init command - Initialize new LightCrew projects
"""

import os
import click
from pathlib import Path


MINIMAL_MAIN = '''#!/usr/bin/env python3
"""
{project_name} - LightCrew Project
"""

import asyncio
from lightcrew import Agent, Task, Crew


async def main():
    """Main entry point."""
    agent = Agent(
        role="Assistant",
        goal="Help with tasks",
        llm="openai",
        llm_model="gpt-4o-mini"
    )
    
    task = Task(
        description="Say hello and introduce yourself",
        agent=agent,
        expected_output="A friendly greeting"
    )
    
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.execute()
    
    if result.success:
        print(result.results[0].output)
    else:
        print("Error:", result.results[0].error)


if __name__ == "__main__":
    asyncio.run(main())
'''


BASIC_MAIN = '''#!/usr/bin/env python3
"""
{project_name} - LightCrew Project
"""

import asyncio
import argparse
from lightcrew import Agent, Task, Crew
from lightcrew.utils import get_logger

logger = get_logger(__name__)


async def run_crew(query: str, model: str = "gpt-4o-mini"):
    """Run the crew with a query."""
    
    # Define your agent
    agent = Agent(
        role="Helpful Assistant",
        goal="Answer user questions accurately and helpfully",
        backstory="You are a knowledgeable AI assistant.",
        llm="openai",
        llm_model=model
    )
    
    # Create a task
    task = Task(
        description=query,
        agent=agent,
        expected_output="A clear and helpful answer"
    )
    
    # Create and run crew
    crew = Crew(agents=[agent], tasks=[task])
    
    logger.info("Starting crew execution...")
    result = await crew.execute()
    
    if result.success and result.results:
        return result.results[0].output
    else:
        error = result.results[0].error if result.results else "Unknown error"
        raise RuntimeError(error)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="{project_name}")
    parser.add_argument("--query", "-q", help="Query to process")
    parser.add_argument("--model", "-m", default="gpt-4o-mini", help="LLM model")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("{project_name} - Interactive Mode (type 'quit' to exit)")
        while True:
            try:
                query = input("\\nEnter query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if not query:
                    continue
                    
                answer = await run_crew(query, args.model)
                print(f"\\nAnswer: {{answer}}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {{e}}")
    else:
        if not args.query:
            parser.print_help()
            return
            
        answer = await run_crew(args.query, args.model)
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())
'''


BASIC_CONFIG = '''# {project_name} Configuration

# LLM Settings
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  timeout: 60.0

# Agent Definitions
agents:
  - name: assistant
    role: Helpful Assistant
    goal: Answer user questions accurately
    backstory: You are a knowledgeable AI assistant

# Tasks
tasks:
  - description: Answer the user's question
    agent: assistant
    expected_output: A clear and helpful answer
'''


ENV_TEMPLATE = '''# Environment Variables
# Add your API keys here

# OpenAI API Key (required for OpenAI integration)
OPENAI_API_KEY=your_api_key_here

# Optional: Other LLM providers
# ANTHROPIC_API_KEY=your_key_here
'''


GITIGNORE = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/

# Virtual Environment
venv/
env/

# Environment Variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store

# Logs
*.log
'''


README_TEMPLATE = '''# {project_name}

A LightCrew AI agent project.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your API key in `.env`:
```bash
OPENAI_API_KEY=your_key_here
```

## Usage

### Interactive Mode
```bash
python main.py --interactive
```

### Single Query
```bash
python main.py --query "Your question here"
```

## Configuration

Edit `config.yaml` to customize agents and tasks.

## Learn More

- [LightCrew Documentation](https://github.com/yourusername/lightcrew)
- [Examples](https://github.com/yourusername/lightcrew/tree/main/examples)
'''


REQUIREMENTS = '''# LightCrew and dependencies
aiohttp>=3.9.0
openai>=1.0.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
'''


def init_project(project_name: str, template: str):
    """Initialize a new LightCrew project."""
    
    # Determine project directory
    if project_name == '.':
        project_dir = Path.cwd()
        project_name = project_dir.name
    else:
        project_dir = Path.cwd() / project_name
        
    click.echo(f"Initializing LightCrew project: {project_name}")
    click.echo(f"Location: {project_dir}")
    
    # Create directory if it doesn't exist
    if not project_dir.exists():
        project_dir.mkdir(parents=True)
        click.echo(f"✓ Created directory: {project_dir}")
    
    # Create files based on template
    files_created = []
    
    # Main file
    main_content = BASIC_MAIN if template in ['basic', 'full'] else MINIMAL_MAIN
    main_file = project_dir / 'main.py'
    if not main_file.exists():
        main_file.write_text(main_content.format(project_name=project_name))
        files_created.append('main.py')
    
    # Config file (for basic and full templates)
    if template in ['basic', 'full']:
        config_file = project_dir / 'config.yaml'
        if not config_file.exists():
            config_file.write_text(BASIC_CONFIG.format(project_name=project_name))
            files_created.append('config.yaml')
    
    # .env file
    env_file = project_dir / '.env'
    if not env_file.exists():
        env_file.write_text(ENV_TEMPLATE)
        files_created.append('.env')
    
    # .gitignore
    gitignore_file = project_dir / '.gitignore'
    if not gitignore_file.exists():
        gitignore_file.write_text(GITIGNORE)
        files_created.append('.gitignore')
    
    # README
    readme_file = project_dir / 'README.md'
    if not readme_file.exists():
        readme_file.write_text(README_TEMPLATE.format(project_name=project_name))
        files_created.append('README.md')
    
    # requirements.txt
    req_file = project_dir / 'requirements.txt'
    if not req_file.exists():
        req_file.write_text(REQUIREMENTS)
        files_created.append('requirements.txt')
    
    # Make main.py executable
    if main_file.exists():
        os.chmod(main_file, 0o755)
    
    # Summary
    click.echo("\n✓ Project initialized successfully!")
    click.echo(f"\nFiles created:")
    for file in files_created:
        click.echo(f"  - {file}")
    
    click.echo(f"\nNext steps:")
    if project_name != '.':
        click.echo(f"  1. cd {project_name}")
    click.echo(f"  2. pip install -r requirements.txt")
    click.echo(f"  3. Edit .env and add your OPENAI_API_KEY")
    click.echo(f"  4. python main.py --interactive")
