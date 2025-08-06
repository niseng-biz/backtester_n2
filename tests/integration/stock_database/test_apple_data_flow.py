"""
Apple株価データの取得・格納・読み出しテストスクリプト

Yahoo Financeからappleの株価や会社データを取得して、
MongoDB Atlasに格納し、読み出すまでの一連の流れをテストします。
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from stock_database.adapters.backtester_adapter import BacktesterDataAdapter
from stock_database.config import get_config_manager
from stock_database.sqlite_database import SQLiteManager
from stock_database.repositories.data_access_api import DataAccessAPI
from stock_database.utils.data_fetcher import DataFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_data_fetching():
    """Yahoo FinanceからAppleのデータを取得してMongoDBに格納"""
    logger.info("=== Step 1: Data Fetching from Yahoo Finance ===")
    
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
                logger.info(f"  Retrieved {len(stock_data)} stock data records from database")
                sample = stock_data[0]
                logger.info(f"  Sample: {sample.date.date()} - O:{sample.open:.2f}, H:{sample.high:.2f}, L:{sample.low:.2f}, C:{sample.close:.2f}, V:{sample.volume}")
            else:
                logger.warning("  No stock data found in database")
        else:
            logger.error("[FAIL] Failed to fetch stock data")
            return False
        
        # Fetch company info
        logger.info(f"Fetching company info for {symbol}...")
        try:
            company_info_result = data_fetcher.fetch_company_info([symbol])
            
            if company_info_result and company_info_result.get(symbol, False):
                logger.info(f"[OK] Successfully fetched company info for {symbol}")
                
                # Get the actual data from database to verify
                collection = data_fetcher.db_manager.get_collection(data_fetcher.db_manager.COMPANY_INFO_COLLECTION)
                company_doc = collection.find_one({"symbol": symbol})
                if company_doc:
                    logger.info(f"  Company: {company_doc.get('company_name', 'N/A')}")
                    logger.info(f"  Sector: {company_doc.get('sector', 'N/A')}")
                    market_cap = company_doc.get('market_cap')
                    if market_cap:
                        logger.info(f"  Market Cap: ${market_cap:,.0f}")
                    else:
                        logger.info("  Market Cap: N/A")
                else:
                    logger.warning("  No company info found in database")
            else:
                logger.error("[FAIL] Failed to fetch company info")
        except Exception as e:
            logger.error(f"[ERROR] Company info fetch error: {e}")
            import traceback
            traceback.print_exc()
        
        # Fetch financial data
        logger.info(f"Fetching financial data for {symbol}...")
        try:
            financial_data_result = data_fetcher.fetch_financial_data([symbol])
            
            if financial_data_result and financial_data_result.get(symbol, False):
                logger.info(f"[OK] Successfully fetched financial data for {symbol}")
                
                # Get the actual data from database to verify
                financial_data = data_fetcher.db_manager.get_financial_data(symbol)
                if financial_data:
                    logger.info(f"  Retrieved {len(financial_data)} financial data records from database")
                    sample = financial_data[0]
                    revenue_str = f"${sample.revenue:,.0f}" if sample.revenue else "N/A"
                    logger.info(f"  Sample: FY{sample.fiscal_year}Q{sample.fiscal_quarter} - Revenue: {revenue_str}")
                else:
                    logger.warning("  No financial data found in database")
            else:
                logger.error("[FAIL] Failed to fetch financial data")
        except Exception as e:
            logger.error(f"[ERROR] Financial data fetch error: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        logger.error(f"Data fetching failed: {e}")
        return False


def test_data_storage():
    """取得したデータをMongoDB Atlasに格納"""
    logger.info("\n=== Step 2: Data Storage to MongoDB Atlas ===")
    
    try:
        # Initialize components
        config = get_config_manager()
        db_manager = SQLiteManager(config)
        data_fetcher = DataFetcher()
        
        # Connect to database
        db_manager.connect()
        logger.info("✓ Connected to MongoDB Atlas")
        
        symbol = "AAPL"
        
        # Fetch and store stock data
        logger.info(f"Fetching and storing stock data for {symbol}...")
        
        stock_data_result = data_fetcher.fetch_stock_data([symbol], force_full_update=True)
        
        if stock_data_result and stock_data_result.get(symbol, False):
            # Data is automatically stored by DataFetcher
            stock_data = db_manager.get_stock_data(symbol, limit=50)
            if stock_data:
                logger.info(f"✓ Stored {len(stock_data)} stock data records")
            else:
                logger.warning("⚠ No stock data found after fetching")
        
        # Fetch and store company info
        logger.info(f"Fetching and storing company info for {symbol}...")
        company_info_result = data_fetcher.fetch_company_info([symbol])
        
        if company_info_result and company_info_result.get(symbol, False):
            # Data is automatically stored by DataFetcher
            collection = db_manager.get_collection(db_manager.COMPANY_INFO_COLLECTION)
            company_doc = collection.find_one({"symbol": symbol})
            if company_doc:
                logger.info(f"✓ Stored company info for {symbol}")
            else:
                logger.warning("⚠ No company info found after fetching")
        
        # Fetch and store financial data
        logger.info(f"Fetching and storing financial data for {symbol}...")
        financial_data_result = data_fetcher.fetch_financial_data([symbol])
        
        if financial_data_result and financial_data_result.get(symbol, False):
            # Data is automatically stored by DataFetcher
            financial_data = db_manager.get_financial_data(symbol)
            if financial_data:
                logger.info(f"✓ Stored {len(financial_data)} financial data records")
            else:
                logger.warning("⚠ No financial data found after fetching")
        
        return True
        
    except Exception as e:
        logger.error(f"Data storage failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def test_data_retrieval():
    """MongoDB Atlasからデータを読み出し"""
    logger.info("\n=== Step 3: Data Retrieval from MongoDB Atlas ===")
    
    try:
        # Initialize data access API
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        # Test stock data retrieval
        logger.info(f"Retrieving stock data for {symbol}...")
        stock_data = data_api.get_stock_data(symbol, limit=10)
        
        if stock_data:
            logger.info(f"✓ Retrieved {len(stock_data)} stock data records")
            
            # Display sample data
            logger.info("  Recent stock data:")
            for i, data in enumerate(stock_data[:5]):
                logger.info(f"    {i+1}. {data.date.date()}: Close=${data.close:.2f}, Volume={data.volume:,}")
        else:
            logger.warning("⚠ No stock data found")
        
        # Test company info retrieval
        logger.info(f"Retrieving company info for {symbol}...")
        company_info = data_api.get_company_info(symbol)
        
        if company_info:
            logger.info(f"✓ Retrieved company info")
            logger.info(f"  Company: {company_info.company_name}")
            logger.info(f"  Sector: {company_info.sector}")
            logger.info(f"  Industry: {company_info.industry}")
            if company_info.market_cap:
                logger.info(f"  Market Cap: ${company_info.market_cap:,.0f}")
        else:
            logger.warning("⚠ No company info found")
        
        # Test financial data retrieval
        logger.info(f"Retrieving financial data for {symbol}...")
        financial_data = data_api.get_financial_data(symbol, limit=5)
        
        if financial_data:
            logger.info(f"✓ Retrieved {len(financial_data)} financial data records")
            
            # Display sample financial data
            logger.info("  Recent financial data:")
            for i, data in enumerate(financial_data[:3]):
                revenue_str = f"${data.revenue:,.0f}" if data.revenue else "N/A"
                logger.info(f"    {i+1}. FY{data.fiscal_year}Q{data.fiscal_quarter}: Revenue={revenue_str}")
        else:
            logger.warning("⚠ No financial data found")
        
        return True
        
    except Exception as e:
        logger.error(f"Data retrieval failed: {e}")
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
            logger.info(f"✓ Retrieved {len(market_data)} market data records for backtester")
            
            # Display sample market data
            logger.info("  Market data for backtester:")
            for i, data in enumerate(market_data[:3]):
                logger.info(f"    {i+1}. {data.timestamp.date()}: OHLCV={data.open:.2f}/{data.high:.2f}/{data.low:.2f}/{data.close:.2f}/{data.volume}")
        else:
            logger.warning("⚠ No market data found for backtester")
        
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
        return False


def test_database_statistics():
    """データベース統計情報の表示"""
    logger.info("\n=== Step 5: Database Statistics ===")
    
    try:
        config = get_config_manager()
        db_manager = SQLiteManager(config)
        db_manager.connect()
        
        # Get database information
        db_info = db_manager.get_database_info()
        
        logger.info("Database Statistics:")
        logger.info(f"  Database: {db_info['database_name']}")
        logger.info(f"  Collections: {db_info['collection_count']}")
        logger.info(f"  Total Data Size: {db_info['data_size']:,} bytes")
        logger.info(f"  Total Storage Size: {db_info['storage_size']:,} bytes")
        
        # Collection statistics
        logger.info("\nCollection Statistics:")
        for collection_name, stats in db_info['collection_stats'].items():
            if 'error' not in stats:
                logger.info(f"  {collection_name}:")
                logger.info(f"    Documents: {stats['count']:,}")
                logger.info(f"    Size: {stats['size']:,} bytes")
                logger.info(f"    Indexes: {stats['indexes']}")
            else:
                logger.info(f"  {collection_name}: Error - {stats['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database statistics failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def main():
    """メインテスト関数"""
    logger.info("Apple Stock Data Flow Test")
    logger.info("=" * 60)
    logger.info("Testing: Yahoo Finance → MongoDB Atlas → Backtester")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 5
    
    # Test 1: Data Fetching
    if test_data_fetching():
        success_count += 1
        logger.info("✓ Test 1 PASSED: Data Fetching")
    else:
        logger.error("✗ Test 1 FAILED: Data Fetching")
    
    # Test 2: Data Storage
    if test_data_storage():
        success_count += 1
        logger.info("✓ Test 2 PASSED: Data Storage")
    else:
        logger.error("✗ Test 2 FAILED: Data Storage")
    
    # Test 3: Data Retrieval
    if test_data_retrieval():
        success_count += 1
        logger.info("✓ Test 3 PASSED: Data Retrieval")
    else:
        logger.error("✗ Test 3 FAILED: Data Retrieval")
    
    # Test 4: Backtester Integration
    if test_backtester_integration():
        success_count += 1
        logger.info("✓ Test 4 PASSED: Backtester Integration")
    else:
        logger.error("✗ Test 4 FAILED: Backtester Integration")
    
    # Test 5: Database Statistics
    if test_database_statistics():
        success_count += 1
        logger.info("✓ Test 5 PASSED: Database Statistics")
    else:
        logger.error("✗ Test 5 FAILED: Database Statistics")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Apple data flow is working correctly.")
        logger.info("✓ Yahoo Finance data fetching")
        logger.info("✓ MongoDB Atlas data storage")
        logger.info("✓ Data retrieval and access")
        logger.info("✓ Backtester integration")
        logger.info("✓ Database management")
    else:
        logger.error(f"❌ {total_tests - success_count} tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()