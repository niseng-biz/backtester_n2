"""
Pytest configuration and fixtures for backtester tests.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from backtester.models import MarketData, LotConfig, LotSizeMode
from backtester.crypto_data_reader import CryptoDataReader


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
def crypto_lot_config():
    """Create a standard crypto LOT configuration for testing."""
    return LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01,
        lot_size_mode=LotSizeMode.VARIABLE,
        capital_percentage=0.8,
        max_lot_size=10.0
    )


@pytest.fixture
def fixed_lot_config():
    """Create a fixed LOT configuration for testing."""
    return LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01,
        lot_size_mode=LotSizeMode.FIXED
    )


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