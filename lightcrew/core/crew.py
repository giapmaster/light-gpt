"""
Crew orchestration implementation for LightCrew framework.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .base import BaseComponent, Observable, Configurable, ExecutionMode, ExecutionResult
from .agent import Agent
from .task import Task, TaskStatus, TaskPriority
from ..memory.memory_manager import MemoryManager
from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class CrewResult:
    """Result of crew execution."""
    success: bool
    results: List[ExecutionResult]
    execution_time: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    metadata: Dict[str, Any]


class Crew(BaseComponent, Observable, Configurable):
    """
    Lightweight Crew orchestrator for managing agents and tasks.
    
    Example:
        >>> crew = Crew([agent1, agent2], [task1, task2])
        >>> result = crew.execute()
    """
    
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        memory: Optional[MemoryManager] = None,
        max_concurrent_tasks: int = 5,
        task_timeout: float = 300.0,
        config: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize a Crew.
        
        Args:
            agents: List of agents in the crew
            tasks: List of tasks to execute
            execution_mode: How to execute tasks (sequential/parallel/async)
            memory: Shared memory manager
            max_concurrent_tasks: Maximum concurrent tasks in parallel mode
            task_timeout: Default timeout for tasks
            config: Additional configuration
        """
        super().__init__(name="Crew", config=config)
        
        # Core attributes
        self.agents = agents
        self.tasks = tasks
        self.execution_mode = execution_mode
        self.memory = memory or MemoryManager()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout = task_timeout
        
        # Execution state
        self.is_running = False
        self.current_task_index = 0
        self.completed_tasks = []
        self.failed_tasks = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Task assignment
        self._assign_agents_to_tasks()
        
        # Validation
        self._validate_setup()
        
        logger.info(f"Crew initialized with {len(self.agents)} agents and {len(self.tasks)} tasks")
    
    def _assign_agents_to_tasks(self):
        """Assign agents to tasks that don't have agents."""
        agent_index = 0
        for task in self.tasks:
            if not task.agent and self.agents:
                task.agent = self.agents[agent_index % len(self.agents)]
                agent_index += 1
                logger.info(f"Assigned agent '{task.agent.role}' to task '{task.description[:30]}...'")
    
    def _validate_setup(self):
        """Validate crew setup."""
        if not self.agents:
            raise ValueError("Crew must have at least one agent")
        
        if not self.tasks:
            raise ValueError("Crew must have at least one task")
        
        # Check that all tasks have agents
        for task in self.tasks:
            if not task.agent:
                raise ValueError(f"Task '{task.description[:30]}...' has no assigned agent")
        
        # Check for circular dependencies
        self._check_circular_dependencies()
    
    def _check_circular_dependencies(self):
        """Check for circular dependencies in tasks."""
        def has_cycle(task, visited, rec_stack):
            visited.add(task)
            rec_stack.add(task)
            
            for dep in task.dependencies:
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(task)
            return False
        
        visited = set()
        for task in self.tasks:
            if task not in visited:
                if has_cycle(task, visited, set()):
                    raise ValueError("Circular dependency detected in tasks")
    
    async def execute(self, inputs: Dict[str, Any] = None) -> CrewResult:
        """
        Execute all tasks according to the execution mode.
        
        Args:
            inputs: Input data for the crew execution
            
        Returns:
            CrewResult with execution summary
        """
        if self.is_running:
            raise RuntimeError("Crew is already running")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            # Notify observers
            self.notify_observers("crew_started", {
                "agents": len(self.agents),
                "tasks": len(self.tasks),
                "mode": self.execution_mode.value
            })
            
            # Store inputs in memory
            if inputs and self.memory:
                await self.memory.store("crew_inputs", inputs)
            
            # Execute based on mode
            if self.execution_mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential()
            elif self.execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel()
            elif self.execution_mode == ExecutionMode.ASYNC:
                results = await self._execute_async()
            else:
                raise ValueError(f"Unsupported execution mode: {self.execution_mode}")
            
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            # Create result summary
            crew_result = CrewResult(
                success=all(r.success for r in results),
                results=results,
                execution_time=execution_time,
                total_tasks=len(self.tasks),
                completed_tasks=len([r for r in results if r.success]),
                failed_tasks=len([r for r in results if not r.success]),
                metadata={
                    "execution_mode": self.execution_mode.value,
                    "agents": [agent.role for agent in self.agents],
                    "start_time": self.start_time,
                    "end_time": self.end_time
                }
            )
            
            # Notify observers
            self.notify_observers("crew_completed", crew_result)
            
            logger.info(f"Crew execution completed in {execution_time:.2f}s "
                       f"({crew_result.completed_tasks}/{crew_result.total_tasks} tasks successful)")
            
            return crew_result
            
        except Exception as e:
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            error_result = CrewResult(
                success=False,
                results=[],
                execution_time=execution_time,
                total_tasks=len(self.tasks),
                completed_tasks=0,
                failed_tasks=len(self.tasks),
                metadata={"error": str(e)}
            )
            
            # Notify observers
            self.notify_observers("crew_failed", {"error": str(e)})
            
            logger.error(f"Crew execution failed: {e}")
            raise
        
        finally:
            self.is_running = False
    
    def execute_sync(self, inputs: Dict[str, Any] = None) -> CrewResult:
        """
        Execute crew synchronously.
        
        Args:
            inputs: Input data for the crew execution
            
        Returns:
            CrewResult with execution summary
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute(inputs))
    
    async def _execute_sequential(self) -> List[ExecutionResult]:
        """Execute tasks sequentially."""
        results = []
        
        # Sort tasks by priority and dependencies
        sorted_tasks = self._topological_sort()
        
        for task in sorted_tasks:
            logger.info(f"Executing task: '{task.description[:50]}...'")
            
            try:
                result = await task.execute()
                results.append(result)
                
                if result.success:
                    self.completed_tasks.append(task)
                else:
                    self.failed_tasks.append(task)
                    # In sequential mode, stop on first failure
                    logger.error(f"Task failed, stopping sequential execution: {result.error}")
                    break
                    
            except Exception as e:
                error_result = ExecutionResult(
                    success=False,
                    output=None,
                    error=str(e),
                    metadata={"task": task.description}
                )
                results.append(error_result)
                self.failed_tasks.append(task)
                logger.error(f"Task execution error: {e}")
                break
        
        return results
    
    async def _execute_parallel(self) -> List[ExecutionResult]:
        """Execute tasks in parallel with dependency management."""
        results = []
        remaining_tasks = set(self.tasks)
        running_tasks = {}
        
        while remaining_tasks or running_tasks:
            # Find ready tasks (dependencies satisfied)
            ready_tasks = [
                task for task in remaining_tasks 
                if task.is_ready and len(running_tasks) < self.max_concurrent_tasks
            ]
            
            # Start ready tasks
            for task in ready_tasks:
                logger.info(f"Starting parallel task: '{task.description[:50]}...'")
                future = asyncio.create_task(task.execute())
                running_tasks[future] = task
                remaining_tasks.remove(task)
            
            # Wait for at least one task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.keys(), 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for future in done:
                    task = running_tasks.pop(future)
                    try:
                        result = await future
                        results.append(result)
                        
                        if result.success:
                            self.completed_tasks.append(task)
                        else:
                            self.failed_tasks.append(task)
                            
                    except Exception as e:
                        error_result = ExecutionResult(
                            success=False,
                            output=None,
                            error=str(e),
                            metadata={"task": task.description}
                        )
                        results.append(error_result)
                        self.failed_tasks.append(task)
            
            # If no tasks are ready and none are running, we might have unresolvable dependencies
            if not ready_tasks and not running_tasks and remaining_tasks:
                logger.error("Deadlock detected: remaining tasks have unresolvable dependencies")
                break
        
        return results
    
    async def _execute_async(self) -> List[ExecutionResult]:
        """Execute all tasks asynchronously (fire and forget)."""
        # Create all task futures
        futures = [asyncio.create_task(task.execute()) for task in self.tasks]
        
        # Wait for all to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ExecutionResult(
                    success=False,
                    output=None,
                    error=str(result),
                    metadata={"task": self.tasks[i].description}
                )
                processed_results.append(error_result)
                self.failed_tasks.append(self.tasks[i])
            else:
                processed_results.append(result)
                if result.success:
                    self.completed_tasks.append(self.tasks[i])
                else:
                    self.failed_tasks.append(self.tasks[i])
        
        return processed_results
    
    def _topological_sort(self) -> List[Task]:
        """Sort tasks topologically based on dependencies."""
        # Kahn's algorithm
        in_degree = {task: len(task.dependencies) for task in self.tasks}
        queue = [task for task in self.tasks if in_degree[task] == 0]
        result = []
        
        while queue:
            # Sort by priority
            queue.sort(key=lambda t: t.priority.value, reverse=True)
            task = queue.pop(0)
            result.append(task)
            
            # Update in-degrees
            for dependent in task.dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.tasks):
            raise ValueError("Circular dependency detected in tasks")
        
        return result
    
    def add_agent(self, agent: Agent):
        """Add an agent to the crew."""
        self.agents.append(agent)
        logger.info(f"Added agent '{agent.role}' to crew")
    
    def add_task(self, task: Task):
        """Add a task to the crew."""
        self.tasks.append(task)
        # Assign agent if task doesn't have one
        if not task.agent and self.agents:
            task.agent = self.agents[0]  # Assign to first agent
        logger.info(f"Added task '{task.description[:30]}...' to crew")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get crew statistics."""
        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "execution_mode": self.execution_mode.value,
            "is_running": self.is_running,
            "execution_time": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else None
            )
        }
    
    def __str__(self):
        return f"Crew(agents={len(self.agents)}, tasks={len(self.tasks)}, mode={self.execution_mode.value})"
    
    def __repr__(self):
        return (f"Crew(agents={len(self.agents)}, tasks={len(self.tasks)}, "
                f"mode={self.execution_mode.value}, running={self.is_running})")