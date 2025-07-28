"""
Configuration management for the stock database system.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and access for the stock database system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default locations.
        """
        # Load environment variables from .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        
        self.config_path = config_path or self._find_config_file()
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def _find_config_file(self) -> str:
        """Find the configuration file in default locations."""
        possible_paths = [
            "config.yaml",
            "stock_database/config.yaml",
            os.path.expanduser("~/.stock_database/config.yaml"),
            "/etc/stock_database/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return default path if none found
        return "config.yaml"
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file) or {}
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found at {self.config_path}, using defaults")
                self._config = self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        # Default to SQLite for simplicity
        database_config = {
            "type": "sqlite",
            "sqlite": {
                "path": "data/stock_data.db"
            }
        }
        
        # Check for MongoDB Atlas environment variables (optional)
        mongodb_address = os.getenv('MONGODB_ADRESS')  # Note: keeping original typo from .env
        mongodb_username = os.getenv('MONGODB_USERNAME')
        mongodb_password = os.getenv('MONGODB_PASSWORD')
        
        # If MongoDB environment variables are set, add MongoDB config
        if mongodb_address and mongodb_username and mongodb_password:
            database_config["mongodb"] = {
                "connection_string": f"{mongodb_address}",
                "username": mongodb_username,
                "password": mongodb_password,
                "database": "stock_data",
                "connection_timeout": 30,
                "max_pool_size": 100,
                "is_atlas": True
            }
            logger.info("MongoDB Atlas configuration available from environment variables")
        
        logger.info(f"Using {database_config['type']} database configuration")
        
        return {
            "database": database_config,
            "data_fetching": {
                "yahoo_finance": {
                    "request_delay": 1.0,
                    "max_retries": 3,
                    "timeout": 30,
                    "batch_size": 10
                },
                "symbols": [
                    "AAPL",
                    "GOOGL", 
                    "MSFT",
                    "TSLA"
                ],
                "update_schedule": {
                    "stock_data": "0 18 * * 1-5",  # 平日18時
                    "financial_data": "0 2 * * 6"   # 土曜2時
                }
            },
            "logging": {
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
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.mongodb.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            path: Path to save configuration. If None, uses current config_path.
        """
        save_path = path or self.config_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(self._config, file, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get("database", {})
    
    def get_data_fetching_config(self) -> Dict[str, Any]:
        """Get data fetching configuration."""
        return self.get("data_fetching", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get("logging", {})
    
    def get_symbols(self) -> list:
        """Get list of symbols to track."""
        return self.get("data_fetching.symbols", [])
    
    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to the tracking list."""
        symbols = self.get_symbols()
        if symbol not in symbols:
            symbols.append(symbol)
            self.set("data_fetching.symbols", symbols)
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from the tracking list."""
        symbols = self.get_symbols()
        if symbol in symbols:
            symbols.remove(symbol)
            self.set("data_fetching.symbols", symbols)


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def initialize_config(config_path: Optional[str] = None) -> ConfigManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager