"""
Settings and configuration for LightCrew framework.
"""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config, set_config, load_config


@dataclass
class LLMSettings:
    """LLM configuration settings."""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    timeout: float = 30.0
    max_tokens: int = 1000
    temperature: float = 0.7
    
    def __post_init__(self):
        # Auto-load API key from environment if not provided
        if not self.api_key:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")


@dataclass
class MemorySettings:
    """Memory configuration settings."""
    backend: str = "in_memory"  # in_memory, redis, file
    default_ttl: Optional[float] = None
    auto_cleanup: bool = True
    cleanup_interval: float = 300.0
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # File settings
    file_path: str = "lightcrew_memory.json"


@dataclass
class ExecutionSettings:
    """Execution configuration settings."""
    mode: str = "sequential"  # sequential, parallel, async
    max_concurrent_tasks: int = 5
    task_timeout: float = 180.0
    agent_timeout: float = 300.0
    max_retries: int = 3


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    use_colors: bool = True
    log_file: Optional[str] = None
    format_string: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


@dataclass
class ToolSettings:
    """Tool configuration settings."""
    auto_register: bool = True
    builtin_tools: list = field(default_factory=lambda: ["echo", "calculator", "text_length"])
    tool_timeout: float = 30.0


class Settings:
    """
    Main settings class for LightCrew framework.
    
    Provides centralized configuration management with support for
    environment variables, config files, and programmatic updates.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings.
        
        Args:
            config_file: Path to configuration file
        """
        # Load configuration
        if config_file:
            load_config(config_file)
        
        # Initialize settings from config
        self.llm = LLMSettings(
            provider=get_config("llm.provider", "openai"),
            model=get_config("llm.model", "gpt-3.5-turbo"),
            api_key=get_config("llm.api_key"),
            timeout=get_config("llm.timeout", 30.0),
            max_tokens=get_config("llm.max_tokens", 1000),
            temperature=get_config("llm.temperature", 0.7)
        )
        
        self.memory = MemorySettings(
            backend=get_config("memory.backend", "in_memory"),
            default_ttl=get_config("memory.default_ttl"),
            auto_cleanup=get_config("memory.auto_cleanup", True),
            cleanup_interval=get_config("memory.cleanup_interval", 300.0),
            redis_host=get_config("memory.redis_host", "localhost"),
            redis_port=get_config("memory.redis_port", 6379),
            redis_db=get_config("memory.redis_db", 0),
            redis_password=get_config("memory.redis_password"),
            file_path=get_config("memory.file_path", "lightcrew_memory.json")
        )
        
        self.execution = ExecutionSettings(
            mode=get_config("execution.mode", "sequential"),
            max_concurrent_tasks=get_config("execution.max_concurrent_tasks", 5),
            task_timeout=get_config("execution.task_timeout", 180.0),
            agent_timeout=get_config("execution.agent_timeout", 300.0),
            max_retries=get_config("execution.max_retries", 3)
        )
        
        self.logging = LoggingSettings(
            level=get_config("logging.level", "INFO"),
            use_colors=get_config("logging.use_colors", True),
            log_file=get_config("logging.log_file"),
            format_string=get_config("logging.format_string", 
                                   "%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        )
        
        self.tools = ToolSettings(
            auto_register=get_config("tools.auto_register", True),
            builtin_tools=get_config("tools.builtin_tools", ["echo", "calculator", "text_length"]),
            tool_timeout=get_config("tools.tool_timeout", 30.0)
        )
        
        # Framework info
        self.framework = {
            "name": get_config("framework.name", "lightcrew"),
            "version": get_config("framework.version", "0.1.0"),
            "mode": get_config("framework.mode", "lightweight")
        }
    
    def update_llm_settings(self, **kwargs):
        """Update LLM settings."""
        for key, value in kwargs.items():
            if hasattr(self.llm, key):
                setattr(self.llm, key, value)
                set_config(f"llm.{key}", value)
    
    def update_memory_settings(self, **kwargs):
        """Update memory settings."""
        for key, value in kwargs.items():
            if hasattr(self.memory, key):
                setattr(self.memory, key, value)
                set_config(f"memory.{key}", value)
    
    def update_execution_settings(self, **kwargs):
        """Update execution settings."""
        for key, value in kwargs.items():
            if hasattr(self.execution, key):
                setattr(self.execution, key, value)
                set_config(f"execution.{key}", value)
    
    def update_logging_settings(self, **kwargs):
        """Update logging settings."""
        for key, value in kwargs.items():
            if hasattr(self.logging, key):
                setattr(self.logging, key, value)
                set_config(f"logging.{key}", value)
    
    def update_tool_settings(self, **kwargs):
        """Update tool settings."""
        for key, value in kwargs.items():
            if hasattr(self.tools, key):
                setattr(self.tools, key, value)
                set_config(f"tools.{key}", value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "framework": self.framework,
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "timeout": self.llm.timeout,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature
                # Note: API key not included for security
            },
            "memory": {
                "backend": self.memory.backend,
                "default_ttl": self.memory.default_ttl,
                "auto_cleanup": self.memory.auto_cleanup,
                "cleanup_interval": self.memory.cleanup_interval,
                "redis_host": self.memory.redis_host,
                "redis_port": self.memory.redis_port,
                "redis_db": self.memory.redis_db,
                "file_path": self.memory.file_path
                # Note: Redis password not included for security
            },
            "execution": {
                "mode": self.execution.mode,
                "max_concurrent_tasks": self.execution.max_concurrent_tasks,
                "task_timeout": self.execution.task_timeout,
                "agent_timeout": self.execution.agent_timeout,
                "max_retries": self.execution.max_retries
            },
            "logging": {
                "level": self.logging.level,
                "use_colors": self.logging.use_colors,
                "log_file": self.logging.log_file,
                "format_string": self.logging.format_string
            },
            "tools": {
                "auto_register": self.tools.auto_register,
                "builtin_tools": self.tools.builtin_tools,
                "tool_timeout": self.tools.tool_timeout
            }
        }
    
    def __str__(self):
        return f"Settings(framework={self.framework['name']} v{self.framework['version']})"
    
    def __repr__(self):
        return (f"Settings(llm={self.llm.provider}, memory={self.memory.backend}, "
                f"execution={self.execution.mode})")


# Global settings instance
_global_settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return _global_settings


def reload_settings(config_file: Optional[str] = None):
    """Reload global settings."""
    global _global_settings
    _global_settings = Settings(config_file)