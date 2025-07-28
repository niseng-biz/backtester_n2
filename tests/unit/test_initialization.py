#!/usr/bin/env python3
"""
Test script to verify the complete initialization system.
"""

import json
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stock_database import get_system_status, initialize_stock_database


def test_initialization():
    """Test the complete initialization system."""
    print("Testing stock database initialization...")
    
    # Initialize the system
    initialize_stock_database()
    print("✓ System initialized successfully")
    
    # Get system status
    status = get_system_status()
    print("✓ System status retrieved")
    
    # Display status information
    print("\n=== System Status ===")
    print(f"Config Path: {status['config_path']}")
    print(f"Database Host: {status['database_host']}")
    print(f"Database Name: {status['database_name']}")
    print(f"Symbols Count: {status['symbols_count']}")
    print(f"Logging Level: {status['logging_level']}")
    print(f"Yahoo Finance Request Delay: {status['yahoo_finance_settings']['request_delay']}s")
    print(f"Yahoo Finance Max Retries: {status['yahoo_finance_settings']['max_retries']}")
    print(f"Yahoo Finance Batch Size: {status['yahoo_finance_settings']['batch_size']}")
    
    print(f"\nTracked Symbols: {', '.join(status['symbols'])}")
    
    print("\n✓ All initialization tests passed!")


def main():
    """Main test function."""
    print("=== Stock Database Initialization Test ===\n")
    
    try:
        test_initialization()
        print("\n🎉 Initialization system working correctly!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())