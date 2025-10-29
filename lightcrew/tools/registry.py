"""
Tool registry for managing and discovering tools.
"""

from typing import Dict, List, Optional, Type, Any
from .base_tool import BaseTool
from ..utils.logger import get_logger


logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing tools in LightCrew.
    
    Provides tool discovery, registration, and instantiation capabilities.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        
        # Register built-in tools
        self._register_builtin_tools()
        
        logger.info("Tool registry initialized")
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        from .base_tool import echo_tool, calculator_tool, text_length_tool
        
        builtin_tools = [echo_tool, calculator_tool, text_length_tool]
        
        for tool in builtin_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool):
        """
        Register a tool instance.
        
        Args:
            tool: Tool instance to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overriding")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_tool_class(self, name: str, tool_class: Type[BaseTool]):
        """
        Register a tool class for lazy instantiation.
        
        Args:
            name: Tool name
            tool_class: Tool class to register
        """
        if name in self._tool_classes:
            logger.warning(f"Tool class '{name}' already registered, overriding")
        
        self._tool_classes[name] = tool_class
        logger.info(f"Registered tool class: {name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        # Try to get existing instance
        if name in self._tools:
            return self._tools[name]
        
        # Try to instantiate from class
        if name in self._tool_classes:
            try:
                tool_class = self._tool_classes[name]
                tool_instance = tool_class()
                self._tools[name] = tool_instance
                logger.info(f"Instantiated tool from class: {name}")
                return tool_instance
            except Exception as e:
                logger.error(f"Failed to instantiate tool '{name}': {e}")
                return None
        
        logger.warning(f"Tool '{name}' not found in registry")
        return None
    
    def list_tools(self) -> List[str]:
        """
        List all available tool names.
        
        Returns:
            List of tool names
        """
        all_tools = set(self._tools.keys()) | set(self._tool_classes.keys())
        return sorted(list(all_tools))
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool information dictionary or None if not found
        """
        tool = self.get_tool(name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "schema": tool.get_schema(),
            "stats": tool.get_stats()
        }
    
    def search_tools(self, query: str) -> List[str]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        matches = []
        
        for tool_name in self.list_tools():
            tool = self.get_tool(tool_name)
            if tool:
                # Search in name and description
                if (query_lower in tool.name.lower() or 
                    query_lower in tool.description.lower()):
                    matches.append(tool_name)
        
        return matches
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        removed = False
        
        if name in self._tools:
            del self._tools[name]
            removed = True
        
        if name in self._tool_classes:
            del self._tool_classes[name]
            removed = True
        
        if removed:
            logger.info(f"Unregistered tool: {name}")
        else:
            logger.warning(f"Tool '{name}' not found for unregistration")
        
        return removed
    
    def clear(self):
        """Clear all registered tools."""
        self._tools.clear()
        self._tool_classes.clear()
        logger.info("Cleared all tools from registry")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self.list_tools()),
            "instantiated_tools": len(self._tools),
            "tool_classes": len(self._tool_classes),
            "tools": self.list_tools()
        }
    
    def __len__(self):
        """Get number of available tools."""
        return len(self.list_tools())
    
    def __contains__(self, name: str):
        """Check if a tool is registered."""
        return name in self._tools or name in self._tool_classes
    
    def __iter__(self):
        """Iterate over tool names."""
        return iter(self.list_tools())


# Global registry instance
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(tool: BaseTool):
    """Register a tool in the global registry."""
    _global_registry.register_tool(tool)


def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool from the global registry."""
    return _global_registry.get_tool(name)


def list_tools() -> List[str]:
    """List all tools in the global registry."""
    return _global_registry.list_tools()