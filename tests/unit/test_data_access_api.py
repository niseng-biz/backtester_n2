"""
Unit tests for DataAccessAPI class.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
from stock_database.models.stock_data import StockData
from stock_database.repositories.data_access_api import DataAccessAPI


class TestDataAccessAPI:
    """Test cases for DataAccessAPI."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = Mock()
        mock_db.ensure_connection = Mock()
        return mock_db
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        stock_repo = Mock()
        financial_repo = Mock()
        company_repo = Mock()
        return stock_repo, financial_repo, company_repo
    
    @pytest.fixture
    def api(self, mock_db_manager, mock_repositories):
        """Create a DataAccessAPI instance with mocked dependencies."""
        stock_repo, financial_repo, company_repo = mock_repositories
        
        with patch('stock_database.repositories.data_access_api.StockDataRepository', return_value=stock_repo), \
             patch('stock_database.repositories.data_access_api.FinancialDataRepository', return_value=financial_repo), \
             patch('stock_database.repositories.data_access_api.CompanyInfoRepository', return_value=company_repo):
            
            api = DataAccessAPI(db_manager=mock_db_manager)
            return api
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2023,
            revenue=100000000000,
            net_income=25000000000,
            eps=6.15,
            per=25.0,
            roe=0.167
        )
        
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000
        )
        
        return stock_data, financial_data, company_info
    
    def test_initialization(self, mock_db_manager):
        """Test DataAccessAPI initialization."""
        with patch('stock_database.repositories.data_access_api.StockDataRepository') as mock_stock, \
             patch('stock_database.repositories.data_access_api.FinancialDataRepository') as mock_financial, \
             patch('stock_database.repositories.data_access_api.CompanyInfoRepository') as mock_company:
            
            api = DataAccessAPI(
                db_manager=mock_db_manager,
                stock_cache_ttl=300,
                financial_cache_ttl=600,
                company_cache_ttl=1800
            )
            
            # Verify repositories were initialized with correct parameters
            mock_stock.assert_called_once_with(mock_db_manager, 300)
            mock_financial.assert_called_once_with(mock_db_manager, 600)
            mock_company.assert_called_once_with(mock_db_manager, 1800)
    
    def test_get_stock_data(self, api, sample_data):
        """Test getting stock data."""
        stock_data, _, _ = sample_data
        api.stock_repo.get_stock_data.return_value = [stock_data]
        
        result = api.get_stock_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31))
        
        assert result == [stock_data]
        api.stock_repo.get_stock_data.assert_called_once_with(
            "AAPL", datetime(2024, 1, 1), datetime(2024, 1, 31), None
        )
    
    def test_get_latest_stock_data(self, api, sample_data):
        """Test getting latest stock data."""
        stock_data, _, _ = sample_data
        api.stock_repo.get_stock_data.return_value = [stock_data]
        
        result = api.get_latest_stock_data("AAPL")
        
        assert result == stock_data
        api.stock_repo.get_stock_data.assert_called_once_with("AAPL", limit=1)
    
    def test_get_latest_stock_data_none(self, api):
        """Test getting latest stock data when none exists."""
        api.stock_repo.get_stock_data.return_value = []
        
        result = api.get_latest_stock_data("AAPL")
        
        assert result is None
    
    def test_get_financial_data(self, api, sample_data):
        """Test getting financial data."""
        _, financial_data, _ = sample_data
        api.financial_repo.get_financial_data.return_value = [financial_data]
        
        result = api.get_financial_data("AAPL", fiscal_year=2023)
        
        assert result == [financial_data]
        api.financial_repo.get_financial_data.assert_called_once_with("AAPL", 2023, None, None)
    
    def test_get_company_info(self, api, sample_data):
        """Test getting company info."""
        _, _, company_info = sample_data
        api.company_repo.get_company_info.return_value = company_info
        
        result = api.get_company_info("AAPL")
        
        assert result == company_info
        api.company_repo.get_company_info.assert_called_once_with("AAPL")
    
    def test_get_complete_company_data(self, api, sample_data):
        """Test getting complete company data."""
        stock_data, financial_data, company_info = sample_data
        
        # Mock repository responses
        api.company_repo.get_company_info.return_value = company_info
        api.stock_repo.get_stock_data.return_value = [stock_data]
        api.stock_repo.get_recent_data.return_value = [stock_data]
        api.financial_repo.get_latest_financial_data.return_value = financial_data
        api.financial_repo.get_annual_data.return_value = [financial_data]
        api.financial_repo.get_financial_ratios.return_value = {"per": 25.0, "roe": 0.167}
        api.stock_repo.get_data_summary.return_value = {"total_records": 100, "data_completeness": 0.95}
        api.financial_repo.get_data_summary.return_value = {"total_records": 5, "annual_records": 5}
        
        result = api.get_complete_company_data("AAPL", include_stock_days=30, include_financial_years=5)
        
        # Verify structure
        assert result["symbol"] == "AAPL"
        assert result["company_info"] == company_info
        assert result["latest_stock_data"] == stock_data
        assert result["recent_stock_data"] == [stock_data]
        assert result["latest_financial_data"] == financial_data
        assert result["annual_financial_data"] == [financial_data]
        assert result["financial_ratios"] == {"per": 25.0, "roe": 0.167}
        assert "data_summary" in result
        
        # Verify repository calls
        api.company_repo.get_company_info.assert_called_once_with("AAPL")
        api.stock_repo.get_recent_data.assert_called_once_with("AAPL", 30)
        api.financial_repo.get_annual_data.assert_called_once_with("AAPL", 5)
    
    def test_bulk_get_latest_data(self, api, sample_data):
        """Test bulk getting latest data."""
        stock_data, financial_data, company_info = sample_data
        symbols = ["AAPL", "GOOGL"]
        
        # Mock repository responses
        api.stock_repo.bulk_get_latest_dates.return_value = {
            "AAPL": datetime(2024, 1, 1),
            "GOOGL": datetime(2024, 1, 2)
        }
        api.company_repo.bulk_get_company_info.return_value = {
            "AAPL": company_info,
            "GOOGL": None
        }
        api.financial_repo.get_latest_financial_data.return_value = financial_data
        
        result = api.bulk_get_latest_data(symbols)
        
        # Verify structure
        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result
        
        # Verify AAPL data
        aapl_data = result["AAPL"]
        assert aapl_data["symbol"] == "AAPL"
        assert aapl_data["latest_stock_date"] == datetime(2024, 1, 1)
        assert aapl_data["company_info"] == company_info
        assert aapl_data["latest_financial_data"] == financial_data
        
        # Verify repository calls
        api.stock_repo.bulk_get_latest_dates.assert_called_once_with(symbols)
        api.company_repo.bulk_get_company_info.assert_called_once_with(symbols)
    
    def test_get_sector_analysis(self, api, sample_data):
        """Test sector analysis."""
        _, financial_data, company_info = sample_data
        
        # Mock repository responses
        api.company_repo.get_companies_by_sector.return_value = [company_info]
        api.stock_repo.bulk_get_latest_dates.return_value = {"AAPL": datetime(2024, 1, 1)}
        api.company_repo.bulk_get_company_info.return_value = {"AAPL": company_info}
        api.financial_repo.get_latest_financial_data.return_value = financial_data
        api.financial_repo.get_financial_ratios.return_value = {"per": 25.0, "roe": 0.167}
        
        result = api.get_sector_analysis("Technology", limit=10)
        
        # Verify structure
        assert result["sector"] == "Technology"
        assert result["company_count"] == 1
        assert len(result["companies"]) == 1
        assert "latest_data" in result
        assert "market_cap_stats" in result
        assert "financial_ratio_stats" in result
        
        # Verify repository calls
        api.company_repo.get_companies_by_sector.assert_called_once_with("Technology")
    
    def test_compare_companies(self, api, sample_data):
        """Test company comparison."""
        _, financial_data, company_info = sample_data
        symbols = ["AAPL", "GOOGL"]
        metrics = ["market_cap", "per"]
        
        # Mock repository responses
        api.company_repo.get_company_info.return_value = company_info
        api.financial_repo.get_financial_ratios.return_value = {"per": 25.0, "roe": 0.167}
        api.financial_repo.get_latest_financial_data.return_value = financial_data
        
        result = api.compare_companies(symbols, metrics)
        
        # Verify structure
        assert result["symbols"] == symbols
        assert result["metrics"] == metrics
        assert "company_data" in result
        assert "metric_comparisons" in result
        assert "rankings" in result
        
        # Verify repository calls were made for each symbol
        assert api.company_repo.get_company_info.call_count == len(symbols)
        assert api.financial_repo.get_financial_ratios.call_count == len(symbols)
    
    def test_save_all_data(self, api, sample_data):
        """Test saving all data types."""
        stock_data, financial_data, company_info = sample_data
        
        result = api.save_all_data(
            stock_data=[stock_data],
            financial_data=[financial_data],
            company_info=[company_info]
        )
        
        # Verify counts
        assert result["stock_data"] == 1
        assert result["financial_data"] == 1
        assert result["company_info"] == 1
        
        # Verify repository calls
        api.stock_repo.save_stock_data.assert_called_once_with([stock_data])
        api.financial_repo.save_financial_data.assert_called_once_with([financial_data])
        api.company_repo.save_company_info.assert_called_once_with([company_info])
    
    def test_save_all_data_partial(self, api, sample_data):
        """Test saving partial data."""
        stock_data, _, _ = sample_data
        
        result = api.save_all_data(stock_data=[stock_data])
        
        # Verify counts
        assert result["stock_data"] == 1
        assert result["financial_data"] == 0
        assert result["company_info"] == 0
        
        # Verify only stock repo was called
        api.stock_repo.save_stock_data.assert_called_once_with([stock_data])
        api.financial_repo.save_financial_data.assert_not_called()
        api.company_repo.save_company_info.assert_not_called()
    
    def test_clear_cache_symbol(self, api):
        """Test clearing cache for specific symbol."""
        api.clear_cache("AAPL")
        
        # Verify all repositories had cache cleared for symbol
        api.stock_repo.clear_symbol_cache.assert_called_once_with("AAPL")
        api.financial_repo.clear_symbol_cache.assert_called_once_with("AAPL")
        api.company_repo.clear_symbol_cache.assert_called_once_with("AAPL")
    
    def test_clear_cache_all(self, api):
        """Test clearing all cache."""
        api.clear_cache()
        
        # Verify all repositories had cache cleared
        api.stock_repo._clear_cache.assert_called_once()
        api.financial_repo._clear_cache.assert_called_once()
        api.company_repo._clear_cache.assert_called_once()
    
    def test_get_system_stats(self, api):
        """Test getting system statistics."""
        # Mock repository responses
        api.stock_repo.get_collection_stats.return_value = {"count": 1000}
        api.financial_repo.get_collection_stats.return_value = {"count": 100}
        api.company_repo.get_collection_stats.return_value = {"count": 50}
        
        api.stock_repo.get_cache_stats.return_value = {"active_entries": 10}
        api.financial_repo.get_cache_stats.return_value = {"active_entries": 5}
        api.company_repo.get_cache_stats.return_value = {"active_entries": 3}
        
        api.stock_repo.get_query_stats.return_value = {"get_stock_data": {"count": 100}}
        api.financial_repo.get_query_stats.return_value = {"get_financial_data": {"count": 50}}
        api.company_repo.get_query_stats.return_value = {"get_company_info": {"count": 25}}
        
        result = api.get_system_stats()
        
        # Verify structure
        assert "database_stats" in result
        assert "cache_stats" in result
        assert "query_stats" in result
        
        # Verify database stats
        assert result["database_stats"]["stock_data"]["count"] == 1000
        assert result["database_stats"]["financial_data"]["count"] == 100
        assert result["database_stats"]["company_info"]["count"] == 50
        
        # Verify cache stats
        assert result["cache_stats"]["stock_data"]["active_entries"] == 10
        assert result["cache_stats"]["financial_data"]["active_entries"] == 5
        assert result["cache_stats"]["company_info"]["active_entries"] == 3
    
    def test_calculate_stats(self, api):
        """Test statistics calculation utility method."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        result = api._calculate_stats(values)
        
        assert result["count"] == 5
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        assert result["mean"] == 3.0
        assert result["median"] == 3.0
        assert result["std_dev"] > 0
    
    def test_calculate_stats_empty(self, api):
        """Test statistics calculation with empty list."""
        result = api._calculate_stats([])
        
        assert result == {}
    
    def test_get_available_symbols(self, api):
        """Test getting available symbols."""
        # Mock repository responses
        api.stock_repo.get_symbols.return_value = ["AAPL", "GOOGL"]
        api.financial_repo.get_symbols.return_value = ["AAPL", "MSFT"]
        api.company_repo.get_all_symbols.return_value = ["AAPL", "GOOGL", "MSFT"]
        
        result = api.get_available_symbols()
        
        # Verify structure
        assert "stock_data" in result
        assert "financial_data" in result
        assert "company_info" in result
        
        # Verify values
        assert result["stock_data"] == ["AAPL", "GOOGL"]
        assert result["financial_data"] == ["AAPL", "MSFT"]
        assert result["company_info"] == ["AAPL", "GOOGL", "MSFT"]
    
    def test_health_check_healthy(self, api):
        """Test health check when system is healthy."""
        # Mock successful operations
        api.db_manager.ensure_connection.return_value = None
        api.stock_repo.get_symbols.return_value = ["AAPL"]
        api.financial_repo.get_symbols.return_value = ["AAPL"]
        api.company_repo.get_all_symbols.return_value = ["AAPL"]
        
        result = api.health_check()
        
        assert result["overall_status"] == "healthy"
        assert result["database_connection"] is True
        assert all(result["repositories"].values())
        assert result["errors"] == []
    
    def test_health_check_database_error(self, api):
        """Test health check when database connection fails."""
        # Mock database connection failure
        api.db_manager.ensure_connection.side_effect = Exception("Connection failed")
        
        result = api.health_check()
        
        assert result["overall_status"] == "unhealthy"
        assert result["database_connection"] is False
        assert len(result["errors"]) > 0
        assert "Database connection error" in result["errors"][0]
    
    def test_health_check_repository_error(self, api):
        """Test health check when repository fails."""
        # Mock successful database connection but repository failure
        api.db_manager.ensure_connection.return_value = None
        api.stock_repo.get_symbols.side_effect = Exception("Repository error")
        api.financial_repo.get_symbols.return_value = ["AAPL"]
        api.company_repo.get_all_symbols.return_value = ["AAPL"]
        
        result = api.health_check()
        
        assert result["overall_status"] == "degraded"
        assert result["database_connection"] is True
        assert result["repositories"]["stock_data"] is False
        assert result["repositories"]["financial_data"] is True
        assert result["repositories"]["company_info"] is True
        assert len(result["errors"]) > 0
        assert "Stock data repository error" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__])