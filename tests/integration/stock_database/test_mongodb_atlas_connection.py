"""
MongoDB Atlas connection test script.

This script tests the connection to MongoDB Atlas and displays
connection information and basic database statistics.
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add the project root directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from stock_database.config import get_config_manager
from stock_database.database import MongoDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test MongoDB Atlas connection."""
    try:
        logger.info("Testing MongoDB Atlas connection...")
        
        # Initialize configuration
        config = get_config_manager()
        db_config = config.get_database_config().get("mongodb", {})
        
        # Display configuration (without sensitive data)
        logger.info("Configuration:")
        if db_config.get("is_atlas", False):
            logger.info(f"  Type: MongoDB Atlas")
            logger.info(f"  Connection String: {db_config.get('connection_string', 'Not set')}")
            logger.info(f"  Username: {db_config.get('username', 'Not set')}")
            logger.info(f"  Password: {'*' * len(db_config.get('password', '')) if db_config.get('password') else 'Not set'}")
        else:
            logger.info(f"  Type: Local MongoDB")
            logger.info(f"  Host: {db_config.get('host', 'localhost')}")
            logger.info(f"  Port: {db_config.get('port', 27017)}")
        
        logger.info(f"  Database: {db_config.get('database', 'stock_data')}")
        logger.info(f"  Connection Timeout: {db_config.get('connection_timeout', 30)}s")
        
        # Test connection
        db_manager = MongoDBManager(config)
        db_manager.connect()
        
        if db_manager.is_connected():
            logger.info("✓ Connection successful!")
            
            # Get database information
            db_info = db_manager.get_database_info()
            
            logger.info("\nDatabase Information:")
            logger.info(f"  Database Name: {db_info['database_name']}")
            logger.info(f"  Collections: {db_info['collection_count']}")
            logger.info(f"  Data Size: {db_info['data_size']:,} bytes")
            logger.info(f"  Storage Size: {db_info['storage_size']:,} bytes")
            logger.info(f"  Index Size: {db_info['index_size']:,} bytes")
            
            # Display collection information
            if db_info['collection_stats']:
                logger.info("\nCollection Statistics:")
                for collection_name, stats in db_info['collection_stats'].items():
                    if 'error' not in stats:
                        logger.info(f"  {collection_name}:")
                        logger.info(f"    Documents: {stats['count']:,}")
                        logger.info(f"    Size: {stats['size']:,} bytes")
                        logger.info(f"    Indexes: {stats['indexes']}")
                        logger.info(f"    Index Size: {stats['totalIndexSize']:,} bytes")
                    else:
                        logger.info(f"  {collection_name}: Error - {stats['error']}")
            else:
                logger.info("\nNo collections found in database")
            
            # Test basic operations
            logger.info("\nTesting Basic Operations:")
            
            # Test ping
            try:
                db_manager.client.admin.command('ping')
                logger.info("  ✓ Ping successful")
            except Exception as e:
                logger.error(f"  ✗ Ping failed: {e}")
            
            # Test collection access
            try:
                collection = db_manager.get_collection("test_collection")
                logger.info("  ✓ Collection access successful")
            except Exception as e:
                logger.error(f"  ✗ Collection access failed: {e}")
            
            # Test simple query
            try:
                stock_collection = db_manager.get_collection(db_manager.STOCK_DATA_COLLECTION)
                count = stock_collection.count_documents({})
                logger.info(f"  ✓ Query successful: {count} stock data documents")
            except Exception as e:
                logger.error(f"  ✗ Query failed: {e}")
            
            return True
            
        else:
            logger.error("✗ Connection failed!")
            return False
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def test_environment_variables():
    """Test if environment variables are properly loaded."""
    import os

    from dotenv import load_dotenv

    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent / "stock_database" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f".env file not found at {env_path}")
    
    logger.info("Testing Environment Variables:")
    
    required_vars = ['MONGODB_ADRESS', 'MONGODB_USERNAME', 'MONGODB_PASSWORD']
    all_present = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'MONGODB_PASSWORD':
                logger.info(f"  ✓ {var}: {'*' * len(value)}")
            else:
                logger.info(f"  ✓ {var}: {value}")
        else:
            logger.error(f"  ✗ {var}: Not set")
            all_present = False
    
    return all_present


def main():
    """Main test function."""
    logger.info("MongoDB Atlas Connection Test")
    logger.info("=" * 50)
    
    # Test environment variables first
    if not test_environment_variables():
        logger.error("Environment variables are not properly configured!")
        logger.error("Please check your .env file in the stock_database directory.")
        sys.exit(1)
    
    logger.info("")
    
    # Test connection
    if test_connection():
        logger.info("=" * 50)
        logger.info("✓ All tests passed! MongoDB Atlas connection is working.")
    else:
        logger.error("=" * 50)
        logger.error("✗ Connection test failed!")
        logger.error("Please check your MongoDB Atlas configuration and network connectivity.")
        sys.exit(1)


if __name__ == "__main__":
    main()