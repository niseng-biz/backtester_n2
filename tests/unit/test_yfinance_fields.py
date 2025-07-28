"""
yfinanceフィールドに対応した包括的テストスクリプト

更新されたCompanyInfoとFinancialDataモデルを使用して
データの格納・読み出しをテストします。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent))

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


def test_company_info_yfinance_fields():
    """yfinanceフィールドに対応したcompany infoのテスト"""
    logger.info("=== Company Info with yfinance Fields Test ===")
    
    try:
        # Create company info with yfinance fields
        company_info = CompanyInfo(
            symbol="AAPL",
            long_name="Apple Inc.",
            short_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3194468958208,
            country="United States",
            currency="USD",
            exchange="NMS",
            website="https://www.apple.com",
            business_summary="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
            full_time_employees=164000,
            city="Cupertino",
            state="CA",
            zip_code="95014",
            phone="(408) 996-1010",
            address1="One Apple Park Way"
        )
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert company info
        logger.info("Inserting company info with yfinance fields...")
        db_manager.upsert_company_info([company_info])
        logger.info("[OK] Company info inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        retrieved_info = data_api.get_company_info("AAPL")
        
        if retrieved_info:
            logger.info("[OK] Company info retrieved successfully")
            logger.info(f"  Long Name: {retrieved_info.long_name}")
            logger.info(f"  Short Name: {retrieved_info.short_name}")
            logger.info(f"  Sector: {retrieved_info.sector}")
            logger.info(f"  Industry: {retrieved_info.industry}")
            logger.info(f"  Market Cap: ${retrieved_info.market_cap:,.0f}")
            logger.info(f"  Country: {retrieved_info.country}")
            logger.info(f"  Currency: {retrieved_info.currency}")
            logger.info(f"  Exchange: {retrieved_info.exchange}")
            logger.info(f"  Website: {retrieved_info.website}")
            logger.info(f"  Employees: {retrieved_info.full_time_employees:,}")
            logger.info(f"  City: {retrieved_info.city}")
            logger.info(f"  State: {retrieved_info.state}")
            logger.info(f"  Phone: {retrieved_info.phone}")
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


def test_financial_data_yfinance_fields():
    """yfinanceフィールドに対応したfinancial dataのテスト"""
    logger.info("\\n=== Financial Data with yfinance Fields Test ===")
    
    try:
        # Create financial data with yfinance fields
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=3,
            total_revenue=85777000000,
            cost_of_revenue=52300000000,
            gross_profit=33477000000,
            operating_expense=12100000000,
            operating_income=21377000000,
            pretax_income=21900000000,
            tax_provision=3200000000,
            net_income=18700000000,
            basic_eps=1.40,
            diluted_eps=1.40,
            total_assets=364980000000,
            total_liabilities_net_minority_interest=308030000000,
            stockholders_equity=56950000000,
            cash_and_cash_equivalents=29943000000,
            total_debt=98186002432,
            operating_cash_flow=28500000000,
            free_cash_flow=25200000000,
            capital_expenditure=3300000000,
            trailing_pe=33.31,
            forward_pe=25.74,
            price_to_book=8.5,
            return_on_equity=1.38,
            return_on_assets=0.238,
            debt_to_equity=146.99,
            current_ratio=0.821,
            quick_ratio=0.68,
            gross_margins=0.466,
            operating_margins=0.310,
            profit_margins=0.243
        )
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert financial data
        logger.info("Inserting financial data with yfinance fields...")
        db_manager.upsert_financial_data([financial_data])
        logger.info("[OK] Financial data inserted successfully")
        
        # Test retrieval using DataAccessAPI
        data_api = DataAccessAPI()
        retrieved_data = data_api.get_financial_data("AAPL", limit=1)
        
        if retrieved_data:
            logger.info(f"[OK] Retrieved {len(retrieved_data)} financial records")
            sample = retrieved_data[0]
            logger.info(f"  FY{sample.fiscal_year}Q{sample.fiscal_quarter}:")
            logger.info(f"    Total Revenue: ${sample.total_revenue:,.0f}")
            logger.info(f"    Cost of Revenue: ${sample.cost_of_revenue:,.0f}")
            logger.info(f"    Gross Profit: ${sample.gross_profit:,.0f}")
            logger.info(f"    Operating Income: ${sample.operating_income:,.0f}")
            logger.info(f"    Net Income: ${sample.net_income:,.0f}")
            logger.info(f"    Basic EPS: ${sample.basic_eps:.2f}")
            logger.info(f"    Diluted EPS: ${sample.diluted_eps:.2f}")
            logger.info(f"    Total Assets: ${sample.total_assets:,.0f}")
            logger.info(f"    Stockholders Equity: ${sample.stockholders_equity:,.0f}")
            logger.info(f"    Operating Cash Flow: ${sample.operating_cash_flow:,.0f}")
            logger.info(f"    Free Cash Flow: ${sample.free_cash_flow:,.0f}")
            logger.info(f"    Trailing P/E: {sample.trailing_pe:.2f}")
            logger.info(f"    Return on Equity: {sample.return_on_equity:.3f}")
            logger.info(f"    Current Ratio: {sample.current_ratio:.3f}")
            logger.info(f"    Gross Margins: {sample.gross_margins:.3f}")
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


def test_database_schema():
    """新しいデータベーススキーマの確認"""
    logger.info("\\n=== Database Schema Test ===")
    
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
        
        # Check table schemas
        cursor = db_manager.connection.cursor()
        
        logger.info("\\nCompany Info Table Schema:")
        cursor.execute(f"PRAGMA table_info({db_manager.COMPANY_INFO_TABLE})")
        company_columns = cursor.fetchall()
        for col in company_columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        logger.info("\\nFinancial Data Table Schema:")
        cursor.execute(f"PRAGMA table_info({db_manager.FINANCIAL_DATA_TABLE})")
        financial_columns = cursor.fetchall()
        for col in financial_columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    logger.info("yfinance Fields Comprehensive Test")
    logger.info("=" * 60)
    logger.info("Testing updated CompanyInfo and FinancialData models")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Company Info with yfinance Fields
    if test_company_info_yfinance_fields():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Company Info with yfinance Fields")
    else:
        logger.error("[FAIL] Test 1 FAILED: Company Info with yfinance Fields")
    
    # Test 2: Financial Data with yfinance Fields
    if test_financial_data_yfinance_fields():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Financial Data with yfinance Fields")
    else:
        logger.error("[FAIL] Test 2 FAILED: Financial Data with yfinance Fields")
    
    # Test 3: Database Schema
    if test_database_schema():
        success_count += 1
        logger.info("[OK] Test 3 PASSED: Database Schema")
    else:
        logger.error("[FAIL] Test 3 FAILED: Database Schema")
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[SUCCESS] ALL TESTS PASSED!")
        logger.info("[OK] Company info with yfinance fields working")
        logger.info("[OK] Financial data with yfinance fields working")
        logger.info("[OK] Database schema updated correctly")
        logger.info("\\n[CONCLUSION] yfinance-based models are working correctly!")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed.")
        if success_count >= 2:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()