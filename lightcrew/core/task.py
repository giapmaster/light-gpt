"""
Task implementation for LightCrew framework.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .base import BaseComponent, Observable, Configurable, TaskConfig, ExecutionResult
from .agent import Agent
from ..utils.logger import get_logger


logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Task(BaseComponent, Observable, Configurable):
    """
    Lightweight Task with execution management.
    
    Example:
        >>> task = Task("Research AI trends", agent=researcher_agent)
        >>> result = task.execute()
    """
    
    def __init__(
        self,
        description: str,
        agent: Optional[Agent] = None,
        expected_output: str = "",
        context: List[str] = None,
        tools: List[str] = None,
        async_execution: bool = False,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 180.0,
        retry_count: int = 3,
        callback: Optional[Callable] = None,
        config: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize a Task.
        
        Args:
            description: Task description
            agent: Agent to execute the task
            expected_output: Expected output format/description
            context: List of context strings
            tools: List of tool names to use
            async_execution: Whether to execute asynchronously
            priority: Task priority
            timeout: Execution timeout in seconds
            retry_count: Number of retries on failure
            callback: Callback function after completion
            config: Additional configuration
        """
        super().__init__(name=f"Task_{description[:30]}...", config=config)
        
        # Core attributes
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context = context or []
        self.tools = tools or []
        self.async_execution = async_execution
        self.priority = priority
        self.timeout = timeout
        self.retry_count = retry_count
        self.callback = callback
        
        # Execution state
        self.status = TaskStatus.PENDING
        self.result: Optional[ExecutionResult] = None
        self.attempts = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Dependencies
        self.dependencies: List['Task'] = []
        self.dependents: List['Task'] = []
        
        logger.info(f"Task created: '{self.description[:50]}...'")
    
    async def execute(self, agent: Optional[Agent] = None) -> ExecutionResult:
        """
        Execute the task asynchronously.
        
        Args:
            agent: Agent to use (overrides task's agent)
            
        Returns:
            ExecutionResult with the output
        """
        # Use provided agent or task's agent
        execution_agent = agent or self.agent
        if not execution_agent:
            raise ValueError("No agent provided for task execution")
        
        # Check dependencies
        if not await self._check_dependencies():
            raise RuntimeError("Task dependencies not satisfied")
        
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.attempts += 1
        
        try:
            # Notify observers
            self.notify_observers("task_started", {
                "task": self.description,
                "agent": execution_agent.role,
                "attempt": self.attempts
            })
            
            # Build context from dependencies and provided context
            full_context = self._build_context()
            
            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    execution_agent.execute(self.description, full_context),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise RuntimeError(f"Task execution timed out after {self.timeout}s")
            
            # Check if execution was successful
            if result.success:
                self.status = TaskStatus.COMPLETED
                self.completed_at = datetime.now()
                self.result = result
                
                # Execute callback if provided
                if self.callback:
                    try:
                        if asyncio.iscoroutinefunction(self.callback):
                            await self.callback(result)
                        else:
                            self.callback(result)
                    except Exception as e:
                        logger.warning(f"Task callback failed: {e}")
                
                # Notify observers
                self.notify_observers("task_completed", result)
                
                logger.info(f"Task completed: '{self.description[:50]}...'")
                return result
            else:
                # Handle failure with retry
                return await self._handle_failure(result.error, execution_agent)
                
        except Exception as e:
            return await self._handle_failure(str(e), execution_agent)
    
    def execute_sync(self, agent: Optional[Agent] = None) -> ExecutionResult:
        """
        Execute the task synchronously.
        
        Args:
            agent: Agent to use (overrides task's agent)
            
        Returns:
            ExecutionResult with the output
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute(agent))
    
    async def _handle_failure(self, error: str, agent: Agent) -> ExecutionResult:
        """Handle task execution failure."""
        if self.attempts < self.retry_count:
            logger.warning(f"Task failed (attempt {self.attempts}/{self.retry_count}): {error}")
            # Retry after a short delay
            await asyncio.sleep(1.0 * self.attempts)  # Exponential backoff
            return await self.execute(agent)
        else:
            # Max retries reached
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now()
            
            result = ExecutionResult(
                success=False,
                output=None,
                error=f"Task failed after {self.attempts} attempts: {error}",
                metadata={
                    "task": self.description,
                    "agent": agent.role,
                    "attempts": self.attempts
                }
            )
            
            self.result = result
            
            # Notify observers
            self.notify_observers("task_failed", result)
            
            logger.error(f"Task failed permanently: '{self.description[:50]}...' - {error}")
            return result
    
    async def _check_dependencies(self) -> bool:
        """Check if all dependencies are satisfied."""
        for dep in self.dependencies:
            if dep.status != TaskStatus.COMPLETED:
                logger.warning(f"Dependency not satisfied: {dep.description[:50]}...")
                return False
        return True
    
    def _build_context(self) -> str:
        """Build context from dependencies and provided context."""
        context_parts = []
        
        # Add provided context
        if self.context:
            context_parts.extend(self.context)
        
        # Add outputs from completed dependencies
        for dep in self.dependencies:
            if dep.status == TaskStatus.COMPLETED and dep.result:
                context_parts.append(f"From {dep.description[:30]}...: {dep.result.output}")
        
        return "\n".join(context_parts)
    
    def add_dependency(self, task: 'Task'):
        """Add a dependency task."""
        if task not in self.dependencies:
            self.dependencies.append(task)
            task.dependents.append(self)
            logger.info(f"Added dependency: {task.description[:30]}...")
    
    def remove_dependency(self, task: 'Task'):
        """Remove a dependency task."""
        if task in self.dependencies:
            self.dependencies.remove(task)
            task.dependents.remove(self)
            logger.info(f"Removed dependency: {task.description[:30]}...")
    
    def cancel(self):
        """Cancel the task."""
        if self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            self.status = TaskStatus.CANCELLED
            self.completed_at = datetime.now()
            
            # Notify observers
            self.notify_observers("task_cancelled", {"task": self.description})
            
            logger.info(f"Task cancelled: '{self.description[:50]}...'")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        return {
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "attempts": self.attempts,
            "dependencies": len(self.dependencies),
            "dependents": len(self.dependents),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at else None
            )
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to execute (dependencies satisfied)."""
        return all(dep.status == TaskStatus.COMPLETED for dep in self.dependencies)
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def __str__(self):
        return f"Task('{self.description[:50]}...', status={self.status.value})"
    
    def __repr__(self):
        return (f"Task(description='{self.description[:30]}...', "
                f"status={self.status.value}, agent={self.agent.role if self.agent else None})")