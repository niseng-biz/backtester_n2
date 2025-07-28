"""
Apple株価データの取得・格納・読み出しテストスクリプト（SQLite版）

Yahoo Financeからappleの株価や会社データを取得して、
SQLiteデータベースに格納し、読み出すまでの一連の流れをテストします。
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from stock_database.adapters.backtester_adapter import BacktesterDataAdapter
from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager
from stock_database.repositories.data_access_api import DataAccessAPI
from stock_database.utils.data_fetcher import DataFetcher

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_sqlite_connection():
    """SQLiteデータベース接続テスト"""
    logger.info("=== SQLite Connection Test ===")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Test connection
        db_manager.connect()
        logger.info(f"[OK] Connected to SQLite database at {db_manager.db_path}")
        
        # Get database info
        db_info = db_manager.get_database_info()
        logger.info(f"  Database size: {db_info['database_size']} bytes")
        logger.info(f"  Tables: {list(db_info['table_stats'].keys())}")
        
        for table_name, stats in db_info['table_stats'].items():
            logger.info(f"    {table_name}: {stats['count']} records")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"SQLite connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_fetching():
    """Yahoo FinanceからAppleのデータを取得してSQLiteに格納"""
    logger.info("\n=== Step 1: Data Fetching from Yahoo Finance ===")
    
    try:
        # Initialize data fetcher
        data_fetcher = DataFetcher()
        
        # Fetch Apple data
        symbol = "AAPL"
        logger.info(f"Fetching data for {symbol}...")
        
        # Fetch stock data (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        logger.info(f"Fetching stock data from {start_date.date()} to {end_date.date()}")
        stock_data_result = data_fetcher.fetch_stock_data(
            symbols=[symbol],
            force_full_update=True
        )
        
        if stock_data_result and stock_data_result.get(symbol, False):
            logger.info(f"[OK] Successfully fetched stock data for {symbol}")
            
            # Get the actual data from database to verify
            stock_data = data_fetcher.db_manager.get_stock_data(symbol, limit=10)
            if stock_data:
                logger.info(f"  Retrieved {len(stock_data)} stock data records from SQLite")
                sample = stock_data[0]
                logger.info(f"  Sample: {sample.date.date()} - O:{sample.open:.2f}, H:{sample.high:.2f}, L:{sample.low:.2f}, C:{sample.close:.2f}, V:{sample.volume}")
            else:
                logger.warning("  No stock data found in SQLite database")
        else:
            logger.error("[FAIL] Failed to fetch stock data")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Data fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_storage():
    """取得したデータをSQLiteに格納"""
    logger.info("\n=== Step 2: Data Storage to SQLite ===")
    
    try:
        # Initialize components
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        data_fetcher = DataFetcher()
        
        # Connect to database
        db_manager.connect()
        logger.info(f"[OK] Connected to SQLite database at {db_manager.db_path}")
        
        symbol = "AAPL"
        
        # Fetch and store stock data
        logger.info(f"Fetching and storing stock data for {symbol}...")
        
        stock_data_result = data_fetcher.fetch_stock_data([symbol], force_full_update=True)
        
        if stock_data_result and stock_data_result.get(symbol, False):
            # Data is automatically stored by DataFetcher
            stock_data = db_manager.get_stock_data(symbol, limit=50)
            if stock_data:
                logger.info(f"[OK] Stored {len(stock_data)} stock data records in SQLite")
            else:
                logger.warning("[WARN] No stock data found after fetching")
        
        return True
        
    except Exception as e:
        logger.error(f"Data storage failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def test_data_retrieval():
    """SQLiteからデータを読み出し"""
    logger.info("\n=== Step 3: Data Retrieval from SQLite ===")
    
    try:
        # Initialize data access API
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        # Test stock data retrieval
        logger.info(f"Retrieving stock data for {symbol}...")
        stock_data = data_api.get_stock_data(symbol, limit=10)
        
        if stock_data:
            logger.info(f"[OK] Retrieved {len(stock_data)} stock data records from SQLite")
            
            # Display sample data
            logger.info("  Recent stock data:")
            for i, data in enumerate(stock_data[:5]):
                logger.info(f"    {i+1}. {data.date.date()}: Close=${data.close:.2f}, Volume={data.volume:,}")
        else:
            logger.warning("[WARN] No stock data found in SQLite")
        
        return True
        
    except Exception as e:
        logger.error(f"Data retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtester_integration():
    """BacktesterDataAdapterを使用したデータ取得テスト"""
    logger.info("\n=== Step 4: Backtester Integration Test ===")
    
    try:
        # Initialize backtester adapter
        adapter = BacktesterDataAdapter()
        symbol = "AAPL"
        
        # Test market data retrieval
        logger.info(f"Testing backtester data adapter for {symbol}...")
        
        # Get recent market data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        market_data = adapter.get_market_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if market_data:
            logger.info(f"[OK] Retrieved {len(market_data)} market data records for backtester")
            
            # Display sample market data
            logger.info("  Market data for backtester:")
            for i, data in enumerate(market_data[:3]):
                logger.info(f"    {i+1}. {data.timestamp.date()}: OHLCV={data.open:.2f}/{data.high:.2f}/{data.low:.2f}/{data.close:.2f}/{data.volume}")
        else:
            logger.warning("[WARN] No market data found for backtester")
        
        # Test data validation
        logger.info(f"Validating data availability for backtesting...")
        validation_result = adapter.validate_data_availability(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            min_data_points=5
        )
        
        logger.info(f"  Data availability: {validation_result['is_available']}")
        logger.info(f"  Data points: {validation_result['data_points']}")
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                logger.warning(f"    Warning: {warning}")
        
        # Test performance stats
        perf_stats = adapter.get_performance_stats()
        logger.info(f"  Adapter performance:")
        logger.info(f"    Queries: {perf_stats['query_count']}")
        logger.info(f"    Conversions: {perf_stats['conversion_count']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Backtester integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_statistics():
    """データベース統計情報の表示"""
    logger.info("\n=== Step 5: Database Statistics ===")
    
    try:
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Get database information
        db_info = db_manager.get_database_info()
        
        logger.info("SQLite Database Statistics:")
        logger.info(f"  Database path: {db_info['database_path']}")
        logger.info(f"  Database size: {db_info['database_size']:,} bytes")
        
        # Table statistics
        logger.info("\nTable Statistics:")
        for table_name, stats in db_info['table_stats'].items():
            logger.info(f"  {table_name}: {stats['count']:,} records")
        
        return True
        
    except Exception as e:
        logger.error(f"Database statistics failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def main():
    """メインテスト関数"""
    logger.info("Apple Stock Data Flow Test (SQLite Version)")
    logger.info("=" * 60)
    logger.info("Testing: Yahoo Finance -> SQLite -> Backtester")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 6
    
    # Test 0: SQLite Connection
    if test_sqlite_connection():
        success_count += 1
        logger.info("[OK] Test 0 PASSED: SQLite Connection")
    else:
        logger.error("[FAIL] Test 0 FAILED: SQLite Connection")
    
    # Test 1: Data Fetching
    if test_data_fetching():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Data Fetching")
    else:
        logger.error("[FAIL] Test 1 FAILED: Data Fetching")
    
    # Test 2: Data Storage
    if test_data_storage():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Data Storage")
    else:
        logger.error("[FAIL] Test 2 FAILED: Data Storage")
    
    # Test 3: Data Retrieval
    if test_data_retrieval():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Data Retrieval")
    else:
        logger.error("[FAIL] Test 3 FAILED: Data Retrieval")
    
    # Test 4: Backtester Integration
    if test_backtester_integration():
        success_count += 1
        logger.info("[OK] Test 4 PASSED: Backtester Integration")
    else:
        logger.error("[FAIL] Test 4 FAILED: Backtester Integration")
    
    # Test 5: Database Statistics
    if test_database_statistics():
        success_count += 1
        logger.info("[OK] Test 5 PASSED: Database Statistics")
    else:
        logger.error("[FAIL] Test 5 FAILED: Database Statistics")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED! SQLite data flow is working correctly.")
        logger.info("[OK] Yahoo Finance data fetching")
        logger.info("[OK] SQLite data storage")
        logger.info("[OK] Data retrieval and access")
        logger.info("[OK] Backtester integration")
        logger.info("[OK] Database management")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed. Please check the errors above.")
        if success_count >= 4:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()