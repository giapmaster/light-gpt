# LightCrew - Lightweight AI Agent Framework

## Overview
LightCrew is a lightweight AI agent framework designed to facilitate the development and deployment of intelligent agents. It streamlines the integration of large language models (LLMs) into applications with a modular architecture that supports asynchronous execution and pluggable memory backends.

**Current Version:** 0.1.0  
**Status:** Development Environment Set Up  
**Last Updated:** November 6, 2025

## Project Architecture

### Core Components
- **Agent**: Manages roles and integrates with LLMs
- **Task**: Handles asynchronous execution with validation
- **Crew**: Orchestrates tasks either sequentially or in parallel
- **Memory**: Supports pluggable backends (in-memory storage, Redis)
- **Tools**: Provides a registry system with security validation

### Technology Stack
- **Language**: Python 3.11
- **Async Framework**: asyncio, aiohttp
- **LLM Integration**: OpenAI (extensible to other providers)
- **Configuration**: YAML, python-dotenv
- **Package Manager**: pip

## Project Structure
```
lightcrew/
├── lightcrew/          # Core framework
│   ├── cli/           # Command-line interface
│   │   ├── commands/  # CLI command implementations
│   │   └── main.py    # CLI entry point
│   ├── core/          # Core components (Agent, Task, Crew)
│   ├── memory/        # Memory management
│   ├── tools/         # Tool registry and base classes
│   ├── config/        # Configuration settings
│   └── utils/         # Utilities and LLM providers
├── examples/          # Example applications
│   ├── openai_minimal/       # Simple OpenAI integration demo
│   ├── content_generator/    # Multi-agent content generation
│   └── research_assistant/   # Research and report generation
├── setup.py           # Package installation configuration
├── requirements.txt   # Core dependencies
└── replit.md         # This file
```

## Setup & Configuration

### Dependencies
The core dependencies are:
- `aiohttp>=3.9.0` - Async HTTP client
- `openai>=1.0.0` - OpenAI API integration
- `pyyaml>=6.0.1` - YAML configuration support
- `python-dotenv>=1.0.0` - Environment variable management
- `click>=8.1.7` - CLI framework

All dependencies are installed via `requirements.txt`.

### Installation
LightCrew is installed as an editable package with CLI support:
```bash
pip install -e .
```

This makes the `lightcrew` command available globally.

### Environment Variables
- `OPENAI_API_KEY` - Required for OpenAI integration (set via Replit Secrets)

## Running the Project

### LightCrew CLI
The framework now includes a comprehensive CLI tool for managing projects and running crews.

**View all commands:**
```bash
lightcrew --help
```

**Initialize a new project:**
```bash
lightcrew init my_project --template basic
cd my_project
pip install -r requirements.txt
```

**Run examples:**
```bash
lightcrew examples list
lightcrew examples run openai_minimal --interactive
```

**Create components:**
```bash
lightcrew create agent ResearchAgent --role Researcher
lightcrew create tool search_tool
lightcrew create crew my_crew --agents agent1 agent2
```

**Run crews from config:**
```bash
lightcrew run config.yaml --interactive
lightcrew run config.yaml --query "Your question"
```

**Manage configuration:**
```bash
lightcrew config --list
lightcrew config --set OPENAI_API_KEY sk-...
```

### Current Workflow
The default workflow runs the OpenAI minimal example in interactive mode:
```bash
python3 examples/openai_minimal/main.py --interactive
```

### Available Examples

#### 1. OpenAI Minimal Demo
A simple single-agent example that uses OpenAI to answer questions.

**Interactive Mode:**
```bash
python3 examples/openai_minimal/main.py --interactive
```

**Single Query Mode:**
```bash
python3 examples/openai_minimal/main.py --query "What is AI?" --model gpt-4o-mini
```

#### 2. Content Generator
Multi-agent system (Researcher → Writer → Editor) for generating quality content.

**Requirements:**
```bash
pip install -r examples/content_generator/requirements.txt
```

**Usage:**
```bash
python3 examples/content_generator/main.py --interactive
```

#### 3. Research Assistant
Automated research and comprehensive report generation.

**Requirements:**
```bash
pip install -r examples/research_assistant/requirements.txt
```

**Usage:**
```bash
python3 examples/research_assistant/main.py --interactive
```

## Development Guide

### Using the Framework
```python
from lightcrew import Agent, Task, Crew

# Create an agent
agent = Agent(
    role="researcher",
    goal="Find information",
    llm="openai",
    llm_model="gpt-4o-mini"
)

# Create a task
task = Task(
    description="Research AI trends",
    agent=agent,
    expected_output="A summary of AI trends"
)

# Create and execute crew
crew = Crew(agents=[agent], tasks=[task])
result = await crew.execute()
```

### Adding New Tools
```python
from lightcrew.tools import tool

@tool(name="my_tool", description="My custom tool")
def my_tool(param: str) -> dict:
    """Tool implementation"""
    return {"result": f"Processed: {param}"}
```

## Replit Environment Notes

### File Management
- Core framework code is in `lightcrew/`
- Example applications are in `examples/`
- `.gitignore` is configured for Python projects
- No virtual environment needed (Replit handles this)

### API Keys
To use the OpenAI examples:
1. Get an OpenAI API key from https://platform.openai.com
2. Add it to Replit Secrets as `OPENAI_API_KEY`
3. The framework will automatically use it from environment variables

### Logs
The application uses structured logging. Check the console output for:
- Initialization messages
- Agent execution status
- Error messages and warnings

## Recent Changes
- **Nov 6, 2025**: CLI Implementation
  - Built comprehensive CLI tool using Click framework
  - Added `lightcrew init` command for project scaffolding
  - Added `lightcrew run` command for executing crews from config
  - Added `lightcrew create` commands for generating agents, tools, and crews
  - Added `lightcrew examples` command for managing examples
  - Added `lightcrew config` command for configuration management
  - Created setup.py for package installation
  - All CLI commands tested and working

- **Nov 6, 2025**: Initial Replit environment setup
  - Installed Python 3.11
  - Created requirements.txt with core dependencies
  - Set up .gitignore for Python
  - Configured workflow for openai_minimal example
  - Verified all imports and examples work correctly

## User Preferences
None specified yet.

## Known Issues
- LSP diagnostics show some type hints issues in the codebase (non-blocking)
- API server mentioned in content_generator README doesn't exist (documentation only)

## Future Enhancements
- Add support for additional LLM providers (Anthropic, local models)
- Implement Redis backend for memory management
- Create web-based demo interface
- Add comprehensive test suite
- Publish package to PyPI
- Add CLI tests and integration tests
- Enhance CLI with progress bars and better formatting
