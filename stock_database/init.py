"""
Initialization module for the stock database system.
"""

import logging

from .config import get_config_manager, initialize_config, with_config
from .logger import setup_logger


def initialize_stock_database(config_path: str = None) -> None:
    """
    Initialize the stock database system with configuration and logging.
    
    Args:
        config_path: Optional path to configuration file
    """
    # Initialize configuration
    config_manager = initialize_config(config_path)
    
    # Setup logging based on configuration
    logging_config = config_manager.get_logging_config()
    setup_logger(logging_config)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("Stock database system initialized successfully")
    logger.info(f"Configuration loaded from: {config_manager.config_path}")
    logger.info(f"Tracking {len(config_manager.get_symbols())} symbols")


@with_config
def get_system_status(config_manager=None) -> dict:
    """
    Get current system status and configuration summary.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        Dictionary containing system status information
    """
    
    return {
        "config_path": config_manager.config_path,
        "database_host": config_manager.get("database.mongodb.host"),
        "database_name": config_manager.get("database.mongodb.database"),
        "symbols_count": len(config_manager.get_symbols()),
        "symbols": config_manager.get_symbols(),
        "logging_level": config_manager.get("logging.level"),
        "yahoo_finance_settings": {
            "request_delay": config_manager.get("data_fetching.yahoo_finance.request_delay"),
            "max_retries": config_manager.get("data_fetching.yahoo_finance.max_retries"),
            "batch_size": config_manager.get("data_fetching.yahoo_finance.batch_size")
        }
    }