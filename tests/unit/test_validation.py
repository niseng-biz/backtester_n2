"""
Unit tests for data validation functionality.
"""
import unittest
from datetime import datetime, timedelta

from stock_database.models import (Anomaly, CompanyInfo, DataValidator,
                                   FinancialData, StockData, ValidationResult)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class."""
    
    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertTrue(bool(result))
        self.assertEqual(str(result), "Validation passed")
    
    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidationResult()
        result.add_error("Test error")
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertFalse(bool(result))
        self.assertIn("Test error", str(result))


class TestAnomaly(unittest.TestCase):
    """Test Anomaly class."""
    
    def test_anomaly_creation(self):
        """Test anomaly creation."""
        anomaly = Anomaly(
            anomaly_type="outlier",
            field="price",
            value=100.0,
            expected_range=(50.0, 150.0),
            severity="warning",
            description="Price outlier detected"
        )
        
        self.assertEqual(anomaly.anomaly_type, "outlier")
        self.assertEqual(anomaly.field, "price")
        self.assertEqual(anomaly.value, 100.0)
        self.assertEqual(anomaly.expected_range, (50.0, 150.0))
        self.assertEqual(anomaly.severity, "warning")
        self.assertEqual(anomaly.description, "Price outlier detected")
    
    def test_anomaly_to_dict(self):
        """Test anomaly to dictionary conversion."""
        anomaly = Anomaly("outlier", "price", 100.0)
        anomaly_dict = anomaly.to_dict()
        
        self.assertEqual(anomaly_dict['type'], "outlier")
        self.assertEqual(anomaly_dict['field'], "price")
        self.assertEqual(anomaly_dict['value'], 100.0)


class TestDataValidator(unittest.TestCase):
    """Test DataValidator class."""
    
    def test_validate_symbol_valid(self):
        """Test valid symbol validation."""
        result = DataValidator.validate_symbol("AAPL")
        self.assertTrue(result.is_valid)
        
        result = DataValidator.validate_symbol("BRK.B")
        self.assertTrue(result.is_valid)
        
        result = DataValidator.validate_symbol("BRK-B")
        self.assertTrue(result.is_valid)
    
    def test_validate_symbol_invalid(self):
        """Test invalid symbol validation."""
        result = DataValidator.validate_symbol("")
        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.errors[0])
        
        result = DataValidator.validate_symbol("TOOLONGSYMBOL")
        self.assertFalse(result.is_valid)
        self.assertIn("too long", result.errors[0])
        
        result = DataValidator.validate_symbol("AAPL@")
        self.assertFalse(result.is_valid)
        self.assertIn("invalid characters", result.errors[0])
    
    def test_validate_stock_data_valid(self):
        """Test valid stock data validation."""
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
        
        result = DataValidator.validate_stock_data(stock_data)
        self.assertTrue(result.is_valid)
    
    def test_validate_stock_data_invalid_prices(self):
        """Test stock data validation with invalid prices."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=-150.0,  # Invalid negative price
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        result = DataValidator.validate_stock_data(stock_data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("negative" in error for error in result.errors))
    
    def test_validate_stock_data_invalid_ohlc(self):
        """Test stock data validation with invalid OHLC relationships."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=149.0,  # High less than open
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        
        result = DataValidator.validate_stock_data(stock_data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("High price" in error for error in result.errors))
    
    def test_validate_financial_data_valid(self):
        """Test valid financial data validation."""
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=2023,
            revenue=100000000000.0,
            net_income=25000000000.0,
            total_assets=350000000000.0,
            total_liabilities=200000000000.0,
            shareholders_equity=150000000000.0
        )
        
        result = DataValidator.validate_financial_data(financial_data)
        self.assertTrue(result.is_valid)
    
    def test_validate_financial_data_invalid_year(self):
        """Test financial data validation with invalid year."""
        financial_data = FinancialData(
            symbol="AAPL",
            fiscal_year=1800,  # Invalid year
            revenue=100000000000.0
        )
        
        result = DataValidator.validate_financial_data(financial_data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("reasonable range" in error for error in result.errors))
    
    def test_validate_company_info_valid(self):
        """Test valid company info validation."""
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000.0,
            currency="USD"
        )
        
        result = DataValidator.validate_company_info(company_info)
        self.assertTrue(result.is_valid)
    
    def test_validate_company_info_invalid_currency(self):
        """Test company info validation with invalid currency."""
        company_info = CompanyInfo(
            symbol="AAPL",
            company_name="Apple Inc.",
            currency="INVALID"  # Invalid currency code
        )
        
        result = DataValidator.validate_company_info(company_info)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("3-letter code" in error for error in result.errors))
    
    def test_detect_anomalies_outliers(self):
        """Test anomaly detection for outliers."""
        # Create stock data with one outlier
        stock_data_list = []
        base_date = datetime(2024, 1, 1)
        
        # Normal data
        for i in range(10):
            stock_data_list.append(StockData(
                symbol="AAPL",
                date=base_date + timedelta(days=i),
                open=150.0 + i,
                high=155.0 + i,
                low=149.0 + i,
                close=154.0 + i,
                volume=1000000,
                adjusted_close=154.0 + i
            ))
        
        # Add outlier
        stock_data_list.append(StockData(
            symbol="AAPL",
            date=base_date + timedelta(days=10),
            open=1000.0,  # Outlier
            high=1005.0,
            low=999.0,
            close=1004.0,
            volume=1000000,
            adjusted_close=1004.0
        ))
        
        anomalies = DataValidator.detect_anomalies(stock_data_list)
        self.assertGreater(len(anomalies), 0)
        self.assertTrue(any(anomaly.anomaly_type == "outlier" for anomaly in anomalies))
    
    def test_detect_anomalies_ohlc_inconsistency(self):
        """Test anomaly detection for OHLC inconsistencies."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=150.0,
            high=149.0,  # High less than max(open, close) - inconsistency
            low=149.0,
            close=154.0,  # Close is 154.0, so high should be at least 154.0
            volume=1000000,
            adjusted_close=154.0
        )
        
        anomalies = DataValidator.detect_anomalies([stock_data])
        self.assertGreater(len(anomalies), 0)
        self.assertTrue(any(anomaly.anomaly_type == "ohlc_inconsistency" for anomaly in anomalies))
    
    def test_validate_batch(self):
        """Test batch validation."""
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
            revenue=100000000000.0
        )
        
        results = DataValidator.validate_batch([stock_data, financial_data])
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].is_valid)
        self.assertTrue(results[1].is_valid)


if __name__ == '__main__':
    unittest.main()