"""
Configuration management for LightCrew framework.
"""

import json
try:
    import yaml  # Optional; only required for YAML configs
except Exception:
    yaml = None
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path

from .logger import get_logger


logger = get_logger(__name__)


class ConfigManager:
    """Configuration manager for LightCrew."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        path = config_path or self.config_path
        
        if not path:
            logger.warning("No configuration path provided, using defaults")
            # Cache defaults to avoid repeated warnings on subsequent get() calls
            self._config = self._get_default_config()
            self._loaded = True
            return self._config
        
        if not os.path.exists(path):
            logger.warning(f"Configuration file not found: {path}, using defaults")
            self._config = self._get_default_config()
            self._loaded = True
            return self._config
        
        try:
            with open(path, 'r') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    if yaml is None:
                        raise ImportError("PyYAML is required to load YAML config files. Install with: pip install pyyaml")
                    self._config = yaml.safe_load(f) or {}
                elif path.endswith('.json'):
                    self._config = json.load(f) or {}
                else:
                    # Try to detect format
                    content = f.read()
                    try:
                        self._config = json.loads(content)
                    except json.JSONDecodeError:
                        if yaml is None:
                            raise ValueError(f"Unsupported configuration format and YAML parser not available: {path}")
                        try:
                            self._config = yaml.safe_load(content)
                        except Exception:
                            raise ValueError(f"Unsupported configuration format: {path}")
            
            self._loaded = True
            logger.info(f"Configuration loaded from: {path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            # Fallback to defaults and mark as loaded to avoid repeated attempts
            self._config = self._get_default_config()
            self._loaded = True
            return self._config
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        path = config_path or self.config_path
        
        if not path:
            logger.error("No configuration path provided for saving")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            
            with open(path, 'w') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    if yaml is None:
                        raise ImportError("PyYAML is required to save YAML config files. Install with: pip install pyyaml")
                    yaml.dump(self._config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {path}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if not self._loaded:
            self.load()
        
        # Support dot notation (e.g., "llm.provider")
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        if not self._loaded:
            self.load()
        
        # Support dot notation
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Configuration set: {key} = {value}")
    
    def update(self, config: Dict[str, Any]):
        """
        Update configuration with new values.
        
        Args:
            config: Configuration dictionary to merge
        """
        if not self._loaded:
            self.load()
        
        self._deep_update(self._config, config)
        logger.debug("Configuration updated")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep update dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "framework": {
                "name": "lightcrew",
                "version": "0.1.0",
                "mode": "lightweight"
            },
            "logging": {
                "level": "INFO",
                "use_colors": True,
                "log_file": None
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": None,
                "timeout": 30.0
            },
            "memory": {
                "backend": "in_memory",
                "default_ttl": None,
                "auto_cleanup": True,
                "cleanup_interval": 300.0
            },
            "execution": {
                "mode": "sequential",
                "max_concurrent_tasks": 5,
                "task_timeout": 180.0,
                "agent_timeout": 300.0
            },
            "tools": {
                "auto_register": True,
                "builtin_tools": ["echo", "calculator", "text_length"]
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        if not self._loaded:
            self.load()
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value using bracket notation."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Set configuration value using bracket notation."""
        self.set(key, value)


# Global configuration manager
_global_config = ConfigManager()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    return _global_config.load(config_path)


def save_config(config_path: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config_path: Path to save configuration
        
    Returns:
        True if successful, False otherwise
    """
    return _global_config.save(config_path)


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return _global_config.get(key, default)


def set_config(key: str, value: Any):
    """
    Set a configuration value.
    
    Args:
        key: Configuration key
        value: Value to set
    """
    _global_config.set(key, value)


def update_config(config: Dict[str, Any]):
    """
    Update configuration with new values.
    
    Args:
        config: Configuration dictionary to merge
    """
    _global_config.update(config)


# Environment variable support
def load_from_env(prefix: str = "LIGHTCREW_"):
    """
    Load configuration from environment variables.
    
    Args:
        prefix: Prefix for environment variables
    """
    env_config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Convert LIGHTCREW_LLM_PROVIDER to llm.provider
            config_key = key[len(prefix):].lower().replace('_', '.')
            
            # Try to parse as JSON, then as string
            try:
                parsed_value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                parsed_value = value
            
            # Set nested configuration
            keys = config_key.split('.')
            current = env_config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = parsed_value
    
    if env_config:
        update_config(env_config)
        logger.info(f"Loaded configuration from environment variables with prefix '{prefix}'")
