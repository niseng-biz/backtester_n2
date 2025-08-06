"""
Database factory for creating SQLite database manager instances.
"""

import logging

from .config import get_config_manager, with_config
from .sqlite_database import SQLiteManager

logger = logging.getLogger(__name__)


@with_config
def create_database_manager(config_manager=None) -> SQLiteManager:
    """
    Create SQLite database manager.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        SQLite database manager instance
    """
    logger.info("Creating SQLite database manager")
    return SQLiteManager(config_manager)


class DatabaseManager:
    """
    Simplified database manager that delegates to SQLite implementation.
    """
    
    def __init__(self, config_manager=None):
        """Initialize database manager with SQLite."""
        if config_manager is None:
            config_manager = get_config_manager()
        self._manager = SQLiteManager(config_manager)
    
    def __getattr__(self, name):
        """Delegate all attributes to the SQLite manager."""
        return getattr(self._manager, name)
    
    def __enter__(self):
        """Context manager entry."""
        return self._manager.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return self._manager.__exit__(exc_type, exc_val, exc_tb)