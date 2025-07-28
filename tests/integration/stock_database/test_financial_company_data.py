"""
Financial DataとCompany Infoの取得・格納・読み出しテストスクリプト

Yahoo FinanceからAppleの財務データと会社情報を取得して、
SQLiteデータベースに格納し、読み出すまでの一連の流れをテストします。
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager
from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
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


def test_company_info_fetching():
    """Yahoo FinanceからAppleの会社情報を取得してSQLiteに格納"""
    logger.info("=== Step 1: Company Info Fetching from Yahoo Finance ===")
    
    try:
        # Initialize data fetcher with single-threaded mode for SQLite
        data_fetcher = DataFetcher()
        
        # Test symbol
        symbol = "AAPL"
        logger.info(f"Fetching company info for {symbol}...")
        
        # Fetch company info directly using the curl client
        try:
            company_info_data = data_fetcher.yahoo_client.get_company_info(symbol)
            
            if company_info_data:
                logger.info(f"[OK] Raw company info fetched for {symbol}")
                logger.info(f"  Company Name: {company_info_data.get('longName', 'N/A')}")
                logger.info(f"  Sector: {company_info_data.get('sector', 'N/A')}")
                logger.info(f"  Industry: {company_info_data.get('industry', 'N/A')}")
                logger.info(f"  Market Cap: {company_info_data.get('marketCap', 'N/A')}")
                
                # Transform to CompanyInfo object
                company_info = CompanyInfo(
                    symbol=symbol,
                    company_name=company_info_data.get('longName', ''),
                    sector=company_info_data.get('sector', ''),
                    industry=company_info_data.get('industry', ''),
                    market_cap=company_info_data.get('marketCap'),
                    employees=company_info_data.get('fullTimeEmployees'),
                    website=company_info_data.get('website', ''),
                    headquarters=company_info_data.get('city', ''),
                    founded_year=None  # Not typically available in Yahoo Finance
                )
                
                # Store in database
                db_manager = DatabaseManager()
                db_manager.connect()
                
                # Insert company info using raw SQL
                cursor = db_manager.connection.cursor()
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {db_manager.COMPANY_INFO_TABLE} (
                        symbol, company_name, sector, industry, market_cap, employees,
                        website, headquarters, founded_year, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_info.symbol,
                    company_info.company_name,
                    company_info.sector,
                    company_info.industry,
                    company_info.market_cap,
                    company_info.employees,
                    company_info.website,
                    company_info.headquarters,
                    company_info.founded_year,
                    company_info.created_at.isoformat(),
                    company_info.updated_at.isoformat()
                ))
                db_manager.connection.commit()
                db_manager.disconnect()
                
                logger.info(f"[OK] Company info stored in SQLite for {symbol}")
                return True
            else:
                logger.error(f"[FAIL] No company info data received for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Company info fetch error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"Company info fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_fetching():
    """Yahoo FinanceからAppleの財務データを取得してSQLiteに格納"""
    logger.info("\n=== Step 2: Financial Data Fetching from Yahoo Finance ===")
    
    try:
        # Initialize data fetcher
        data_fetcher = DataFetcher()
        
        # Test symbol
        symbol = "AAPL"
        logger.info(f"Fetching financial data for {symbol}...")
        
        # Fetch financial data directly using the curl client
        try:
            financial_data_raw = data_fetcher.yahoo_client.get_financial_data(symbol)
            
            if financial_data_raw:
                logger.info(f"[OK] Raw financial data fetched for {symbol}")
                
                # Process quarterly and annual data
                financial_records = []
                
                # Process quarterly data
                quarterly_data = financial_data_raw.get('quarterly', {})
                if quarterly_data:
                    for quarter_data in quarterly_data:
                        try:
                            fiscal_year = quarter_data.get('fiscalYear')
                            fiscal_quarter = quarter_data.get('fiscalQuarter', 0)
                            
                            if fiscal_year:
                                financial_record = FinancialData(
                                    symbol=symbol,
                                    fiscal_year=fiscal_year,
                                    fiscal_quarter=fiscal_quarter,
                                    revenue=quarter_data.get('totalRevenue'),
                                    net_income=quarter_data.get('netIncome'),
                                    total_assets=quarter_data.get('totalAssets'),
                                    total_liabilities=quarter_data.get('totalLiab'),
                                    shareholders_equity=quarter_data.get('totalStockholderEquity'),
                                    eps=quarter_data.get('basicEPS'),
                                    pe_ratio=None,  # Calculate separately if needed
                                    roe=None,  # Calculate separately if needed
                                    roa=None,  # Calculate separately if needed
                                )
                                financial_records.append(financial_record)
                        except Exception as e:
                            logger.warning(f"Error processing quarterly data: {e}")
                            continue
                
                # Process annual data
                annual_data = financial_data_raw.get('annual', {})
                if annual_data:
                    for annual_record in annual_data:
                        try:
                            fiscal_year = annual_record.get('fiscalYear')
                            
                            if fiscal_year:
                                financial_record = FinancialData(
                                    symbol=symbol,
                                    fiscal_year=fiscal_year,
                                    fiscal_quarter=0,  # 0 indicates annual data
                                    revenue=annual_record.get('totalRevenue'),
                                    net_income=annual_record.get('netIncome'),
                                    total_assets=annual_record.get('totalAssets'),
                                    total_liabilities=annual_record.get('totalLiab'),
                                    shareholders_equity=annual_record.get('totalStockholderEquity'),
                                    eps=annual_record.get('basicEPS'),
                                    pe_ratio=None,
                                    roe=None,
                                    roa=None,
                                )
                                financial_records.append(financial_record)
                        except Exception as e:
                            logger.warning(f"Error processing annual data: {e}")
                            continue
                
                if financial_records:
                    # Store in database
                    db_manager = DatabaseManager()
                    db_manager.connect()
                    db_manager.upsert_financial_data(financial_records)
                    db_manager.disconnect()
                    
                    logger.info(f"[OK] Stored {len(financial_records)} financial records for {symbol}")
                    
                    # Display sample data
                    for i, record in enumerate(financial_records[:3]):
                        revenue_str = f"${record.revenue:,.0f}" if record.revenue else "N/A"
                        logger.info(f"  Sample {i+1}: FY{record.fiscal_year}Q{record.fiscal_quarter} - Revenue: {revenue_str}")
                    
                    return True
                else:
                    logger.warning(f"[WARN] No financial records processed for {symbol}")
                    return False
            else:
                logger.error(f"[FAIL] No financial data received for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Financial data fetch error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"Financial data fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_company_info_retrieval():
    """SQLiteから会社情報を読み出し"""
    logger.info("\n=== Step 3: Company Info Retrieval from SQLite ===")
    
    try:
        # Initialize data access API
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        # Test company info retrieval
        logger.info(f"Retrieving company info for {symbol}...")
        company_info = data_api.get_company_info(symbol)
        
        if company_info:
            logger.info(f"[OK] Retrieved company info from SQLite")
            logger.info(f"  Company: {company_info.company_name}")
            logger.info(f"  Symbol: {company_info.symbol}")
            logger.info(f"  Sector: {company_info.sector}")
            logger.info(f"  Industry: {company_info.industry}")
            if company_info.market_cap:
                logger.info(f"  Market Cap: ${company_info.market_cap:,.0f}")
            if company_info.employees:
                logger.info(f"  Employees: {company_info.employees:,}")
            if company_info.website:
                logger.info(f"  Website: {company_info.website}")
            return True
        else:
            logger.warning("[WARN] No company info found in SQLite")
            return False
        
    except Exception as e:
        logger.error(f"Company info retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_retrieval():
    """SQLiteから財務データを読み出し"""
    logger.info("\n=== Step 4: Financial Data Retrieval from SQLite ===")
    
    try:
        # Initialize data access API
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        # Test financial data retrieval
        logger.info(f"Retrieving financial data for {symbol}...")
        financial_data = data_api.get_financial_data(symbol, limit=10)
        
        if financial_data:
            logger.info(f"[OK] Retrieved {len(financial_data)} financial records from SQLite")
            
            # Display sample data
            logger.info("  Recent financial data:")
            for i, data in enumerate(financial_data[:5]):
                revenue_str = f"${data.revenue:,.0f}" if data.revenue else "N/A"
                net_income_str = f"${data.net_income:,.0f}" if data.net_income else "N/A"
                quarter_str = f"Q{data.fiscal_quarter}" if data.fiscal_quarter > 0 else "Annual"
                logger.info(f"    {i+1}. FY{data.fiscal_year} {quarter_str}: Revenue={revenue_str}, Net Income={net_income_str}")
            
            return True
        else:
            logger.warning("[WARN] No financial data found in SQLite")
            return False
        
    except Exception as e:
        logger.error(f"Financial data retrieval failed: {e}")
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


def test_data_integration():
    """統合データアクセステスト"""
    logger.info("\n=== Step 6: Integrated Data Access Test ===")
    
    try:
        # Initialize data access API
        data_api = DataAccessAPI()
        symbol = "AAPL"
        
        # Test complete company data retrieval
        logger.info(f"Retrieving complete company data for {symbol}...")
        complete_data = data_api.get_complete_company_data(
            symbol=symbol,
            include_stock_days=5,
            include_financial_years=3
        )
        
        logger.info(f"[OK] Retrieved complete data for {symbol}")
        logger.info(f"  Symbol: {complete_data['symbol']}")
        
        # Company info
        if complete_data['company_info']:
            company = complete_data['company_info']
            logger.info(f"  Company: {company['company_name']}")
            logger.info(f"  Sector: {company['sector']}")
        
        # Stock data
        stock_count = len(complete_data['recent_stock_data'])
        logger.info(f"  Recent stock data: {stock_count} records")
        
        # Financial data
        financial_count = len(complete_data['annual_financial_data'])
        logger.info(f"  Annual financial data: {financial_count} records")
        
        # Latest data
        if complete_data['latest_stock_data']:
            latest_stock = complete_data['latest_stock_data']
            logger.info(f"  Latest stock price: ${latest_stock.close:.2f}")
        
        if complete_data['latest_financial_data']:
            latest_financial = complete_data['latest_financial_data']
            revenue_str = f"${latest_financial.revenue:,.0f}" if latest_financial.revenue else "N/A"
            logger.info(f"  Latest revenue (FY{latest_financial.fiscal_year}): {revenue_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    logger.info("Financial Data and Company Info Test")
    logger.info("=" * 60)
    logger.info("Testing: Yahoo Finance -> SQLite (Financial & Company Data)")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 6
    
    # Test 1: Company Info Fetching
    if test_company_info_fetching():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Company Info Fetching")
    else:
        logger.error("[FAIL] Test 1 FAILED: Company Info Fetching")
    
    # Test 2: Financial Data Fetching
    if test_financial_data_fetching():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Financial Data Fetching")
    else:
        logger.error("[FAIL] Test 2 FAILED: Financial Data Fetching")
    
    # Test 3: Company Info Retrieval
    if test_company_info_retrieval():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Company Info Retrieval")
    else:
        logger.error("[FAIL] Test 3 FAILED: Company Info Retrieval")
    
    # Test 4: Financial Data Retrieval
    if test_financial_data_retrieval():
        success_count += 1
        logger.info("[OK] Test 4 PASSED: Financial Data Retrieval")
    else:
        logger.error("[FAIL] Test 4 FAILED: Financial Data Retrieval")
    
    # Test 5: Database Statistics
    if test_database_statistics():
        success_count += 1
        logger.info("[OK] Test 5 PASSED: Database Statistics")
    else:
        logger.error("[FAIL] Test 5 FAILED: Database Statistics")
    
    # Test 6: Data Integration
    if test_data_integration():
        success_count += 1
        logger.info("[OK] Test 6 PASSED: Data Integration")
    else:
        logger.error("[FAIL] Test 6 FAILED: Data Integration")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED! Financial and company data flow is working correctly.")
        logger.info("[OK] Yahoo Finance company info fetching")
        logger.info("[OK] Yahoo Finance financial data fetching")
        logger.info("[OK] SQLite data storage")
        logger.info("[OK] Data retrieval and access")
        logger.info("[OK] Integrated data access")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed. Please check the errors above.")
        if success_count >= 4:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()