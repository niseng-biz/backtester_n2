"""
Logging configuration and setup for the stock database system.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, List


def setup_logger(config: Dict[str, Any] = None) -> logging.Logger:
    """
    Set up logging configuration based on the provided config.
    
    Args:
        config: Logging configuration dictionary
        
    Returns:
        Configured logger instance
    """
    if config is None:
        config = _get_default_logging_config()
    
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set logging level
    level = getattr(logging, config.get("level", "INFO").upper())
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    
    # Add handlers
    handlers = config.get("handlers", [])
    for handler_config in handlers:
        handler = _create_handler(handler_config, formatter)
        if handler:
            logger.addHandler(handler)
    
    # If no handlers were added, add a console handler
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def _create_handler(handler_config: Dict[str, Any], formatter: logging.Formatter) -> logging.Handler:
    """
    Create a logging handler based on configuration.
    
    Args:
        handler_config: Handler configuration dictionary
        formatter: Logging formatter
        
    Returns:
        Configured logging handler
    """
    handler_type = handler_config.get("type", "console")
    
    if handler_type == "console":
        handler = logging.StreamHandler(sys.stdout)
    
    elif handler_type == "file":
        filename = handler_config.get("filename", "stock_data.log")
        
        # Ensure log directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if rotation is needed
        max_bytes = handler_config.get("max_bytes", 10485760)  # 10MB
        backup_count = handler_config.get("backup_count", 5)
        
        if max_bytes > 0:
            handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(filename, encoding='utf-8')
    
    else:
        # Unknown handler type, return console handler as fallback
        handler = logging.StreamHandler(sys.stdout)
    
    handler.setFormatter(formatter)
    return handler


def _get_default_logging_config() -> Dict[str, Any]:
    """Get default logging configuration."""
    return {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "handlers": [
            {
                "type": "file",
                "filename": "stock_data.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5
            },
            {
                "type": "console"
            }
        ]
    }


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capability to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__name__)