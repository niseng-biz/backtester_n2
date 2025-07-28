"""
Unit tests for BacktesterDataAdapter.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from stock_database.adapters.backtester_adapter import (BacktesterDataAdapter,
                                                        MarketData)
from stock_database.models.stock_data import StockData


class TestBacktesterDataAdapter:
    """Test cases for BacktesterDataAdapter."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        return Mock()
    
    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data for testing."""
        base_date = datetime(2024, 1, 1)
        return [
            StockData(
                symbol="AAPL",
                date=base_date + timedelta(days=i),
                open=150.0 + i,
                high=155.0 + i,
                low=149.0 + i,
                close=154.0 + i,
                volume=1000000 + i * 1000,
                adjusted_close=154.0 + i
            )
            for i in range(5)
        ]
    
    @pytest.fixture
    def adapter(self, mock_db_manager):
        """Create a BacktesterDataAdapter instance."""
        with patch('stock_database.adapters.backtester_adapter.DataAccessAPI'):
            return BacktesterDataAdapter(db_manager=mock_db_manager)
    
    def test_initialization(self, mock_db_manager):
        """Test adapter initialization."""
        with patch('stock_database.adapters.backtester_adapter.DataAccessAPI') as mock_api:
            adapter = BacktesterDataAdapter(
                db_manager=mock_db_manager,
                cache_ttl=300,
                batch_size=500
            )
            
            assert adapter.db_manager == mock_db_manager
            assert adapter.batch_size == 500
            assert adapter.cache_ttl == 300
            assert adapter._query_count == 0
            assert adapter._conversion_count == 0
            mock_api.assert_called_once()
    
    def test_initialization_without_db_manager(self):
        """Test adapter initialization without providing db_manager."""
        with patch('stock_database.adapters.backtester_adapter.MongoDBManager') as mock_mongo:
            with patch('stock_database.adapters.backtester_adapter.DataAccessAPI'):
                adapter = BacktesterDataAdapter()
                mock_mongo.assert_called_once()
    
    def test_convert_to_market_data(self, adapter, sample_stock_data):
        """Test conversion from StockData to MarketData."""
        market_data = adapter.convert_to_market_data(sample_stock_data)
        
        assert len(market_data) == 5
        assert adapter._conversion_count == 5
        
        for i, market_item in enumerate(market_data):
            stock_item = sample_stock_data[i]
            assert isinstance(market_item, MarketData)
            assert market_item.timestamp == stock_item.date
            assert market_item.open == stock_item.open
            assert market_item.high == stock_item.high
            assert market_item.low == stock_item.low
            assert market_item.close == stock_item.close
            assert market_item.volume == stock_item.volume
    
    def test_convert_to_market_data_empty_list(self, adapter):
        """Test conversion with empty list."""
        market_data = adapter.convert_to_market_data([])
        assert market_data == []
        assert adapter._conversion_count == 0
    
    def test_convert_to_market_data_invalid_data(self, adapter):
        """Test conversion with invalid stock data."""
        invalid_stock_data = [
            StockData(
                symbol="INVALID",
                date=datetime(2024, 1, 1),
                open=-10.0,  # Invalid negative price
                high=155.0,
                low=149.0,
                close=154.0,
                volume=1000000,
                adjusted_close=154.0
            )
        ]
        
        # Mock the validate method to return False
        with patch.object(invalid_stock_data[0], 'validate', return_value=False):
            market_data = adapter.convert_to_market_data(invalid_stock_data)
            assert len(market_data) == 0
    
    def test_get_market_data_success(self, adapter, sample_stock_data):
        """Test successful market data retrieval."""
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter.get_market_data("AAPL")
        
        assert len(result) == 5
        assert adapter._query_count == 1
        adapter.data_api.get_stock_data.assert_called_once_with(
            symbol="AAPL",
            start_date=None,
            end_date=None,
            limit=None
        )
        
        # Check sorting (oldest first)
        for i in range(len(result) - 1):
            assert result[i].timestamp <= result[i + 1].timestamp
    
    def test_get_market_data_with_parameters(self, adapter, sample_stock_data):
        """Test market data retrieval with date parameters."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        limit = 10
        
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter.get_market_data("AAPL", start_date, end_date, limit)
        
        adapter.data_api.get_stock_data.assert_called_once_with(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def test_get_market_data_invalid_symbol(self, adapter):
        """Test market data retrieval with invalid symbol."""
        with pytest.raises(ValueError, match="Symbol must be a non-empty string"):
            adapter.get_market_data("")
        
        with pytest.raises(ValueError, match="Symbol must be a non-empty string"):
            adapter.get_market_data(None)
    
    def test_get_market_data_no_data_found(self, adapter):
        """Test market data retrieval when no data is found."""
        adapter.data_api.get_stock_data = Mock(return_value=[])
        
        result = adapter.get_market_data("NONEXISTENT")
        
        assert result == []
        assert adapter._query_count == 1
    
    def test_get_market_data_range_valid(self, adapter, sample_stock_data):
        """Test market data range retrieval with valid dates."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter.get_market_data_range("AAPL", start_date, end_date)
        
        assert len(result) == 5
        adapter.data_api.get_stock_data.assert_called_once()
    
    def test_get_market_data_range_invalid_dates(self, adapter):
        """Test market data range retrieval with invalid date range."""
        start_date = datetime(2024, 1, 5)
        end_date = datetime(2024, 1, 1)
        
        with pytest.raises(ValueError, match="Start date must be before or equal to end date"):
            adapter.get_market_data_range("AAPL", start_date, end_date)
    
    def test_get_market_data_range_large_dataset(self, adapter, sample_stock_data):
        """Test market data range retrieval for large dataset using streaming."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)  # Large range
        
        adapter.batch_size = 10  # Small batch size to trigger streaming
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        with patch.object(adapter, '_get_market_data_streaming', return_value=sample_stock_data) as mock_streaming:
            result = adapter.get_market_data_range("AAPL", start_date, end_date)
            mock_streaming.assert_called_once_with("AAPL", start_date, end_date)
    
    def test_get_multiple_symbols_data(self, adapter, sample_stock_data):
        """Test retrieval of data for multiple symbols."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter.get_multiple_symbols_data(symbols)
        
        assert len(result) == 3
        assert all(symbol in result for symbol in symbols)
        assert all(len(result[symbol]) == 5 for symbol in symbols)
        assert adapter.data_api.get_stock_data.call_count == 3
    
    def test_get_multiple_symbols_data_with_error(self, adapter, sample_stock_data):
        """Test multiple symbols data retrieval with one symbol failing."""
        symbols = ["AAPL", "INVALID", "MSFT"]
        
        def mock_get_stock_data(symbol, **kwargs):
            if symbol == "INVALID":
                raise Exception("Invalid symbol")
            return sample_stock_data
        
        adapter.data_api.get_stock_data = Mock(side_effect=mock_get_stock_data)
        
        result = adapter.get_multiple_symbols_data(symbols)
        
        assert len(result) == 3
        assert len(result["AAPL"]) == 5
        assert len(result["INVALID"]) == 0  # Empty due to error
        assert len(result["MSFT"]) == 5
    
    def test_get_latest_market_data(self, adapter, sample_stock_data):
        """Test retrieval of latest market data."""
        adapter.data_api.get_recent_stock_data = Mock(return_value=sample_stock_data[:2])
        
        result = adapter.get_latest_market_data("AAPL", days=2)
        
        assert len(result) == 2
        adapter.data_api.get_recent_stock_data.assert_called_once_with("AAPL", 2)
    
    def test_validate_data_availability_success(self, adapter):
        """Test data availability validation with sufficient data."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        # Mock data summary
        mock_summary = {
            "total_records": 100,
            "date_range": (datetime(2023, 12, 1), datetime(2024, 2, 1)),
            "data_completeness": 0.95
        }
        adapter.data_api.stock_repo.get_data_summary = Mock(return_value=mock_summary)
        
        # Mock market data
        sample_market_data = [
            MarketData(datetime(2024, 1, 1), 150, 155, 149, 154, 1000000),
            MarketData(datetime(2024, 1, 2), 151, 156, 150, 155, 1001000)
        ]
        adapter.get_market_data = Mock(return_value=sample_market_data)
        adapter.data_api.stock_repo.get_missing_dates = Mock(return_value=[])
        
        result = adapter.validate_data_availability("AAPL", start_date, end_date, min_data_points=2)
        
        assert result["is_available"] is True
        assert result["data_points"] == 2
        assert len(result["warnings"]) == 0
        assert result["data_completeness"] == 0.95
    
    def test_validate_data_availability_no_data(self, adapter):
        """Test data availability validation with no data."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        mock_summary = {"total_records": 0}
        adapter.data_api.stock_repo.get_data_summary = Mock(return_value=mock_summary)
        
        result = adapter.validate_data_availability("AAPL", start_date, end_date)
        
        assert result["is_available"] is False
        assert result["data_points"] == 0
        assert "No data available for symbol" in result["warnings"]
    
    def test_get_data_statistics(self, adapter, sample_stock_data):
        """Test data statistics retrieval."""
        adapter.data_api.get_recent_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter.get_data_statistics("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert result["data_points"] == 5
        assert "price_statistics" in result
        assert "volume_statistics" in result
        assert "volatility" in result
        
        # Check price statistics
        prices = [data.close for data in sample_stock_data]
        assert result["price_statistics"]["min"] == min(prices)
        assert result["price_statistics"]["max"] == max(prices)
        assert result["price_statistics"]["current"] == prices[0]
    
    def test_get_data_statistics_no_data(self, adapter):
        """Test data statistics with no data available."""
        adapter.data_api.get_recent_stock_data = Mock(return_value=[])
        
        result = adapter.get_data_statistics("NONEXISTENT")
        
        assert result["symbol"] == "NONEXISTENT"
        assert "error" in result
        assert result["error"] == "No data available"
    
    def test_optimize_for_backtesting(self, adapter, sample_stock_data):
        """Test backtesting optimization."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        adapter.get_market_data = Mock(return_value=[
            MarketData(datetime(2024, 1, 1), 150, 155, 149, 154, 1000000)
        ])
        
        result = adapter.optimize_for_backtesting("AAPL", start_date, end_date, preload=True)
        
        assert result["symbol"] == "AAPL"
        assert result["preloaded"] is True
        assert result["data_points"] == 1
        assert result["memory_usage_mb"] >= 0  # Allow 0.0 for small datasets
        assert result["optimization_time"] >= 0
    
    def test_optimize_for_backtesting_no_preload(self, adapter):
        """Test backtesting optimization without preloading."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        result = adapter.optimize_for_backtesting("AAPL", start_date, end_date, preload=False)
        
        assert result["symbol"] == "AAPL"
        assert result["preloaded"] is False
        assert result["data_points"] == 0
        assert result["memory_usage_mb"] == 0
    
    def test_get_performance_stats(self, adapter):
        """Test performance statistics retrieval."""
        # Simulate some operations
        adapter._query_count = 10
        adapter._conversion_count = 50
        adapter._cache_hits = 3
        
        stats = adapter.get_performance_stats()
        
        assert stats["query_count"] == 10
        assert stats["conversion_count"] == 50
        assert stats["cache_hits"] == 3
        assert stats["cache_hit_rate"] == 0.3
        assert stats["batch_size"] == adapter.batch_size
        assert stats["cache_ttl"] == adapter.cache_ttl
    
    def test_clear_cache(self, adapter):
        """Test cache clearing."""
        adapter.data_api.clear_cache = Mock()
        
        adapter.clear_cache("AAPL")
        adapter.data_api.clear_cache.assert_called_once_with("AAPL")
        
        adapter.clear_cache()
        adapter.data_api.clear_cache.assert_called_with(None)
    
    def test_health_check_healthy(self, adapter):
        """Test health check with healthy system."""
        # Mock healthy API response
        mock_api_health = {"overall_status": "healthy"}
        adapter.data_api.health_check = Mock(return_value=mock_api_health)
        
        # Mock available symbols and test data
        adapter.data_api.get_available_symbols = Mock(return_value={"stock_data": ["AAPL"]})
        adapter.get_latest_market_data = Mock(return_value=[
            MarketData(datetime(2024, 1, 1), 150, 155, 149, 154, 1000000)
        ])
        
        result = adapter.health_check()
        
        assert result["adapter_status"] == "healthy"
        assert result["data_api_status"] == "healthy"
        assert result["test_conversion"] is True
        assert len(result["errors"]) == 0
    
    def test_health_check_degraded(self, adapter):
        """Test health check with degraded system."""
        # Mock degraded API response
        mock_api_health = {"overall_status": "degraded"}
        adapter.data_api.health_check = Mock(return_value=mock_api_health)
        
        # Mock available symbols but failed test conversion
        adapter.data_api.get_available_symbols = Mock(return_value={"stock_data": ["AAPL"]})
        adapter.get_latest_market_data = Mock(side_effect=Exception("Test error"))
        
        result = adapter.health_check()
        
        assert result["adapter_status"] == "degraded"
        assert result["data_api_status"] == "degraded"
        assert result["test_conversion"] is False
        assert len(result["errors"]) > 0
    
    def test_health_check_no_symbols(self, adapter):
        """Test health check with no available symbols."""
        mock_api_health = {"overall_status": "healthy"}
        adapter.data_api.health_check = Mock(return_value=mock_api_health)
        adapter.data_api.get_available_symbols = Mock(return_value={"stock_data": []})
        
        result = adapter.health_check()
        
        assert result["adapter_status"] == "degraded"
        assert result["test_conversion"] is False
        assert "No symbols available for testing" in result["errors"]
    
    def test_streaming_data_retrieval(self, adapter, sample_stock_data):
        """Test streaming data retrieval for large datasets."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        
        adapter.batch_size = 100
        adapter.data_api.get_stock_data = Mock(return_value=sample_stock_data)
        
        result = adapter._get_market_data_streaming("AAPL", start_date, end_date)
        
        assert len(result) == 5  # Based on sample data
        # Verify data is sorted by timestamp
        for i in range(len(result) - 1):
            assert result[i].timestamp <= result[i + 1].timestamp
    
    def test_error_handling_in_get_market_data(self, adapter):
        """Test error handling in get_market_data method."""
        adapter.data_api.get_stock_data = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(Exception, match="Database error"):
            adapter.get_market_data("AAPL")
        
        assert adapter._query_count == 1
    
    def test_error_handling_in_conversion(self, adapter):
        """Test error handling in data conversion."""
        invalid_data = [Mock()]  # Mock object that will cause conversion to fail
        invalid_data[0].validate.side_effect = Exception("Validation error")
        
        with pytest.raises(Exception):
            adapter.convert_to_market_data(invalid_data)