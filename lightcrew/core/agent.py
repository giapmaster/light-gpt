"""
Agent implementation for LightCrew framework.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .base import BaseComponent, Observable, Configurable, AgentConfig, ExecutionResult, LLMProvider
from ..memory.memory_manager import MemoryManager
from ..tools.base_tool import BaseTool
from ..utils.logger import get_logger


logger = get_logger(__name__)


class Agent(BaseComponent, Observable, Configurable):
    """
    Lightweight AI Agent with role-based configuration.
    
    Example:
        >>> agent = Agent(role="researcher", llm="openai")
        >>> result = agent.execute("Research AI trends")
    """
    
    def __init__(
        self,
        role: str,
        goal: str = "",
        backstory: str = "",
        llm: Union[str, LLMProvider] = "openai",
        llm_model: str = "gpt-3.5-turbo",
        tools: List[Union[str, BaseTool]] = None,
        memory: Optional[MemoryManager] = None,
        config: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize an Agent.
        
        Args:
            role: The agent's role (e.g., "researcher", "writer")
            goal: The agent's goal or objective
            backstory: Background story for the agent
            llm: LLM provider (string name or LLMProvider instance)
            llm_model: Specific model to use
            tools: List of tools available to the agent
            memory: Memory manager instance
            config: Additional configuration
        """
        super().__init__(name=role, config=config)
        
        # Core attributes
        self.role = role
        self.goal = goal or f"I am a {role} agent"
        self.backstory = backstory or f"I am an AI agent specialized in {role} tasks"
        
        # LLM setup
        self.llm = self._setup_llm(llm, llm_model)
        
        # Tools setup
        self.tools = self._setup_tools(tools or [])
        
        # Memory setup
        self.memory = memory or MemoryManager()
        
        # Execution state
        self.execution_count = 0
        self.last_execution = None
        
        # Configuration
        self.max_iterations = self.get_config("max_iterations", 10)
        self.timeout = self.get_config("timeout", 300.0)
        
        logger.info(f"Agent '{self.role}' initialized with {len(self.tools)} tools")
    
    def _setup_llm(self, llm: Union[str, LLMProvider], model: str) -> LLMProvider:
        """Setup LLM provider."""
        if isinstance(llm, str):
            # Import and create provider based on string
            if llm.lower() == "openai":
                from ..utils.llm_providers import OpenAIProvider
                return OpenAIProvider(model=model)
            elif llm.lower() == "anthropic":
                from ..utils.llm_providers import AnthropicProvider
                return AnthropicProvider(model=model)
            else:
                # Default to mock provider for testing
                from ..utils.llm_providers import MockLLMProvider
                return MockLLMProvider(model=model)
        else:
            return llm
    
    def _setup_tools(self, tools: List[Union[str, BaseTool]]) -> List[BaseTool]:
        """Setup tools for the agent."""
        tool_instances = []
        for tool in tools:
            if isinstance(tool, str):
                # Load tool by name (implement tool registry later)
                logger.warning(f"Tool loading by name '{tool}' not implemented yet")
            elif isinstance(tool, BaseTool):
                tool_instances.append(tool)
        return tool_instances
    
    async def execute(self, task_description: str, context: str = "") -> ExecutionResult:
        """
        Execute a task asynchronously.
        
        Args:
            task_description: Description of the task to execute
            context: Additional context for the task
            
        Returns:
            ExecutionResult with the output
        """
        start_time = asyncio.get_event_loop().time()
        self.execution_count += 1
        
        try:
            # Notify observers
            self.notify_observers("execution_started", {
                "task": task_description,
                "agent": self.role
            })
            
            # Build prompt
            prompt = self._build_prompt(task_description, context)
            
            # Execute with LLM
            self.llm.initialize()
            output = await self.llm.generate(prompt)
            
            # Store in memory
            if self.memory:
                await self.memory.store(
                    key=f"execution_{self.execution_count}",
                    value={
                        "task": task_description,
                        "output": output,
                        "agent": self.role
                    }
                )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = ExecutionResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "agent": self.role,
                    "task": task_description,
                    "execution_count": self.execution_count
                }
            )
            
            self.last_execution = result
            
            # Notify observers
            self.notify_observers("execution_completed", result)
            
            logger.info(f"Agent '{self.role}' completed task in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = str(e)
            
            result = ExecutionResult(
                success=False,
                output=None,
                error=error_msg,
                execution_time=execution_time,
                metadata={
                    "agent": self.role,
                    "task": task_description,
                    "execution_count": self.execution_count
                }
            )
            
            # Notify observers
            self.notify_observers("execution_failed", result)
            
            logger.error(f"Agent '{self.role}' failed: {error_msg}")
            return result
    
    def execute_sync(self, task_description: str, context: str = "") -> ExecutionResult:
        """
        Execute a task synchronously.
        
        Args:
            task_description: Description of the task to execute
            context: Additional context for the task
            
        Returns:
            ExecutionResult with the output
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute(task_description, context))
    
    def _build_prompt(self, task_description: str, context: str = "") -> str:
        """Build the prompt for the LLM."""
        prompt_parts = [
            f"Role: {self.role}",
            f"Goal: {self.goal}",
            f"Backstory: {self.backstory}",
            "",
            f"Task: {task_description}"
        ]
        
        if context:
            prompt_parts.extend(["", f"Context: {context}"])
        
        if self.tools:
            tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in self.tools]
            prompt_parts.extend([
                "",
                "Available Tools:",
                *tool_descriptions
            ])
        
        prompt_parts.extend([
            "",
            "Please complete the task based on your role and the available information.",
            "Provide a clear and concise response."
        ])
        
        return "\n".join(prompt_parts)
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent."""
        self.tools.append(tool)
        logger.info(f"Added tool '{tool.name}' to agent '{self.role}'")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent."""
        self.tools = [t for t in self.tools if t.name != tool_name]
        logger.info(f"Removed tool '{tool_name}' from agent '{self.role}'")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "role": self.role,
            "execution_count": self.execution_count,
            "tools_count": len(self.tools),
            "last_execution": self.last_execution.timestamp if self.last_execution else None,
            "memory_enabled": self.memory is not None
        }
    
    def __str__(self):
        return f"Agent(role='{self.role}', tools={len(self.tools)})"
    
    def __repr__(self):
        return (f"Agent(role='{self.role}', goal='{self.goal[:50]}...', "
                f"tools={len(self.tools)}, executions={self.execution_count})")