"""
Base classes and interfaces for LightCrew framework.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import asyncio
import time
from datetime import datetime


class ExecutionMode(Enum):
    """Task execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ASYNC = "async"


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.config = kwargs
        self._initialized = False
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous generation method."""
        pass
    
    def initialize(self):
        """Initialize the LLM provider."""
        if not self._initialized:
            self._setup()
            self._initialized = True
    
    def _setup(self):
        """Setup method to be overridden by implementations."""
        pass


@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentConfig:
    """Configuration for an Agent."""
    role: str
    goal: str = ""
    backstory: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    max_iterations: int = 10
    timeout: float = 300.0  # 5 minutes
    tools: List[str] = None
    memory_enabled: bool = True
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


@dataclass
class TaskConfig:
    """Configuration for a Task."""
    description: str
    expected_output: str = ""
    context: List[str] = None
    async_execution: bool = False
    timeout: float = 180.0  # 3 minutes
    retry_count: int = 3
    tools: List[str] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = []
        if self.tools is None:
            self.tools = []


class BaseComponent:
    """Base class for all LightCrew components.

    Note: Accepts *args and **kwargs and calls super().__init__ to
    cooperate with multiple inheritance (e.g., with Configurable/Observable).
    """
    
    def __init__(self, name: str = None, *args, **kwargs):
        # Cooperate with MRO so mixins like Configurable can receive their kwargs
        super().__init__(*args, **kwargs)
        self.name = name or self.__class__.__name__
        self.id = f"{self.name}_{int(time.time())}"
        self.created_at = datetime.now()
        self.metadata = {}
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', id='{self.id}')"


class Observable:
    """Mixin for components that can be observed."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._observers = []
    
    def add_observer(self, observer):
        """Add an observer to this component."""
        self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove an observer from this component."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, event: str, data: Any = None):
        """Notify all observers of an event."""
        for observer in self._observers:
            if hasattr(observer, 'on_event'):
                observer.on_event(event, data)


class Configurable:
    """Mixin for components that can be configured."""
    
    def __init__(self, config: Dict[str, Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config or {}
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set a configuration value."""
        self.config[key] = value
    
    def update_config(self, config: Dict[str, Any]):
        """Update configuration with new values."""
        self.config.update(config)


# Utility functions
def ensure_async(func):
    """Decorator to ensure a function is async."""
    if asyncio.iscoroutinefunction(func):
        return func
    else:
        async def async_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return async_wrapper


def measure_time(func):
    """Decorator to measure execution time."""
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
