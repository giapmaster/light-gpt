"""
Logging utilities for LightCrew framework.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    use_colors: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration for LightCrew.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string
        use_colors: Whether to use colored output
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Default format
    if format_string is None:
        format_string = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if use_colors:
        console_formatter = ColoredFormatter(format_string)
    else:
        console_formatter = logging.Formatter(format_string)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # LightCrew specific logger
    lightcrew_logger = logging.getLogger("lightcrew")
    lightcrew_logger.info("LightCrew logging initialized")
    
    return lightcrew_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Performance logging decorator
def log_performance(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function performance.
    
    Args:
        logger: Logger to use (defaults to function's module logger)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                func_logger.debug(
                    f"Function '{func.__name__}' executed in {execution_time:.3f}s"
                )
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                func_logger.error(
                    f"Function '{func.__name__}' failed after {execution_time:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


# Initialize default logging
_default_logger = setup_logging()