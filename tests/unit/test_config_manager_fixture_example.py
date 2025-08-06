"""
Example test showing how to use the config_manager fixture instead of get_config_manager().

This demonstrates the unified pattern for configuration management in tests.
"""

import pytest
from stock_database.database_factory import DatabaseManager
from stock_database.sqlite_database import SQLiteManager


class TestConfigManagerFixture:
    """Example test class showing config manager fixture usage."""
    
    def test_config_manager_fixture(self, config_manager):
        """Test using the config_manager fixture instead of get_config_manager()."""
        # Before: config = get_config_manager()
        # After: Use the config_manager fixture parameter
        
        assert config_manager is not None
        assert hasattr(config_manager, 'get')
        assert hasattr(config_manager, 'get_database_config')
        
        # Test getting configuration values
        db_config = config_manager.get_database_config()
        assert db_config is not None
        assert 'type' in db_config
        
    def test_database_manager_with_fixture(self, database_manager):
        """Test using the database_manager fixture."""
        # Before: 
        # config = get_config_manager()
        # db_manager = DatabaseManager(config)
        # After: Use the database_manager fixture parameter
        
        assert database_manager is not None
        assert hasattr(database_manager, 'connect')
        assert hasattr(database_manager, 'disconnect')
        
    def test_sqlite_manager_with_fixture(self, sqlite_db_manager):
        """Test using the sqlite_db_manager fixture."""
        # Before:
        # config = get_config_manager()
        # db_manager = SQLiteManager(config)
        # After: Use the sqlite_db_manager fixture parameter
        
        assert sqlite_db_manager is not None
        assert hasattr(sqlite_db_manager, 'connect')
        assert hasattr(sqlite_db_manager, 'disconnect')
        assert hasattr(sqlite_db_manager, 'db_path')
        
    def test_manual_config_creation_when_needed(self, config_manager):
        """Test creating database manager manually when needed."""
        # Sometimes you still need to create managers manually
        # but you can use the fixture for the config
        
        # Before: 
        # config = get_config_manager()
        # db_manager = SQLiteManager(config)
        
        # After: Use fixture for config
        db_manager = SQLiteManager(config_manager)
        
        assert db_manager is not None
        assert db_manager.config == config_manager