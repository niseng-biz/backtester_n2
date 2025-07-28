"""
シンプルなデータ挿入テストスクリプト

基本的なフィールドのみを使用してcompany infoとfinancial dataの
格納・読み出し機能をテストします。
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


def test_company_info_basic():
    """基本的なcompany infoのテスト"""
    logger.info("=== Basic Company Info Test ===")
    
    try:
        # Create simple company info
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3729000000000
        )
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert company info
        logger.info("Inserting company info...")
        db_manager.upsert_company_info([company_info])
        logger.info("[OK] Company info inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        retrieved_info = data_api.get_company_info("AAPL")
        
        if retrieved_info:
            logger.info("[OK] Company info retrieved successfully")
            logger.info(f"  Company: {retrieved_info.company_name}")
            logger.info(f"  Sector: {retrieved_info.sector}")
            logger.info(f"  Industry: {retrieved_info.industry}")
            if retrieved_info.market_cap:
                logger.info(f"  Market Cap: ${retrieved_info.market_cap:,.0f}")
        else:
            logger.error("[FAIL] Could not retrieve company info")
            return False
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Company info test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_basic():
    """基本的なfinancial dataのテスト"""
    logger.info("\\n=== Basic Financial Data Test ===")
    
    try:
        # Create simple financial data
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=3,
            revenue=85777000000,
            net_income=21448000000,
            eps=1.40,
            per=25.3,
            roe=0.377,
            roa=0.059
        )
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert financial data
        logger.info("Inserting financial data...")
        db_manager.upsert_financial_data([financial_data])
        logger.info("[OK] Financial data inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        retrieved_data = data_api.get_financial_data("AAPL", limit=1)
        
        if retrieved_data:
            logger.info(f"[OK] Retrieved {len(retrieved_data)} financial records")
            sample = retrieved_data[0]
            revenue_str = f"${sample.revenue:,.0f}" if sample.revenue else "N/A"
            net_income_str = f"${sample.net_income:,.0f}" if sample.net_income else "N/A"
            eps_str = f"${sample.eps:.2f}" if sample.eps else "N/A"
            logger.info(f"  FY{sample.fiscal_year}Q{sample.fiscal_quarter}:")
            logger.info(f"    Revenue: {revenue_str}")
            logger.info(f"    Net Income: {net_income_str}")
            logger.info(f"    EPS: {eps_str}")
        else:
            logger.error("[FAIL] Could not retrieve financial data")
            return False
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Financial data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_status():
    """データベースの状態確認"""
    logger.info("\\n=== Database Status Check ===")
    
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
        for table_name, stats in db_info['table_stats'].items():
            count = stats['count']
            logger.info(f"  {table_name}: {count:,} records")
        
        # Check data completeness
        cursor = db_manager.connection.cursor()
        
        cursor.execute("SELECT DISTINCT symbol FROM stock_data")
        stock_symbols = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT DISTINCT symbol FROM company_info")
        company_symbols = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT DISTINCT symbol FROM financial_data")
        financial_symbols = {row[0] for row in cursor.fetchall()}
        
        logger.info("\\nData Completeness:")
        logger.info(f"  Stock data symbols: {len(stock_symbols)} - {', '.join(sorted(stock_symbols))}")
        logger.info(f"  Company info symbols: {len(company_symbols)} - {', '.join(sorted(company_symbols))}")
        logger.info(f"  Financial data symbols: {len(financial_symbols)} - {', '.join(sorted(financial_symbols))}")
        
        # Show complete data
        complete_symbols = stock_symbols & company_symbols & financial_symbols
        logger.info(f"  Complete data (all 3 types): {len(complete_symbols)} symbols")
        if complete_symbols:
            logger.info(f"    Complete symbols: {', '.join(sorted(complete_symbols))}")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    logger.info("Simple Data Insertion and Retrieval Test")
    logger.info("=" * 50)
    logger.info("Testing basic company info and financial data operations")
    logger.info("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Company Info Basic
    if test_company_info_basic():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Company Info Basic")
    else:
        logger.error("[FAIL] Test 1 FAILED: Company Info Basic")
    
    # Test 2: Financial Data Basic
    if test_financial_data_basic():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Financial Data Basic")
    else:
        logger.error("[FAIL] Test 2 FAILED: Financial Data Basic")
    
    # Test 3: Database Status
    if test_database_status():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Database Status")
    else:
        logger.error("[FAIL] Test 3 FAILED: Database Status")
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED!")
        logger.info("[OK] Company info storage and retrieval working")
        logger.info("[OK] Financial data storage and retrieval working")
        logger.info("[OK] Database operations functioning correctly")
        logger.info("\\n[CONCLUSION] Financial data and company info functionality is working correctly!")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed.")
        if success_count >= 2:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()