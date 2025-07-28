"""
Initialization module for the stock database system.
"""

import logging

from .config import get_config_manager, initialize_config
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


def get_system_status() -> dict:
    """
    Get current system status and configuration summary.
    
    Returns:
        Dictionary containing system status information
    """
    config = get_config_manager()
    
    return {
        "config_path": config.config_path,
        "database_host": config.get("database.mongodb.host"),
        "database_name": config.get("database.mongodb.database"),
        "symbols_count": len(config.get_symbols()),
        "symbols": config.get_symbols(),
        "logging_level": config.get("logging.level"),
        "yahoo_finance_settings": {
            "request_delay": config.get("data_fetching.yahoo_finance.request_delay"),
            "max_retries": config.get("data_fetching.yahoo_finance.max_retries"),
            "batch_size": config.get("data_fetching.yahoo_finance.batch_size")
        }
    }