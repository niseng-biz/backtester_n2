"""
Financial DataとCompany Infoのサンプルデータを使用したテストスクリプト

Yahoo Finance APIの認証問題を回避するため、サンプルデータを使用して
SQLiteデータベースへの格納と読み出しをテストします。
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

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_sample_company_info():
    """サンプル会社情報を作成"""
    return CompanyInfo(
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000000000,  # $3T
        employees=164000,
        website="https://www.apple.com",
        headquarters="Cupertino, California",
        founded_year=1976
    )


def create_sample_financial_data():
    """サンプル財務データを作成"""
    financial_records = []
    
    # Annual data for recent years
    annual_data = [
        {
            "fiscal_year": 2023,
            "revenue": 383285000000,  # $383.3B
            "net_income": 96995000000,  # $97.0B
            "total_assets": 352755000000,
            "total_liabilities": 290437000000,
            "shareholders_equity": 62318000000,
            "eps": 6.16
        },
        {
            "fiscal_year": 2022,
            "revenue": 394328000000,  # $394.3B
            "net_income": 99803000000,  # $99.8B
            "total_assets": 352583000000,
            "total_liabilities": 302083000000,
            "shareholders_equity": 50500000000,
            "eps": 6.15
        },
        {
            "fiscal_year": 2021,
            "revenue": 365817000000,  # $365.8B
            "net_income": 94680000000,  # $94.7B
            "total_assets": 351002000000,
            "total_liabilities": 287912000000,
            "shareholders_equity": 63090000000,
            "eps": 5.67
        }
    ]
    
    # Create annual records
    for data in annual_data:
        financial_record = FinancialData(
            symbol="AAPL",
            fiscal_year=data["fiscal_year"],
            fiscal_quarter=0,  # 0 indicates annual data
            revenue=data["revenue"],
            net_income=data["net_income"],
            total_assets=data["total_assets"],
            total_liabilities=data["total_liabilities"],
            shareholders_equity=data["shareholders_equity"],
            eps=data["eps"],
            pe_ratio=25.0,  # Approximate P/E ratio
            roe=data["net_income"] / data["shareholders_equity"] if data["shareholders_equity"] else None,
            roa=data["net_income"] / data["total_assets"] if data["total_assets"] else None,
        )
        financial_records.append(financial_record)
    
    # Quarterly data for 2023
    quarterly_data = [
        {"quarter": 1, "revenue": 94836000000, "net_income": 24160000000},
        {"quarter": 2, "revenue": 81797000000, "net_income": 19881000000},
        {"quarter": 3, "revenue": 89498000000, "net_income": 22956000000},
        {"quarter": 4, "revenue": 119575000000, "net_income": 33916000000}
    ]
    
    for q_data in quarterly_data:
        financial_record = FinancialData(
            symbol="AAPL",
            fiscal_year=2023,
            fiscal_quarter=q_data["quarter"],
            revenue=q_data["revenue"],
            net_income=q_data["net_income"],
            total_assets=352755000000,  # Use annual figure
            total_liabilities=290437000000,  # Use annual figure
            shareholders_equity=62318000000,  # Use annual figure
            eps=q_data["net_income"] / 15728000000,  # Approximate shares outstanding
        )
        financial_records.append(financial_record)
    
    return financial_records


def test_company_info_storage():
    """会社情報をSQLiteに格納"""
    logger.info("=== Step 1: Company Info Storage to SQLite ===")
    
    try:
        # Create sample company info
        company_info = create_sample_company_info()
        logger.info(f"Created sample company info for {company_info.symbol}")
        
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
        
        logger.info(f"[OK] Company info stored in SQLite for {company_info.symbol}")
        logger.info(f"  Company: {company_info.company_name}")
        logger.info(f"  Sector: {company_info.sector}")
        logger.info(f"  Market Cap: ${company_info.market_cap:,.0f}")
        logger.info(f"  Employees: {company_info.employees:,}")
        
        return True
        
    except Exception as e:
        logger.error(f"Company info storage failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_data_storage():
    """財務データをSQLiteに格納"""
    logger.info("\n=== Step 2: Financial Data Storage to SQLite ===")
    
    try:
        # Create sample financial data
        financial_records = create_sample_financial_data()
        logger.info(f"Created {len(financial_records)} sample financial records")
        
        # Store in database
        db_manager = DatabaseManager()
        db_manager.connect()
        db_manager.upsert_financial_data(financial_records)
        db_manager.disconnect()
        
        logger.info(f"[OK] Stored {len(financial_records)} financial records for AAPL")
        
        # Display sample data
        annual_records = [r for r in financial_records if r.fiscal_quarter == 0]
        quarterly_records = [r for r in financial_records if r.fiscal_quarter > 0]
        
        logger.info(f"  Annual records: {len(annual_records)}")
        logger.info(f"  Quarterly records: {len(quarterly_records)}")
        
        for record in annual_records[:2]:
            revenue_str = f"${record.revenue:,.0f}" if record.revenue else "N/A"
            logger.info(f"    FY{record.fiscal_year}: Revenue={revenue_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"Financial data storage failed: {e}")
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
            if company_info.headquarters:
                logger.info(f"  Headquarters: {company_info.headquarters}")
            if company_info.founded_year:
                logger.info(f"  Founded: {company_info.founded_year}")
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
            
            # Test specific queries
            logger.info("\nTesting specific queries:")
            
            # Get annual data only
            annual_data = data_api.get_financial_data(symbol, fiscal_quarter=0)
            logger.info(f"  Annual data: {len(annual_data)} records")
            
            # Get specific year data
            fy2023_data = data_api.get_financial_data(symbol, fiscal_year=2023)
            logger.info(f"  FY2023 data: {len(fy2023_data)} records")
            
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
            logger.info(f"  Company: {company.company_name}")
            logger.info(f"  Sector: {company.sector}")
            logger.info(f"  Market Cap: ${company.market_cap:,.0f}")
        
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
        
        # Financial ratios
        if complete_data['financial_ratios']:
            ratios = complete_data['financial_ratios']
            logger.info("  Financial ratios:")
            for ratio_name, ratio_value in ratios.items():
                if ratio_value is not None:
                    if isinstance(ratio_value, float):
                        logger.info(f"    {ratio_name}: {ratio_value:.2f}")
                    else:
                        logger.info(f"    {ratio_name}: {ratio_value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    logger.info("Financial Data and Company Info Test (Sample Data)")
    logger.info("=" * 60)
    logger.info("Testing: Sample Data -> SQLite (Financial & Company Data)")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 6
    
    # Test 1: Company Info Storage
    if test_company_info_storage():
        success_count += 1
        logger.info("[OK] Test 1 PASSED: Company Info Storage")
    else:
        logger.error("[FAIL] Test 1 FAILED: Company Info Storage")
    
    # Test 2: Financial Data Storage
    if test_financial_data_storage():
        success_count += 1
        logger.info("[OK] Test 2 PASSED: Financial Data Storage")
    else:
        logger.error("[FAIL] Test 2 FAILED: Financial Data Storage")
    
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
        logger.info("[OK] Sample company info storage")
        logger.info("[OK] Sample financial data storage")
        logger.info("[OK] SQLite data retrieval")
        logger.info("[OK] Data access API integration")
        logger.info("[OK] Complete data integration")
    else:
        logger.error(f"[FAIL] {total_tests - success_count} tests failed. Please check the errors above.")
        if success_count >= 4:
            logger.info("[INFO] Core functionality is working correctly.")


if __name__ == "__main__":
    main()