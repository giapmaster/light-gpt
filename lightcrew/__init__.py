"""
LightCrew - Lightweight AI Agent Framework

A minimal yet powerful framework for building AI agent systems with enterprise scalability.
Based on CrewAI analysis but optimized for performance and simplicity.
"""

__version__ = "0.1.0"
__author__ = "LightCrew Team"

# Core imports for easy access
from .core.agent import Agent
from .core.task import Task
from .core.crew import Crew
from .core.base import LLMProvider, ExecutionMode
from .memory.memory_manager import MemoryManager
from .tools.base_tool import BaseTool, tool
from .config.settings import Settings

# Main exports
__all__ = [
    "Agent",
    "Task", 
    "Crew",
    "LLMProvider",
    "ExecutionMode",
    "MemoryManager",
    "BaseTool",
    "tool",
    "Settings"
]

# Version info
def get_version():
    """Get the current version of LightCrew."""
    return __version__

# Quick setup function
def quick_start():
    """
    Quick start guide for LightCrew framework.
    
    Example:
        >>> from lightcrew import Agent, Task, Crew
        >>> agent = Agent(role="researcher", llm="openai")
        >>> task = Task("Research AI trends", agent=agent)
        >>> crew = Crew([agent], [task])
        >>> result = crew.execute()
    """
    print(f"LightCrew v{__version__} - Lightweight AI Agent Framework")
    print("Quick Start:")
    print("1. from lightcrew import Agent, Task, Crew")
    print("2. agent = Agent(role='researcher', llm='openai')")
    print("3. task = Task('Your task description', agent=agent)")
    print("4. crew = Crew([agent], [task])")
    print("5. result = crew.execute()")
    print("\nFor more examples, see: examples/")
