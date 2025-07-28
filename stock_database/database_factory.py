"""
Database factory for creating appropriate database manager instances.
"""

import logging
from typing import Union

from .config import get_config_manager
from .database import MongoDBManager
from .sqlite_database import SQLiteManager

logger = logging.getLogger(__name__)


def create_database_manager(config_manager=None) -> Union[MongoDBManager, SQLiteManager]:
    """
    Create appropriate database manager based on configuration.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        Database manager instance (MongoDB or SQLite)
    """
    config = config_manager or get_config_manager()
    db_config = config.get_database_config()
    
    db_type = db_config.get("type", "sqlite").lower()
    
    if db_type == "mongodb":
        logger.info("Creating MongoDB database manager")
        return MongoDBManager(config)
    elif db_type == "sqlite":
        logger.info("Creating SQLite database manager")
        return SQLiteManager(config)
    else:
        logger.warning(f"Unknown database type '{db_type}', defaulting to SQLite")
        return SQLiteManager(config)


class DatabaseManager:
    """
    Unified database manager that delegates to appropriate implementation.
    """
    
    def __init__(self, config_manager=None):
        """Initialize database manager."""
        self._manager = create_database_manager(config_manager)
        
        # Expose common interface
        self.STOCK_DATA_COLLECTION = getattr(self._manager, 'STOCK_DATA_COLLECTION', None) or getattr(self._manager, 'STOCK_DATA_TABLE', None)
        self.FINANCIAL_DATA_COLLECTION = getattr(self._manager, 'FINANCIAL_DATA_COLLECTION', None) or getattr(self._manager, 'FINANCIAL_DATA_TABLE', None)
        self.COMPANY_INFO_COLLECTION = getattr(self._manager, 'COMPANY_INFO_COLLECTION', None) or getattr(self._manager, 'COMPANY_INFO_TABLE', None)
    
    def __getattr__(self, name):
        """Delegate all other attributes to the underlying manager."""
        return getattr(self._manager, name)
    
    def __enter__(self):
        """Context manager entry."""
        return self._manager.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return self._manager.__exit__(exc_type, exc_val, exc_tb)