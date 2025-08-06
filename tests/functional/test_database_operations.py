#!/usr/bin/env python3
"""
Test script for database operations
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager

def test_database_operations():
    """Test the database operations"""
    print("🧪 Testing Database Operations")
    print("=" * 50)
    
    try:
        # Initialize config manager
        print("🔧 Initializing config manager...")
        config_manager = get_config_manager()
        print("✅ Config manager initialized")
        
        # Initialize database manager
        print("🗄️  Initializing database manager...")
        db_manager = DatabaseManager(config_manager)
        print("✅ Database manager initialized")
        
        # Connect to database
        print("🔌 Connecting to database...")
        db_manager.connect()
        print("✅ Database connected")
        
        # Test basic database operations
        print("📊 Testing basic database operations...")
        
        # Check if database file exists
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stock_data.db')
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            
            # Check database size
            size = os.path.getsize(db_path)
            print(f"📏 Database size: {size:,} bytes")
            
            # Test connection by querying sqlite_master
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tables in database: {tables}")
            
            # Test a simple query if tables exist
            if tables:
                for table in tables[:3]:  # Test first 3 tables
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  📊 {table}: {count} records")
                    except Exception as e:
                        print(f"  ⚠️  Could not query {table}: {e}")
            
            conn.close()
        else:
            print(f"ℹ️  Database file does not exist yet: {db_path}")
            print("   This is normal for a fresh installation")
        
        # Disconnect from database
        print("🔌 Disconnecting from database...")
        db_manager.disconnect()
        print("✅ Database disconnected")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_operations()
    if success:
        print("\n✅ Database operations test PASSED")
    else:
        print("\n❌ Database operations test FAILED")
        sys.exit(1)