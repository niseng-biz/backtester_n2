"""
MongoDB Atlas database setup script.

This script initializes the MongoDB Atlas database with proper collections,
indexes, and sample data for the stock database system.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent))

from stock_database.config import get_config_manager
from stock_database.sqlite_database import SQLiteManager
from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
from stock_database.models.stock_data import StockData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """Set up MongoDB Atlas database with collections and indexes."""
    try:
        logger.info("Starting MongoDB Atlas database setup...")
        
        # Initialize configuration and database manager
        config = get_config_manager()
        db_manager = SQLiteManager(config)
        
        # Test connection
        logger.info("Testing MongoDB Atlas connection...")
        db_manager.connect()
        
        if not db_manager.is_connected():
            raise Exception("Failed to connect to MongoDB Atlas")
        
        logger.info("✓ Successfully connected to MongoDB Atlas")
        
        # Create indexes for optimal performance
        logger.info("Creating database indexes...")
        db_manager.create_indexes()
        logger.info("✓ Database indexes created successfully")
        
        # Get database information
        db_info = db_manager.get_database_info()
        logger.info(f"✓ Database '{db_info['database_name']}' initialized")
        logger.info(f"  Collections: {db_info['collection_count']}")
        logger.info(f"  Data size: {db_info['data_size']} bytes")
        
        # Display collection information
        for collection_name, stats in db_info['collection_stats'].items():
            if 'error' not in stats:
                logger.info(f"  {collection_name}: {stats['count']} documents, {stats['indexes']} indexes")
        
        logger.info("MongoDB Atlas database setup completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def create_sample_data():
    """Create sample data for testing purposes."""
    try:
        logger.info("Creating sample data...")
        
        config = get_config_manager()
        db_manager = SQLiteManager(config)
        db_manager.connect()
        
        # Sample company information
        sample_companies = [
            CompanyInfo(
                symbol="AAPL",
                company_name="Apple Inc.",
                sector="Technology",
                industry="Consumer Electronics",
                market_cap=3000000000000,  # $3T
                description="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
            ),
            CompanyInfo(
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                sector="Technology",
                industry="Internet Content & Information",
                market_cap=1800000000000,  # $1.8T
                description="Alphabet Inc. provides online advertising services in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America."
            ),
            CompanyInfo(
                symbol="MSFT",
                company_name="Microsoft Corporation",
                sector="Technology",
                industry="Software—Infrastructure",
                market_cap=2800000000000,  # $2.8T
                description="Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide."
            ),
            CompanyInfo(
                symbol="TSLA",
                company_name="Tesla, Inc.",
                sector="Consumer Cyclical",
                industry="Auto Manufacturers",
                market_cap=800000000000,  # $800B
                description="Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems."
            )
        ]
        
        # Insert sample company data
        for company in sample_companies:
            try:
                collection = db_manager.get_collection(db_manager.COMPANY_INFO_COLLECTION)
                doc = company.to_dict()
                collection.replace_one(
                    {"symbol": company.symbol},
                    doc,
                    upsert=True
                )
                logger.info(f"✓ Created sample company data for {company.symbol}")
            except Exception as e:
                logger.warning(f"Failed to create company data for {company.symbol}: {e}")
        
        # Sample stock data (last 30 days)
        base_date = datetime.now() - timedelta(days=30)
        sample_stock_data = []
        
        for company in sample_companies:
            symbol = company.symbol
            base_price = {"AAPL": 180, "GOOGL": 140, "MSFT": 350, "TSLA": 250}[symbol]
            
            for i in range(30):
                date = base_date + timedelta(days=i)
                # Skip weekends
                if date.weekday() >= 5:
                    continue
                
                # Generate realistic price data with some volatility
                price_change = (i % 7 - 3) * 2  # Simple price variation
                open_price = base_price + price_change
                high_price = open_price + abs(price_change) + 2
                low_price = open_price - abs(price_change) - 1
                close_price = open_price + (price_change * 0.5)
                volume = 1000000 + (i * 10000)
                
                stock_data = StockData(
                    symbol=symbol,
                    date=date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                    adjusted_close=close_price
                )
                sample_stock_data.append(stock_data)
        
        # Insert sample stock data
        if sample_stock_data:
            db_manager.upsert_stock_data(sample_stock_data)
            logger.info(f"✓ Created {len(sample_stock_data)} sample stock data records")
        
        # Sample financial data
        sample_financial_data = []
        for company in sample_companies:
            symbol = company.symbol
            base_revenue = {"AAPL": 400000000000, "GOOGL": 280000000000, "MSFT": 200000000000, "TSLA": 80000000000}[symbol]
            
            # Create data for last 2 fiscal years
            for year in [2023, 2024]:
                financial_data = FinancialData(
                    symbol=symbol,
                    fiscal_year=year,
                    fiscal_quarter=0,  # Annual data
                    revenue=base_revenue + (year - 2023) * 10000000000,
                    net_income=base_revenue * 0.2,
                    total_assets=base_revenue * 2,
                    total_liabilities=base_revenue * 0.8,
                    shareholders_equity=base_revenue * 1.2,
                    eps=15.0 + (year - 2023) * 2,
                    pe_ratio=25.0,
                    roe=0.18,
                    roa=0.12
                )
                sample_financial_data.append(financial_data)
        
        # Insert sample financial data
        if sample_financial_data:
            db_manager.upsert_financial_data(sample_financial_data)
            logger.info(f"✓ Created {len(sample_financial_data)} sample financial data records")
        
        logger.info("Sample data creation completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def verify_setup():
    """Verify that the database setup was successful."""
    try:
        logger.info("Verifying database setup...")
        
        config = get_config_manager()
        db_manager = SQLiteManager(config)
        db_manager.connect()
        
        # Get database information
        db_info = db_manager.get_database_info()
        
        logger.info("Database verification results:")
        logger.info(f"  Database: {db_info['database_name']}")
        logger.info(f"  Collections: {db_info['collection_count']}")
        
        # Check each collection
        expected_collections = [
            db_manager.STOCK_DATA_COLLECTION,
            db_manager.FINANCIAL_DATA_COLLECTION,
            db_manager.COMPANY_INFO_COLLECTION
        ]
        
        for collection_name in expected_collections:
            if collection_name in db_info['collection_stats']:
                stats = db_info['collection_stats'][collection_name]
                if 'error' not in stats:
                    logger.info(f"  ✓ {collection_name}: {stats['count']} documents, {stats['indexes']} indexes")
                else:
                    logger.warning(f"  ⚠ {collection_name}: {stats['error']}")
            else:
                logger.warning(f"  ⚠ {collection_name}: Collection not found")
        
        # Test basic operations
        logger.info("Testing basic database operations...")
        
        # Test stock data retrieval
        stock_data = db_manager.get_stock_data("AAPL", limit=5)
        logger.info(f"  ✓ Stock data query: Retrieved {len(stock_data)} records for AAPL")
        
        # Test financial data retrieval
        financial_data = db_manager.get_financial_data("AAPL", fiscal_year=2024)
        logger.info(f"  ✓ Financial data query: Retrieved {len(financial_data)} records for AAPL 2024")
        
        logger.info("✓ Database verification completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def main():
    """Main setup function."""
    logger.info("MongoDB Atlas Database Setup")
    logger.info("=" * 50)
    
    success = True
    
    # Step 1: Setup database structure
    if not setup_database():
        logger.error("Database setup failed!")
        success = False
    
    # Step 2: Create sample data
    if success:
        if not create_sample_data():
            logger.warning("Sample data creation failed, but database setup was successful")
    
    # Step 3: Verify setup
    if success:
        if not verify_setup():
            logger.warning("Database verification had issues, but setup may still be functional")
    
    if success:
        logger.info("=" * 50)
        logger.info("✓ MongoDB Atlas setup completed successfully!")
        logger.info("Your database is ready for use.")
    else:
        logger.error("=" * 50)
        logger.error("✗ MongoDB Atlas setup failed!")
        logger.error("Please check the error messages above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()