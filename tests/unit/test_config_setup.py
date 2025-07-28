#!/usr/bin/env python3
"""
Test script to verify the configuration and logging setup.
"""

import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from stock_database.config import ConfigManager, get_config_manager
from stock_database.logger import setup_logger


def test_config_manager():
    """Test the configuration manager functionality."""
    print("Testing ConfigManager...")
    
    # Test initialization
    config = ConfigManager()
    print(f"✓ ConfigManager initialized with config path: {config.config_path}")
    
    # Test getting values
    db_host = config.get("database.mongodb.host")
    print(f"✓ Database host: {db_host}")
    
    symbols = config.get_symbols()
    print(f"✓ Symbols: {symbols}")
    
    # Test setting values
    config.set("test.value", "test_data")
    test_value = config.get("test.value")
    print(f"✓ Set and get test value: {test_value}")
    
    # Test adding/removing symbols
    config.add_symbol("TEST")
    symbols_after_add = config.get_symbols()
    print(f"✓ Symbols after adding TEST: {symbols_after_add}")
    
    config.remove_symbol("TEST")
    symbols_after_remove = config.get_symbols()
    print(f"✓ Symbols after removing TEST: {symbols_after_remove}")
    
    print("ConfigManager tests passed!\n")


def test_logger_setup():
    """Test the logger setup functionality."""
    print("Testing Logger setup...")
    
    # Get config for logging
    config = get_config_manager()
    logging_config = config.get_logging_config()
    
    # Setup logger
    logger = setup_logger(logging_config)
    print("✓ Logger setup completed")
    
    # Test logging
    import logging
    test_logger = logging.getLogger("test_logger")
    
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    
    print("✓ Test messages logged")
    print("Logger setup tests passed!\n")


def main():
    """Main test function."""
    print("=== Stock Database Configuration and Logging Test ===\n")
    
    try:
        test_config_manager()
        test_logger_setup()
        print("🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())