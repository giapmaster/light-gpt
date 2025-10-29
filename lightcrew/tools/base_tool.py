"""
Base tool implementation for LightCrew framework.
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass
from datetime import datetime

from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """
    Abstract base class for all tools in LightCrew.
    
    Tools extend agent capabilities by providing specific functionalities
    like web search, calculations, file operations, etc.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize a tool.
        
        Args:
            name: Tool name (must be unique)
            description: Tool description for LLM understanding
            parameters: Tool parameter schema
            **kwargs: Additional tool configuration
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.config = kwargs
        
        # Execution statistics
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.last_execution: Optional[datetime] = None
        
        logger.info(f"Tool '{self.name}' initialized")
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    def execute_sync(self, **kwargs) -> ToolResult:
        """
        Execute the tool synchronously.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with execution outcome
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute(**kwargs))
    
    async def _execute_with_stats(self, **kwargs) -> ToolResult:
        """Execute tool and update statistics."""
        start_time = asyncio.get_event_loop().time()
        self.execution_count += 1
        self.last_execution = datetime.now()
        
        try:
            result = await self.execute(**kwargs)
            
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            execution_time = asyncio.get_event_loop().time() - start_time
            self.total_execution_time += execution_time
            result.execution_time = execution_time
            
            logger.debug(f"Tool '{self.name}' executed in {execution_time:.3f}s")
            return result
            
        except Exception as e:
            self.failure_count += 1
            execution_time = asyncio.get_event_loop().time() - start_time
            self.total_execution_time += execution_time
            
            error_result = ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"tool": self.name}
            )
            
            logger.error(f"Tool '{self.name}' failed: {e}")
            return error_result
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate tool parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        required_params = self.parameters.get("required", [])
        
        for param in required_params:
            if param not in kwargs:
                logger.error(f"Missing required parameter '{param}' for tool '{self.name}'")
                return False
        
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0 else 0
        )
        
        success_rate = (
            self.success_count / self.execution_count
            if self.execution_count > 0 else 0
        )
        
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": avg_execution_time,
            "last_execution": self.last_execution
        }
    
    def reset_stats(self):
        """Reset tool statistics."""
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.last_execution = None
        logger.info(f"Reset statistics for tool '{self.name}'")
    
    def __str__(self):
        return f"Tool(name='{self.name}')"
    
    def __repr__(self):
        return f"Tool(name='{self.name}', executions={self.execution_count})"


class FunctionTool(BaseTool):
    """Tool that wraps a function."""
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Initialize a function tool.
        
        Args:
            name: Tool name
            description: Tool description
            func: Function to wrap
            parameters: Parameter schema
            **kwargs: Additional configuration
        """
        super().__init__(name, description, parameters, **kwargs)
        self.func = func
        
        # Auto-generate parameters from function signature if not provided
        if not self.parameters:
            self.parameters = self._generate_parameters_from_function()
    
    def _generate_parameters_from_function(self) -> Dict[str, Any]:
        """Generate parameter schema from function signature."""
        sig = inspect.signature(self.func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == "self":
                continue
            
            param_info = {"type": "string"}  # Default type
            
            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            # Add description from docstring if available
            if self.func.__doc__:
                # Simple docstring parsing - could be improved
                param_info["description"] = f"Parameter {param_name}"
            
            parameters["properties"][param_name] = param_info
            
            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        return parameters
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the wrapped function."""
        try:
            # Validate parameters
            if not self.validate_parameters(**kwargs):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Parameter validation failed"
                )
            
            # Execute function
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            return ToolResult(
                success=True,
                output=result,
                metadata={"tool": self.name, "function": self.func.__name__}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                metadata={"tool": self.name, "function": self.func.__name__}
            )


# Decorator for creating tools from functions
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Decorator to create a tool from a function.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        parameters: Parameter schema (auto-generated if not provided)
    
    Example:
        @tool(name="calculator", description="Perform basic calculations")
        def calculate(expression: str) -> float:
            \"\"\"Calculate the result of a mathematical expression.\"\"\"
            return eval(expression)
    """
    def decorator(func: Callable) -> FunctionTool:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        return FunctionTool(
            name=tool_name,
            description=tool_description,
            func=func,
            parameters=parameters
        )
    
    return decorator


# Built-in tools
@tool(name="echo", description="Echo the input text")
def echo_tool(text: str) -> str:
    """Echo the input text back."""
    return text


@tool(name="calculator", description="Perform basic mathematical calculations")
def calculator_tool(expression: str) -> float:
    """
    Calculate the result of a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation - only allow basic math operations
        allowed_names = {
            k: v for k, v in __builtins__.items()
            if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
        }
        allowed_names.update({
            'pi': 3.141592653589793,
            'e': 2.718281828459045
        })
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid mathematical expression: {e}")


@tool(name="text_length", description="Get the length of text")
def text_length_tool(text: str) -> int:
    """
    Get the length of the provided text.
    
    Args:
        text: Text to measure
        
    Returns:
        Length of the text
    """
    return len(text)