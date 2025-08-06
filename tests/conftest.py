"""
Pytest configuration and fixtures for backtester tests.
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from backtester.crypto_data_reader import CryptoDataReader
from backtester.models import LotConfig, LotSizeMode, MarketData
from stock_database.config import ConfigManager, get_config_manager
from stock_database.database_factory import DatabaseManager
from stock_database.sqlite_database import SQLiteManager


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    base_date = datetime(2023, 1, 1)
    data = []
    
    for i in range(100):
        timestamp = base_date + timedelta(days=i)
        price = 100 + (i % 20) - 10  # Simple price variation
        data.append(MarketData(
            timestamp=timestamp,
            open=price,
            high=price + 2,
            low=price - 2,
            close=price + 1,
            volume=1000 + (i % 500)
        ))
    
    return data


@pytest.fixture
def standard_lot_configs():
    """Create standard LOT configurations for all asset types."""
    return LotConfig.create_standard_configs()


@pytest.fixture
def crypto_lot_config(standard_lot_configs):
    """Create a standard crypto LOT configuration for testing."""
    return standard_lot_configs['crypto']


@pytest.fixture
def stock_lot_config(standard_lot_configs):
    """Create a standard stock LOT configuration for testing."""
    return standard_lot_configs['stock']


@pytest.fixture
def forex_lot_config(standard_lot_configs):
    """Create a standard forex LOT configuration for testing."""
    return standard_lot_configs['forex']


@pytest.fixture
def fixed_lot_config():
    """Create a fixed LOT configuration for testing."""
    config = LotConfig.create_standard_configs()['crypto']
    config.lot_size_mode = LotSizeMode.FIXED
    return config


@pytest.fixture
def sample_csv_data(tmp_path):
    """Create a temporary CSV file with sample data."""
    csv_file = tmp_path / "test_data.csv"
    
    # Create sample data
    data = []
    base_timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
    
    for i in range(50):
        timestamp = base_timestamp + (i * 86400)  # Daily data
        price = 40000 + (i % 10) * 1000  # Price variation
        data.append({
            'timestamp': timestamp,
            'open': price,
            'high': price + 500,
            'low': price - 500,
            'close': price + 200,
            'volume': 100 + (i % 50)
        })
    
    # Write to CSV
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    
    return str(csv_file)


@pytest.fixture
def data_reader():
    """Create a data reader instance for testing."""
    return CryptoDataReader()


@pytest.fixture
def config_manager():
    """Create a configuration manager instance for testing."""
    return get_config_manager()


@pytest.fixture
def sqlite_db_manager(config_manager):
    """Create a SQLite database manager instance for testing."""
    manager = SQLiteManager(config_manager)
    yield manager
    # Cleanup: disconnect if connected
    if hasattr(manager, '_connected') and manager._connected:
        manager.disconnect()


@pytest.fixture
def database_manager(config_manager):
    """Create a database manager instance for testing."""
    manager = DatabaseManager(config_manager)
    yield manager
    # Cleanup: disconnect if connected
    if hasattr(manager, '_connected') and manager._connected:
        manager.disconnect()


# Additional test data generation helpers
def create_sample_stock_data_list(symbol="AAPL", count=5, start_date=None):
    """Helper function to create a list of sample StockData objects."""
    from stock_database.models.stock_data import StockData
    
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    
    data_list = []
    for i in range(count):
        date = start_date + timedelta(days=i)
        price = 150.0 + i
        data_list.append(StockData(
            symbol=symbol,
            date=date,
            open=price,
            high=price + 5.0,
            low=price - 5.0,
            close=price + 2.0,
            volume=1000000 + i * 1000,
            adjusted_close=price + 2.0
        ))
    
    return data_list


def create_sample_financial_data_list(symbol="AAPL", count=3, start_year=2022):
    """Helper function to create a list of sample FinancialData objects."""
    from stock_database.models.financial_data import FinancialData
    
    data_list = []
    for i in range(count):
        year = start_year + i
        revenue = 100000000000 + i * 10000000000
        data_list.append(FinancialData(
            symbol=symbol,
            fiscal_year=year,
            revenue=revenue,
            net_income=revenue * 0.25,
            eps=6.0 + i * 0.5
        ))
    
    return data_list


def create_sample_company_info(symbol="AAPL", company_name="Apple Inc."):
    """Helper function to create sample CompanyInfo object."""
    from stock_database.models.company_info import CompanyInfo
    
    return CompanyInfo(
        symbol=symbol,
        company_name=company_name,
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000000000,
        country="United States",
        currency="USD",
        exchange="NASDAQ"
    )


@pytest.fixture
def sample_stock_data_list():
    """Create a list of sample StockData objects for testing."""
    return create_sample_stock_data_list()


@pytest.fixture
def sample_financial_data_list():
    """Create a list of sample FinancialData objects for testing."""
    return create_sample_financial_data_list()


@pytest.fixture
def sample_company_info():
    """Create sample CompanyInfo object for testing."""
    return create_sample_company_info()


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager for testing."""
    from unittest.mock import Mock
    
    mock_db = Mock()
    mock_db.STOCK_DATA_COLLECTION = "stock_data"
    mock_db.FINANCIAL_DATA_COLLECTION = "financial_data"
    mock_db.COMPANY_INFO_COLLECTION = "company_info"
    mock_db.upsert_stock_data = Mock()
    mock_db.get_stock_data = Mock()
    mock_db.get_latest_stock_date = Mock()
    mock_db.update_stock_data = Mock()
    mock_db.upsert_financial_data = Mock()
    mock_db.get_financial_data = Mock()
    mock_db.get_collection = Mock()
    mock_db._doc_to_financial_data = Mock()
    mock_db._connected = False
    
    return mock_db


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file with sample market data for testing."""
    csv_file = tmp_path / "test_market_data.csv"
    
    csv_content = """Date,Open,High,Low,Close,Volume
2024-01-01,100.0,105.0,95.0,102.0,1000
2024-01-02,102.0,108.0,100.0,106.0,1200
2024-01-03,106.0,110.0,104.0,108.0,1100
2024-01-04,108.0,112.0,106.0,110.0,1300
2024-01-05,110.0,115.0,108.0,112.0,1400"""
    
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def temp_crypto_csv_file(tmp_path):
    """Create a temporary CSV file with sample crypto data for testing."""
    csv_file = tmp_path / "test_crypto_data.csv"
    
    # Create sample crypto data with Unix timestamps
    base_timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
    csv_content = "timestamp,open,high,low,close,Volume\n"
    
    for i in range(5):
        timestamp = base_timestamp + (i * 86400)  # Daily data
        price = 40000 + (i * 1000)
        csv_content += f"{timestamp},{price},{price + 500},{price - 500},{price + 200},{100 + i * 10}\n"
    
    csv_file.write_text(csv_content)
    return str(csv_file)