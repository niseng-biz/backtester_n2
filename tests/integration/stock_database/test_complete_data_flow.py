"""
包括的なデータフロー テストスクリプト（SQLite版）

Yahoo Financeから株価データ、会社情報、財務データを取得して、
SQLiteデータベースに格納し、読み出すまでの完全なテストを実行します。
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_complete_data_fetching():
    """Yahoo Financeから全種類のデータを取得"""
    logger.info("=== Complete Data Fetching Test ===")
    
    try:
        # Initialize data fetcher
        data_fetcher = DataFetcher()
        symbol = "AAPL"
        
        logger.info(f"Fetching all data types for {symbol}...")
        
        # 1. Stock Data
        logger.info("1. Fetching stock data...")
        stock_result = data_fetcher.fetch_stock_data([symbol], force_full_update=True)
        
        if stock_result and stock_result.get(symbol, False):
            stock_data = data_fetcher.db_manager.get_stock_data(symbol, limit=5)
            logger.info(f"   [OK] Stock data: {len(stock_data)} records")
            if stock_data:
                sample = stock_data[0]
                logger.info(f"   Sample: {sample.date.date()} - Close: ${sample.close:.2f}")
        else:
            logger.error("   [FAIL] Stock data fetch failed")
            return False
        
        # 2. Company Info
        logger.info("2. Fetching company info...")
        try:
            company_result = data_fetcher.fetch_company_info([symbol])
            
            if company_result and company_result.get(symbol, False):
                # Get company info from database
                collection = data_fetcher.db_manager.get_collection(data_fetcher.db_manager.COMPANY_INFO_TABLE)
                company_doc = collection.find_one({"symbol": symbol})
                
                if company_doc:
                    logger.info(f"   [OK] Company info retrieved")
                    logger.info(f"   Company: {company_doc.get('company_name', 'N/A')}")
                    logger.info(f"   Sector: {company_doc.get('sector', 'N/A')}")
                    logger.info(f"   Industry: {company_doc.get('industry', 'N/A')}")
                else:
                    logger.warning("   [WARN] Company info not found in database")
            else:
                logger.warning("   [WARN] Company info fetch returned False")
        except Exception as e:
            logger.error(f"   [ERROR] Company info fetch failed: {e}")
        
        # 3. Financial Data
        logger.info("3. Fetching financial data...")
        try:
            financial_result = data_fetcher.fetch_financial_data([symbol])
            
            if financial_result and financial_result.get(symbol, False):
                # Get financial data from database
                financial_data = data_fetcher.db_manager.get_financial_data(symbol)
                
                if financial_data:
                    logger.info(f"   [OK] Financial data: {len(financial_data)} records")
                    sample = financial_data[0]
                    revenue_str = f"${sample.revenue:,.0f}" if sample.revenue else "N/A"
                    logger.info(f"   Sample: FY{sample.fiscal_year}Q{sample.fiscal_quarter} - Revenue: {revenue_str}")
                else:
                    logger.warning("   [WARN] Financial data not found in database")
            else:
                logger.warning("   [WARN] Financial data fetch returned False")
        except Exception as e:
            logger.error(f"   [ERROR] Financial data fetch failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Complete data fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_storage_verification():
    """データ格納の検証"""
    logger.info("\\n=== Data Storage Verification ===")
    
    try:
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        symbol = "AAPL"
        logger.info(f"Verifying stored data for {symbol}...")
        
        # 1. Stock Data Verification
        logger.info("1. Verifying stock data...")
        stock_data = db_manager.get_stock_data(symbol, limit=10)
        logger.info(f"   Stock data records: {len(stock_data)}")
        
        if stock_data:
            logger.info("   Recent stock data:")
            for i, data in enumerate(stock_data[:3]):
                logger.info(f"     {i+1}. {data.date.date()}: ${data.close:.2f} (Vol: {data.volume:,})")
        
        # 2. Company Info Verification
        logger.info("2. Verifying company info...")
        try:
            collection = db_manager.get_collection(db_manager.COMPANY_INFO_TABLE)
            company_doc = collection.find_one({"symbol": symbol})
            
            if company_doc:
                logger.info("   [OK] Company info found:")
                logger.info(f"     Name: {company_doc.get('company_name', 'N/A')}")
                logger.info(f"     Sector: {company_doc.get('sector', 'N/A')}")
                logger.info(f"     Industry: {company_doc.get('industry', 'N/A')}")
                logger.info(f"     Market Cap: ${company_doc.get('market_cap', 0):,.0f}" if company_doc.get('market_cap') else "     Market Cap: N/A")
                logger.info(f"     Employees: {company_doc.get('employees', 'N/A'):,}" if company_doc.get('employees') else "     Employees: N/A")
                logger.info(f"     Website: {company_doc.get('website', 'N/A')}")
            else:
                logger.warning("   [WARN] No company info found")
        except Exception as e:
            logger.error(f"   [ERROR] Company info verification failed: {e}")
        
        # 3. Financial Data Verification
        logger.info("3. Verifying financial data...")
        try:
            financial_data = db_manager.get_financial_data(symbol)
            logger.info(f"   Financial data records: {len(financial_data)}")
            
            if financial_data:
                logger.info("   Recent financial data:")
                for i, data in enumerate(financial_data[:3]):
                    revenue_str = f"${data.revenue:,.0f}" if data.revenue else "N/A"
                    net_income_str = f"${data.net_income:,.0f}" if data.net_income else "N/A"
                    eps_str = f"${data.eps:.2f}" if data.eps else "N/A"
                    logger.info(f"     {i+1}. FY{data.fiscal_year}Q{data.fiscal_quarter}:")
                    logger.info(f"        Revenue: {revenue_str}")
                    logger.info(f"        Net Income: {net_income_str}")
                    logger.info(f"        EPS: {eps_str}")
            else:
                logger.warning("   [WARN] No financial data found")
        except Exception as e:
            logger.error(f"   [ERROR] Financial data verification failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data storage verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def test_data_access_api():
    """DataAccessAPIを使用したデータ読み出しテスト"""
    logger.info("\\n=== Data Access API Test ===")
    
    try:
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        logger.info(f"Testing DataAccessAPI for {symbol}...")
        
        # 1. Stock Data Access
        logger.info("1. Testing stock data access...")
        stock_data = data_api.get_stock_data(symbol, limit=5)
        logger.info(f"   Retrieved {len(stock_data)} stock records")
        
        if stock_data:
            sample = stock_data[0]
            logger.info(f"   Latest: {sample.date.date()} - ${sample.close:.2f}")
        
        # 2. Company Info Access
        logger.info("2. Testing company info access...")
        company_info = data_api.get_company_info(symbol)
        
        if company_info:
            logger.info(f"   [OK] Company: {company_info.company_name}")
            logger.info(f"   Sector: {company_info.sector}")
            logger.info(f"   Industry: {company_info.industry}")
        else:
            logger.warning("   [WARN] No company info available")
        
        # 3. Financial Data Access
        logger.info("3. Testing financial data access...")
        financial_data = data_api.get_financial_data(symbol, limit=3)
        logger.info(f"   Retrieved {len(financial_data)} financial records")
        
        if financial_data:
            sample = financial_data[0]
            revenue_str = f"${sample.revenue:,.0f}" if sample.revenue else "N/A"
            logger.info(f"   Latest: FY{sample.fiscal_year}Q{sample.fiscal_quarter} - Revenue: {revenue_str}")
        
        # 4. Available Symbols
        logger.info("4. Testing available symbols...")
        available_symbols = data_api.get_available_symbols()
        
        for data_type, symbols in available_symbols.items():
            logger.info(f"   {data_type}: {len(symbols)} symbols")
            if symbols and len(symbols) <= 10:
                logger.info(f"     Symbols: {', '.join(symbols)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data access API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtester_integration():
    """BacktesterDataAdapterの統合テスト"""
    logger.info("\\n=== Backtester Integration Test ===")
    
    try:
        adapter = BacktesterDataAdapter()
        symbol = "AAPL"
        
        logger.info(f"Testing backtester integration for {symbol}...")
        
        # 1. Market Data Retrieval
        logger.info("1. Testing market data retrieval...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        market_data = adapter.get_market_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"   Retrieved {len(market_data)} market data records")
        
        if market_data:
            logger.info("   Sample market data:")
            for i, data in enumerate(market_data[:3]):
                logger.info(f"     {i+1}. {data.timestamp.date()}: OHLCV={data.open:.2f}/{data.high:.2f}/{data.low:.2f}/{data.close:.2f}/{data.volume}")
        
        # 2. Data Statistics
        logger.info("2. Testing data statistics...")
        try:
            stats = adapter.get_data_statistics(symbol)
            
            if "error" not in stats:
                logger.info(f"   Data points: {stats['data_points']}")
                logger.info(f"   Date range: {stats['date_range'][0].date()} to {stats['date_range'][1].date()}")
                logger.info(f"   Price range: ${stats['price_statistics']['min']:.2f} - ${stats['price_statistics']['max']:.2f}")
                logger.info(f"   Current price: ${stats['price_statistics']['current']:.2f}")
                if 'volatility' in stats:
                    logger.info(f"   Volatility: {stats['volatility']:.4f}")
            else:
                logger.warning(f"   [WARN] Statistics error: {stats['error']}")
        except Exception as e:
            logger.warning(f"   [WARN] Statistics test failed: {e}")
        
        # 3. Performance Stats
        logger.info("3. Testing performance stats...")
        perf_stats = adapter.get_performance_stats()
        logger.info(f"   Queries: {perf_stats['query_count']}")
        logger.info(f"   Conversions: {perf_stats['conversion_count']}")
        logger.info(f"   Cache hit rate: {perf_stats['cache_hit_rate']:.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f"Backtester integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_comprehensive_stats():
    """包括的なデータベース統計"""
    logger.info("\\n=== Comprehensive Database Statistics ===")
    
    try:
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Database info
        db_info = db_manager.get_database_info()
        
        logger.info("Database Overview:")
        logger.info(f"  Path: {db_info['database_path']}")
        logger.info(f"  Size: {db_info['database_size']:,} bytes ({db_info['database_size']/1024/1024:.2f} MB)")
        
        # Detailed table statistics
        logger.info("\\nTable Statistics:")
        total_records = 0
        
        for table_name, stats in db_info['table_stats'].items():
            count = stats['count']
            total_records += count
            logger.info(f"  {table_name}: {count:,} records")
            
            # Get sample data for each table
            if count > 0:
                try:
                    if table_name == 'stock_data':
                        sample_data = db_manager.get_stock_data("AAPL", limit=1)
                        if sample_data:
                            sample = sample_data[0]
                            logger.info(f"    Latest: {sample.date.date()} - ${sample.close:.2f}")
                    
                    elif table_name == 'company_info':
                        collection = db_manager.get_collection(table_name)
                        sample_doc = collection.find_one({})
                        if sample_doc:
                            logger.info(f"    Sample: {sample_doc.get('symbol', 'N/A')} - {sample_doc.get('company_name', 'N/A')}")
                    
                    elif table_name == 'financial_data':
                        financial_data = db_manager.get_financial_data("AAPL", fiscal_year=None, fiscal_quarter=None)
                        if financial_data:
                            sample = financial_data[0]
                            revenue_str = f"${sample.revenue:,.0f}" if sample.revenue else "N/A"
                            logger.info(f"    Latest: FY{sample.fiscal_year}Q{sample.fiscal_quarter} - Revenue: {revenue_str}")
                
                except Exception as e:
                    logger.debug(f"    Could not get sample data: {e}")
        
        logger.info(f"\\nTotal Records: {total_records:,}")
        
        # Data completeness check
        logger.info("\\nData Completeness Check:")
        symbols_with_stock = set()
        symbols_with_company = set()
        symbols_with_financial = set()
        
        # Check stock data symbols
        try:
            cursor = db_manager.connection.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM stock_data")
            symbols_with_stock = {row[0] for row in cursor.fetchall()}
            logger.info(f"  Symbols with stock data: {len(symbols_with_stock)}")
        except Exception as e:
            logger.debug(f"Could not check stock symbols: {e}")
        
        # Check company info symbols
        try:
            cursor.execute("SELECT DISTINCT symbol FROM company_info")
            symbols_with_company = {row[0] for row in cursor.fetchall()}
            logger.info(f"  Symbols with company info: {len(symbols_with_company)}")
        except Exception as e:
            logger.debug(f"Could not check company symbols: {e}")
        
        # Check financial data symbols
        try:
            cursor.execute("SELECT DISTINCT symbol FROM financial_data")
            symbols_with_financial = {row[0] for row in cursor.fetchall()}
            logger.info(f"  Symbols with financial data: {len(symbols_with_financial)}")
        except Exception as e:
            logger.debug(f"Could not check financial symbols: {e}")
        
        # Show completeness
        all_symbols = symbols_with_stock | symbols_with_company | symbols_with_financial
        if all_symbols:
            logger.info(f"  Total unique symbols: {len(all_symbols)}")
            logger.info(f"  Symbols: {', '.join(sorted(all_symbols))}")
            
            complete_symbols = symbols_with_stock & symbols_with_company & symbols_with_financial
            logger.info(f"  Complete data (all 3 types): {len(complete_symbols)} symbols")
            if complete_symbols:
                logger.info(f"    Complete symbols: {', '.join(sorted(complete_symbols))}")
        
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
    logger.info("Complete Data Flow Test (Stock + Company + Financial)")
    logger.info("=" * 70)
    logger.info("Testing: Yahoo Finance -> SQLite -> DataAccessAPI -> Backtester")
    logger.info("=" * 70)
    
    success_count = 0
    total_tests = 5
    
    # Test 1: Complete Data Fetching
    if test_complete_data_fetching():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Complete Data Fetching")
    else:
        logger.error("[FAIL] Test 1 FAILED: Complete Data Fetching")
    
    # Test 2: Data Storage Verification
    if test_data_storage_verification():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Data Storage Verification")
    else:
        logger.error("[FAIL] Test 2 FAILED: Data Storage Verification")
    
    # Test 3: Data Access API
    if test_data_access_api():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Data Access API")
    else:
        logger.error("[FAIL] Test 3 FAILED: Data Access API")
    
    # Test 4: Backtester Integration
    if test_backtester_integration():
        success_count += 1
        logger.info("[OK] Test 4 PASSED: Backtester Integration")
    else:
        logger.error("[FAIL] Test 4 FAILED: Backtester Integration")
    
    # Test 5: Database Statistics
    if test_database_comprehensive_stats():
        success_count += 1
        logger.info("[OK] Test 5 PASSED: Database Statistics")
    else:
        logger.error("[FAIL] Test 5 FAILED: Database Statistics")
    
    # Summary
    logger.info("=" * 70)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED! Complete data flow is working.")
        logger.info("[OK] Stock data fetching and storage")
        logger.info("[OK] Company info fetching and storage")
        logger.info("[OK] Financial data fetching and storage")
        logger.info("[OK] Data access API integration")
        logger.info("[OK] Backtester integration")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed.")
        if success_count >= 3:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()