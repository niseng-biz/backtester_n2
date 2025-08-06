"""
Unit tests for stock database data models.
"""
import json
from datetime import date, datetime

import pytest

from stock_database.models import (
    CompanyInfo,
    DataValidator,
    FinancialData,
    StockData,
    ValidationResult,
)


class TestStockData:
    """Test cases for StockData model."""
    
    def test_stock_data_creation(self):
        """Test basic StockData creation."""
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
        
        assert stock_data.symbol == "AAPL"
        assert stock_data.date == datetime(2024, 1, 1)
        assert stock_data.open == 150.0
        assert stock_data.high == 155.0
        assert stock_data.low == 149.0
        assert stock_data.close == 154.0
        assert stock_data.volume == 1000000
        assert stock_data.adjusted_close == 154.0
    
    def test_stock_data_validation_valid(self):
        """Test validation of valid stock data."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0,
            rsi=65.5
        )
        
        assert stock_data.validate() is True
    
    def test_stock_data_validation_invalid_ohlc(self):
        """Test validation with invalid OHLC relationships."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=145.0,  # High < Open (invalid)
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        assert stock_data.validate() is False
    
    def test_stock_data_serialization(self):
        """Test JSON serialization and deserialization."""
        original = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        # Test to_dict and from_dict
        data_dict = original.to_dict()
        restored = StockData.from_dict(data_dict)
        
        assert restored.symbol == original.symbol
        assert restored.date == original.date
        assert restored.open == original.open
        
        # Test JSON serialization
        json_str = original.to_json()
        restored_from_json = StockData.from_json(json_str)
        
        assert restored_from_json.symbol == original.symbol
        assert restored_from_json.date == original.date


class TestFinancialData:
    """Test cases for FinancialData model."""
    
    def test_financial_data_creation(self):
        """Test basic FinancialData creation."""
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=1,
            revenue=100000000000,
            net_income=25000000000,
            eps=6.15
        )
        
        assert financial_data.symbol == "AAPL"
        assert financial_data.fiscal_year == 2024
        assert financial_data.fiscal_quarter == 1
        assert financial_data.revenue == 100000000000
        assert financial_data.net_income == 25000000000
        assert financial_data.eps == 6.15
    
    def test_financial_data_validation_valid(self):
        """Test validation of valid financial data."""
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=1,
            revenue=100000000000,
            net_income=25000000000,
            eps=6.15,
            roe=0.167,
            roa=0.071
        )
        
        assert financial_data.validate() is True
    
    def test_financial_data_validation_invalid_quarter(self):
        """Test validation with invalid fiscal quarter."""
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=5,  # Invalid quarter
            revenue=100000000000
        )
        
        assert financial_data.validate() is False
    
    def test_financial_data_serialization(self):
        """Test JSON serialization and deserialization."""
        original = FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=1,
            revenue=100000000000,
            eps=6.15
        )
        
        # Test to_dict and from_dict
        data_dict = original.to_dict()
        restored = FinancialData.from_dict(data_dict)
        
        assert restored.symbol == original.symbol
        assert restored.fiscal_year == original.fiscal_year
        assert restored.revenue == original.revenue
        
        # Test JSON serialization
        json_str = original.to_json()
        restored_from_json = FinancialData.from_json(json_str)
        
        assert restored_from_json.symbol == original.symbol
        assert restored_from_json.fiscal_year == original.fiscal_year


class TestCompanyInfo:
    """Test cases for CompanyInfo model."""
    
    def test_company_info_creation(self):
        """Test basic CompanyInfo creation."""
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            country="United States",
            currency="USD",
            exchange="NASDAQ"
        )
        
        assert company_info.symbol == "AAPL"
        assert company_info.company_name == "Apple Inc."
        assert company_info.sector == "Technology"
        assert company_info.industry == "Consumer Electronics"
        assert company_info.market_cap == 3000000000000
        assert company_info.country == "United States"
        assert company_info.currency == "USD"
        assert company_info.exchange == "NASDAQ"
    
    def test_company_info_validation_valid(self):
        """Test validation of valid company info."""
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            market_cap=3000000000000,
            currency="USD"
        )
        
        assert company_info.validate() is True
    
    def test_company_info_validation_invalid_currency(self):
        """Test validation with invalid currency code."""
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            currency="INVALID"  # Invalid currency code
        )
        
        assert company_info.validate() is False
    
    def test_company_info_serialization(self):
        """Test JSON serialization and deserialization."""
        original = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            currency="USD"
        )
        
        # Test to_dict and from_dict
        data_dict = original.to_dict()
        restored = CompanyInfo.from_dict(data_dict)
        
        assert restored.symbol == original.symbol
        assert restored.company_name == original.company_name
        assert restored.sector == original.sector
        
        # Test JSON serialization
        json_str = original.to_json()
        restored_from_json = CompanyInfo.from_json(json_str)
        
        assert restored_from_json.symbol == original.symbol
        assert restored_from_json.company_name == original.company_name


class TestDataValidator:
    """Test cases for DataValidator."""
    
    def test_validate_symbol_valid(self):
        """Test symbol validation with valid symbols."""
        result = DataValidator.validate_symbol("AAPL")
        assert result.is_valid is True
        
        result = DataValidator.validate_symbol("BRK.B")
        assert result.is_valid is True
    
    def test_validate_symbol_invalid(self):
        """Test symbol validation with invalid symbols."""
        result = DataValidator.validate_symbol("")
        assert result.is_valid is False
        assert "empty" in result.errors[0]
        
        result = DataValidator.validate_symbol("TOOLONGSYMBOL")
        assert result.is_valid is False
        assert "too long" in result.errors[0]
    
    def test_validate_stock_data_comprehensive(self):
        """Test comprehensive stock data validation."""
        # Valid data
        valid_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0,
            rsi=65.5
        )
        
        result = DataValidator.validate_stock_data(valid_data)
        assert result.is_valid is True
        
        # Invalid data - future date
        invalid_data = StockData(
            symbol="AAPL",
            date=datetime(2030, 1, 1),  # Future date
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        result = DataValidator.validate_stock_data(invalid_data)
        assert result.is_valid is False
        assert any("future" in error for error in result.errors)
    
    def test_validate_batch(self):
        """Test batch validation."""
        data_list = [
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=150.0,
                high=155.0,
                low=149.0,
                close=154.0,
                volume=1000000,
                adjusted_close=154.0
            ),
            FinancialData(
                symbol="AAPL",
                fiscal_year=2024,
                revenue=100000000000
            ),
            CompanyInfo(
                symbol="AAPL",
                company_name="Apple Inc."
            )
        ]
        
        results = DataValidator.validate_batch(data_list)
        
        assert len(results) == 3
        assert all(result.is_valid for result in results.values())


class TestValidationResult:
    """Test cases for ValidationResult."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation and methods."""
        result = ValidationResult()
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert bool(result) is True
        
        result.add_error("Test error")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert bool(result) is False
        assert "Test error" in str(result)


if __name__ == "__main__":
    pytest.main([__file__])