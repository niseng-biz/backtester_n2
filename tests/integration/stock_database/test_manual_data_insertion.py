"""
手動データ挿入テストスクリプト

Yahoo FinanceのAPIエラーを回避して、手動でcompany infoとfinancial dataを
作成してデータベースに格納し、読み出し機能をテストします。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the project root directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager
from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
from stock_database.repositories.data_access_api import DataAccessAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_sample_company_info():
    """サンプルのcompany infoデータを作成"""
    logger.info("=== Creating Sample Company Info ===")
    
    try:
        # Apple Inc.のサンプルデータ
        apple_company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3729000000000,  # $3.729 trillion
            country="US",
            currency="USD",
            exchange="NASDAQ"
        )
        
        # Google/Alphabet Inc.のサンプルデータ
        google_company_info = CompanyInfo(
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            sector="Technology",
            industry="Internet Content & Information",
            market_cap=2100000000000,  # $2.1 trillion
            country="US",
            currency="USD",
            exchange="NASDAQ"
        )
        
        # Microsoft Corp.のサンプルデータ
        microsoft_company_info = CompanyInfo(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            sector="Technology",
            industry="Software—Infrastructure",
            market_cap=3100000000000,  # $3.1 trillion
            country="US",
            currency="USD",
            exchange="NASDAQ"
        )
        
        return [apple_company_info, google_company_info, microsoft_company_info]
        
    except Exception as e:
        logger.error(f"Failed to create sample company info: {e}")
        return []


def create_sample_financial_data():
    """サンプルのfinancial dataを作成"""
    logger.info("=== Creating Sample Financial Data ===")
    
    try:
        financial_data_list = []
        
        # Apple Inc. - 過去4四半期のデータ
        apple_financials = [
            FinancialData(
                symbol="AAPL",
                fiscal_year=2024,
                fiscal_quarter=3,
                revenue=85777000000,  # $85.777B
                net_income=21448000000,  # $21.448B
                total_assets=364980000000,  # $364.98B
                total_liabilities=308030000000,  # $308.03B
                shareholders_equity=56950000000,  # $56.95B
                eps=1.40,
                per=25.3,
                roe=0.377,
                roa=0.059
            ),
            FinancialData(
                symbol="AAPL",
                fiscal_year=2024,
                fiscal_quarter=2,
                revenue=90753000000,  # $90.753B
                net_income=23636000000,  # $23.636B
                total_assets=364980000000,
                total_liabilities=308030000000,
                shareholders_equity=56950000000,
                eps=1.53,
                per=24.8,
                roe=0.415,
                roa=0.065
            ),
            FinancialData(
                symbol="AAPL",
                fiscal_year=2024,
                fiscal_quarter=1,
                revenue=119575000000,  # $119.575B
                net_income=33916000000,  # $33.916B
                total_assets=364980000000,
                total_liabilities=308030000000,
                shareholders_equity=56950000000,
                eps=2.18,
                per=23.5,
                roe=0.596,
                roa=0.093
            ),
            FinancialData(
                symbol="AAPL",
                fiscal_year=2023,
                fiscal_quarter=4,
                revenue=89498000000,  # $89.498B
                net_income=22956000000,  # $22.956B
                total_assets=352755000000,
                total_liabilities=290437000000,
                shareholders_equity=62318000000,
                eps=1.46,
                per=26.1,
                roe=0.368,
                roa=0.065
            )
        ]
        
        # Google/Alphabet Inc. - 過去4四半期のデータ
        google_financials = [
            FinancialData(
                symbol="GOOGL",
                fiscal_year=2024,
                fiscal_quarter=2,
                revenue=84742000000,  # $84.742B
                net_income=23619000000,  # $23.619B
                total_assets=402392000000,  # $402.392B
                total_liabilities=109205000000,  # $109.205B
                shareholders_equity=293187000000,  # $293.187B
                eps=1.89,
                per=22.4,
                roe=0.081,
                roa=0.059
            ),
            FinancialData(
                symbol="GOOGL",
                fiscal_year=2024,
                fiscal_quarter=1,
                revenue=80539000000,  # $80.539B
                net_income=23662000000,  # $23.662B
                total_assets=402392000000,
                total_liabilities=109205000000,
                shareholders_equity=293187000000,
                eps=1.89,
                per=21.8,
                roe=0.081,
                roa=0.059
            )
        ]
        
        # Microsoft Corp. - 過去4四半期のデータ
        microsoft_financials = [
            FinancialData(
                symbol="MSFT",
                fiscal_year=2024,
                fiscal_quarter=4,
                revenue=64728000000,  # $64.728B
                net_income=22036000000,  # $22.036B
                total_assets=512123000000,  # $512.123B
                total_liabilities=198298000000,  # $198.298B
                shareholders_equity=313825000000,  # $313.825B
                eps=2.95,
                per=28.5,
                roe=0.070,
                roa=0.043
            ),
            FinancialData(
                symbol="MSFT",
                fiscal_year=2024,
                fiscal_quarter=3,
                revenue=61858000000,  # $61.858B
                net_income=21939000000,  # $21.939B
                total_assets=512123000000,
                total_liabilities=198298000000,
                shareholders_equity=313825000000,
                eps=2.94,
                per=27.8,
                roe=0.070,
                roa=0.043
            )
        ]
        
        financial_data_list.extend(apple_financials)
        financial_data_list.extend(google_financials)
        financial_data_list.extend(microsoft_financials)
        
        return financial_data_list
        
    except Exception as e:
        logger.error(f"Failed to create sample financial data: {e}")
        return []


def test_company_info_insertion_and_retrieval():
    """Company infoの挿入と読み出しテスト"""
    logger.info("\\n=== Company Info Insertion and Retrieval Test ===")
    
    try:
        # Create sample data
        company_info_list = create_sample_company_info()
        if not company_info_list:
            logger.error("Failed to create sample company info")
            return False
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert company info
        logger.info(f"Inserting {len(company_info_list)} company info records...")
        db_manager.upsert_company_info(company_info_list)
        logger.info("[OK] Company info inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        
        for company_info in company_info_list:
            symbol = company_info.symbol
            logger.info(f"\\nTesting retrieval for {symbol}:")
            
            retrieved_info = data_api.get_company_info(symbol)
            
            if retrieved_info:
                logger.info(f"  [OK] Retrieved company info for {symbol}")
                logger.info(f"    Company: {retrieved_info.company_name}")
                logger.info(f"    Sector: {retrieved_info.sector}")
                logger.info(f"    Industry: {retrieved_info.industry}")
                if retrieved_info.market_cap:
                    logger.info(f"    Market Cap: ${retrieved_info.market_cap:,.0f}")
                if retrieved_info.employees:
                    logger.info(f"    Employees: {retrieved_info.employees:,}")
                logger.info(f"    Website: {retrieved_info.website}")
            else:
                logger.error(f"  [FAIL] Could not retrieve company info for {symbol}")
                return False
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Company info test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_insertion_and_retrieval():
    """Financial dataの挿入と読み出しテスト"""
    logger.info("\\n=== Financial Data Insertion and Retrieval Test ===")
    
    try:
        # Create sample data
        financial_data_list = create_sample_financial_data()
        if not financial_data_list:
            logger.error("Failed to create sample financial data")
            return False
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert financial data
        logger.info(f"Inserting {len(financial_data_list)} financial data records...")
        db_manager.upsert_financial_data(financial_data_list)
        logger.info("[OK] Financial data inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        
        # Test retrieval for each symbol
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for symbol in symbols:
            logger.info(f"\\nTesting financial data retrieval for {symbol}:")
            
            financial_data = data_api.get_financial_data(symbol, limit=5)
            logger.info(f"  Retrieved {len(financial_data)} financial records")
            
            if financial_data:
                logger.info("  Recent financial data:")
                for i, data in enumerate(financial_data[:3]):
                    revenue_str = f"${data.revenue:,.0f}" if data.revenue else "N/A"
                    net_income_str = f"${data.net_income:,.0f}" if data.net_income else "N/A"
                    eps_str = f"${data.eps:.2f}" if data.eps else "N/A"
                    quarter_str = f"Q{data.fiscal_quarter}" if data.fiscal_quarter > 0 else "Annual"
                    logger.info(f"    {i+1}. FY{data.fiscal_year} {quarter_str}:")
                    logger.info(f"       Revenue: {revenue_str}")
                    logger.info(f"       Net Income: {net_income_str}")
                    logger.info(f"       EPS: {eps_str}")
            else:
                logger.warning(f"  [WARN] No financial data found for {symbol}")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Financial data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_data_access():
    """統合データアクセステスト"""
    logger.info("\\n=== Integrated Data Access Test ===")
    
    try:
        data_api = DataAccessAPI()
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for symbol in symbols:
            logger.info(f"\\nTesting integrated data access for {symbol}:")
            
            # Stock data
            stock_data = data_api.get_stock_data(symbol, limit=3)
            logger.info(f"  Stock data: {len(stock_data)} records")
            if stock_data:
                latest_stock = stock_data[0]
                logger.info(f"    Latest: {latest_stock.date.date()} - ${latest_stock.close:.2f}")
            
            # Company info
            company_info = data_api.get_company_info(symbol)
            if company_info:
                logger.info(f"  Company: {company_info.company_name}")
                logger.info(f"    Sector: {company_info.sector}")
                if company_info.market_cap:
                    logger.info(f"    Market Cap: ${company_info.market_cap:,.0f}")
            else:
                logger.warning(f"  No company info for {symbol}")
            
            # Financial data
            financial_data = data_api.get_financial_data(symbol, limit=2)
            logger.info(f"  Financial data: {len(financial_data)} records")
            if financial_data:
                latest_financial = financial_data[0]
                revenue_str = f"${latest_financial.revenue:,.0f}" if latest_financial.revenue else "N/A"
                logger.info(f"    Latest: FY{latest_financial.fiscal_year}Q{latest_financial.fiscal_quarter} - Revenue: {revenue_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"Integrated data access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_statistics():
    """データベース統計の確認"""
    logger.info("\\n=== Database Statistics ===")
    
    try:
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Get database information
        db_info = db_manager.get_database_info()
        
        logger.info("Database Overview:")
        logger.info(f"  Path: {db_info['database_path']}")
        logger.info(f"  Size: {db_info['database_size']:,} bytes ({db_info['database_size']/1024/1024:.2f} MB)")
        
        logger.info("\\nTable Statistics:")
        total_records = 0
        
        for table_name, stats in db_info['table_stats'].items():
            count = stats['count']
            total_records += count
            logger.info(f"  {table_name}: {count:,} records")
        
        logger.info(f"\\nTotal Records: {total_records:,}")
        
        # Data completeness check
        logger.info("\\nData Completeness Check:")
        cursor = db_manager.connection.cursor()
        
        # Check symbols in each table
        cursor.execute("SELECT DISTINCT symbol FROM stock_data")
        stock_symbols = {row[0] for row in cursor.fetchall()}
        logger.info(f"  Symbols with stock data: {len(stock_symbols)}")
        
        cursor.execute("SELECT DISTINCT symbol FROM company_info")
        company_symbols = {row[0] for row in cursor.fetchall()}
        logger.info(f"  Symbols with company info: {len(company_symbols)}")
        
        cursor.execute("SELECT DISTINCT symbol FROM financial_data")
        financial_symbols = {row[0] for row in cursor.fetchall()}
        logger.info(f"  Symbols with financial data: {len(financial_symbols)}")
        
        # Show completeness
        all_symbols = stock_symbols | company_symbols | financial_symbols
        logger.info(f"  Total unique symbols: {len(all_symbols)}")
        logger.info(f"  Symbols: {', '.join(sorted(all_symbols))}")
        
        complete_symbols = stock_symbols & company_symbols & financial_symbols
        logger.info(f"  Complete data (all 3 types): {len(complete_symbols)} symbols")
        if complete_symbols:
            logger.info(f"    Complete symbols: {', '.join(sorted(complete_symbols))}")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database statistics failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    logger.info("Manual Data Insertion and Retrieval Test")
    logger.info("=" * 60)
    logger.info("Testing: Manual Data -> SQLite -> DataAccessAPI")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 4
    
    # Test 1: Company Info Insertion and Retrieval
    if test_company_info_insertion_and_retrieval():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Company Info Insertion and Retrieval")
    else:
        logger.error("[FAIL] Test 1 FAILED: Company Info Insertion and Retrieval")
    
    # Test 2: Financial Data Insertion and Retrieval
    if test_financial_data_insertion_and_retrieval():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Financial Data Insertion and Retrieval")
    else:
        logger.error("[FAIL] Test 2 FAILED: Financial Data Insertion and Retrieval")
    
    # Test 3: Integrated Data Access
    if test_integrated_data_access():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Integrated Data Access")
    else:
        logger.error("[FAIL] Test 3 FAILED: Integrated Data Access")
    
    # Test 4: Database Statistics
    if test_database_statistics():
        success_count += 1
        logger.info("[OK] Test 4 PASSED: Database Statistics")
    else:
        logger.error("[FAIL] Test 4 FAILED: Database Statistics")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED! Manual data insertion and retrieval working correctly.")
        logger.info("[OK] Company info storage and retrieval")
        logger.info("[OK] Financial data storage and retrieval")
        logger.info("[OK] Integrated data access")
        logger.info("[OK] Database statistics")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed.")
        if success_count >= 2:
            logger.info("[INFO] Core storage and retrieval functionality is working.")


if __name__ == "__main__":
    main()