"""
Unit tests for repository classes.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
from stock_database.models.stock_data import StockData
from stock_database.repositories.company_info_repository import \
    CompanyInfoRepository
from stock_database.repositories.financial_data_repository import \
    FinancialDataRepository
from stock_database.repositories.stock_data_repository import \
    StockDataRepository


class TestStockDataRepository:
    """Test cases for StockDataRepository."""
    

    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Create a StockDataRepository instance with mocked dependencies."""
        return StockDataRepository(db_manager=mock_db_manager, cache_ttl=60)
    

    
    def test_save_stock_data_valid(self, repository, sample_stock_data_list):
        """Test saving valid stock data."""
        repository.save_stock_data(sample_stock_data_list)
        
        # Verify upsert was called with valid data
        repository.db_manager.upsert_stock_data.assert_called_once()
        args = repository.db_manager.upsert_stock_data.call_args[0][0]
        assert len(args) == 5
        assert all(isinstance(item, StockData) for item in args)
    
    def test_save_stock_data_empty(self, repository):
        """Test saving empty stock data list."""
        repository.save_stock_data([])
        
        # Should not call upsert for empty data
        repository.db_manager.upsert_stock_data.assert_not_called()
    
    def test_save_stock_data_invalid(self, repository):
        """Test saving invalid stock data."""
        invalid_data = [
            StockData(
                symbol="",  # Invalid empty symbol
                date=datetime(2024, 1, 1),
                open=150.0,
                high=155.0,
                low=149.0,
                close=154.0,
                volume=1000000,
                adjusted_close=154.0
            )
        ]
        
        with pytest.raises(ValueError, match="No valid stock data to save"):
            repository.save_stock_data(invalid_data)
    
    def test_get_stock_data(self, repository):
        """Test retrieving stock data."""
        expected_data = [StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )]
        
        repository.db_manager.get_stock_data.return_value = expected_data
        
        result = repository.get_stock_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))
        
        assert result == expected_data
        repository.db_manager.get_stock_data.assert_called_once_with(
            "AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31), None
        )
    
    def test_get_latest_date(self, repository):
        """Test getting latest date for a symbol."""
        expected_date = datetime(2024, 1, 31)
        repository.db_manager.get_latest_stock_date.return_value = expected_date
        
        result = repository.get_latest_date("AAPL")
        
        assert result == expected_date
        repository.db_manager.get_latest_stock_date.assert_called_once_with("AAPL")
    
    def test_update_stock_data(self, repository):
        """Test updating stock data."""
        repository.db_manager.update_stock_data.return_value = True
        
        updates = {"close": 160.0, "volume": 1500000}
        result = repository.update_stock_data("AAPL", datetime(2024, 1, 1), updates)
        
        assert result is True
        repository.db_manager.update_stock_data.assert_called_once_with(
            "AAPL", datetime(2024, 1, 1), updates
        )
    
    def test_get_recent_data(self, repository):
        """Test getting recent data."""
        expected_data = [StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 31),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )]
        
        repository.db_manager.get_stock_data.return_value = expected_data
        
        with patch('stock_database.repositories.stock_data_repository.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 2, 1)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = repository.get_recent_data("AAPL", days=30)
            
            assert result == expected_data
            # Verify the date range calculation
            repository.db_manager.get_stock_data.assert_called_once()
            args = repository.db_manager.get_stock_data.call_args[0]
            assert args[0] == "AAPL"  # symbol
            assert args[1] == datetime(2024, 1, 2)  # start_date (30 days before Feb 1)
            assert args[2] == datetime(2024, 2, 1)  # end_date


class TestFinancialDataRepository:
    """Test cases for FinancialDataRepository."""
    

    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Create a FinancialDataRepository instance with mocked dependencies."""
        return FinancialDataRepository(db_manager=mock_db_manager, cache_ttl=60)
    

    
    def test_save_financial_data_valid(self, repository, sample_financial_data_list):
        """Test saving valid financial data."""
        repository.save_financial_data(sample_financial_data_list)
        
        # Verify upsert was called with valid data
        repository.db_manager.upsert_financial_data.assert_called_once()
        args = repository.db_manager.upsert_financial_data.call_args[0][0]
        assert len(args) == 3
        assert all(isinstance(item, FinancialData) for item in args)
    
    def test_get_financial_data(self, repository):
        """Test retrieving financial data."""
        expected_data = [FinancialData(
            symbol="AAPL",
            fiscal_year=2023,
            revenue=100000000000,
            net_income=25000000000
        )]
        
        repository.db_manager.get_financial_data.return_value = expected_data
        
        result = repository.get_financial_data("AAPL", fiscal_year=2023)
        
        assert result == expected_data
        repository.db_manager.get_financial_data.assert_called_once_with("AAPL", 2023, None)
    
    def test_get_latest_financial_data(self, repository):
        """Test getting latest financial data."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_doc = {
            "symbol": "AAPL",
            "fiscal_year": 2023,
            "revenue": 100000000000,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mock_collection.find_one.return_value = mock_doc
        
        expected_data = FinancialData(symbol="AAPL", fiscal_year=2023, revenue=100000000000)
        repository.db_manager._doc_to_financial_data.return_value = expected_data
        
        result = repository.get_latest_financial_data("AAPL", annual_only=True)
        
        assert result == expected_data
        mock_collection.find_one.assert_called_once()
        call_args = mock_collection.find_one.call_args
        assert call_args[0][0] == {"symbol": "AAPL", "fiscal_quarter": None}
    
    def test_calculate_growth_rates(self, repository):
        """Test calculating growth rates."""
        # Mock annual data for growth calculation
        mock_data = [
            FinancialData(symbol="AAPL", fiscal_year=2022, revenue=80000000000),
            FinancialData(symbol="AAPL", fiscal_year=2023, revenue=100000000000)
        ]
        
        with patch.object(repository, 'get_annual_data', return_value=mock_data):
            result = repository.calculate_growth_rates("AAPL", "revenue", periods=2)
            
            assert len(result) == 1
            assert result[0]["fiscal_year"] == 2023
            assert result[0]["growth_rate"] == 25.0  # (100B - 80B) / 80B * 100
    
    def test_get_financial_ratios(self, repository):
        """Test getting financial ratios."""
        mock_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2023,
            revenue=100000000000,
            net_income=25000000000,
            per=25.0,
            roe=0.167
        )
        
        with patch.object(repository, 'get_latest_financial_data', return_value=mock_data):
            result = repository.get_financial_ratios("AAPL")
            
            assert result["symbol"] == "AAPL"
            assert result["fiscal_year"] == 2023
            assert result["per"] == 25.0
            assert result["roe"] == 0.167
            assert result["net_margin"] == 25.0  # (25B / 100B) * 100


class TestCompanyInfoRepository:
    """Test cases for CompanyInfoRepository."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = Mock()
        mock_db.COMPANY_INFO_COLLECTION = "company_info"
        mock_db.get_collection = Mock()
        return mock_db
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Create a CompanyInfoRepository instance with mocked dependencies."""
        return CompanyInfoRepository(db_manager=mock_db_manager, cache_ttl=60)
    

    
    def test_save_company_info_valid(self, repository, sample_company_info):
        """Test saving valid company info."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        # Create a list with the single company info object
        company_info_list = [sample_company_info]
        repository.save_company_info(company_info_list)
        
        # Verify bulk_write was called
        mock_collection.bulk_write.assert_called_once()
    
    def test_get_company_info(self, repository):
        """Test retrieving company info."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_doc = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_collection.find_one.return_value = mock_doc
        
        result = repository.get_company_info("AAPL")
        
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.company_name == "Apple Inc."
        mock_collection.find_one.assert_called_once_with({"symbol": "AAPL"})
    
    def test_get_companies_by_sector(self, repository):
        """Test getting companies by sector."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_docs = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "symbol": "GOOGL",
                "company_name": "Alphabet Inc.",
                "sector": "Technology",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))
        mock_collection.find.return_value.sort.return_value = mock_cursor
        
        result = repository.get_companies_by_sector("Technology")
        
        assert len(result) == 2
        assert all(company.sector == "Technology" for company in result)
        mock_collection.find.assert_called_once_with({"sector": "Technology"})
    
    def test_get_all_sectors(self, repository):
        """Test getting all sectors."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_collection.distinct.return_value = ["Technology", "Healthcare", "Finance"]
        
        result = repository.get_all_sectors()
        
        assert result == ["Finance", "Healthcare", "Technology"]  # Should be sorted
        mock_collection.distinct.assert_called_once_with("sector")
    
    def test_search_companies(self, repository):
        """Test searching companies."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_docs = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(mock_docs))
        mock_collection.find.return_value.sort.return_value = mock_cursor
        
        result = repository.search_companies("Apple")
        
        assert len(result) == 1
        assert result[0].company_name == "Apple Inc."
        
        # Verify the search query structure
        mock_collection.find.assert_called_once()
        call_args = mock_collection.find.call_args[0][0]
        assert "$or" in call_args
        assert len(call_args["$or"]) == 2  # symbol and company_name fields
    
    def test_update_company_info(self, repository):
        """Test updating company info."""
        mock_collection = Mock()
        repository.db_manager.get_collection.return_value = mock_collection
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        updates = {"market_cap": 3500000000000}
        result = repository.update_company_info("AAPL", updates)
        
        assert result is True
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"symbol": "AAPL"}
        assert "market_cap" in call_args[0][1]["$set"]
        assert "updated_at" in call_args[0][1]["$set"]


if __name__ == "__main__":
    pytest.main([__file__])