"""
Unit tests for YahooFinanceClient.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from stock_database.config import ConfigManager
from stock_database.models.company_info import CompanyInfo
from stock_database.models.financial_data import FinancialData
from stock_database.models.stock_data import StockData
from stock_database.utils.yahoo_finance_client import (RateLimitError,
                                                       YahooFinanceClient,
                                                       YahooFinanceError)


class TestYahooFinanceClient(unittest.TestCase):
    """Test cases for YahooFinanceClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock config manager
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.get.return_value = {
            "request_delay": 0.1,  # Faster for testing
            "max_retries": 2,
            "timeout": 10,
            "batch_size": 5
        }
        
        self.client = YahooFinanceClient(config_manager=self.mock_config)
    
    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.request_delay, 0.1)
        self.assertEqual(self.client.max_retries, 2)
        self.assertEqual(self.client.timeout, 10)
        self.assertEqual(self.client.batch_size, 5)
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_validate_symbol_valid(self, mock_ticker):
        """Test symbol validation with valid symbol."""
        # Mock ticker info - return a dict with symbol key
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {'symbol': 'AAPL', 'longName': 'Apple Inc.'}
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.client.validate_symbol('AAPL')
        self.assertTrue(result)
        mock_ticker.assert_called_once_with('AAPL')
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_validate_symbol_invalid(self, mock_ticker):
        """Test symbol validation with invalid symbol."""
        # Mock ticker that raises exception
        mock_ticker.side_effect = Exception("Invalid symbol")
        
        result = self.client.validate_symbol('INVALID')
        self.assertFalse(result)
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_get_stock_data_success(self, mock_ticker):
        """Test successful stock data retrieval."""
        # Create mock data
        mock_data = pd.DataFrame({
            'Open': [150.0, 151.0],
            'High': [155.0, 156.0],
            'Low': [149.0, 150.0],
            'Close': [154.0, 155.0],
            'Volume': [1000000, 1100000]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.client.get_stock_data('AAPL', period='1mo')
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('symbol', result.columns)
        self.assertEqual(result['symbol'].iloc[0], 'AAPL')
        mock_ticker.assert_called_once_with('AAPL')
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_get_stock_data_empty_response(self, mock_ticker):
        """Test stock data retrieval with empty response."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        with self.assertRaises(YahooFinanceError):
            self.client.get_stock_data('INVALID')
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_get_financial_data_success(self, mock_ticker):
        """Test successful financial data retrieval."""
        # Mock financial data
        mock_financials = pd.DataFrame({
            '2023-12-31': [100000000, 40000000, 30000000, 25000000],
            '2022-12-31': [90000000, 35000000, 25000000, 20000000]
        }, index=['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income'])
        
        mock_balance_sheet = pd.DataFrame({
            '2023-12-31': [350000000, 200000000, 150000000],
            '2022-12-31': [320000000, 180000000, 140000000]
        }, index=['Total Assets', 'Total Liab', 'Total Stockholder Equity'])
        
        mock_cash_flow = pd.DataFrame({
            '2023-12-31': [28000000, 25000000],
            '2022-12-31': [24000000, 21000000]
        }, index=['Total Cash From Operating Activities', 'Free Cash Flow'])
        
        mock_info = {
            'trailingPE': 25.0,
            'priceToBook': 3.5,
            'returnOnEquity': 0.167,
            'sharesOutstanding': 4000000000
        }
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.financials = mock_financials
        mock_ticker_instance.balance_sheet = mock_balance_sheet
        mock_ticker_instance.cashflow = mock_cash_flow
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.client.get_financial_data('AAPL')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertIn('financials', result)
        self.assertIn('balance_sheet', result)
        self.assertIn('cash_flow', result)
        self.assertIn('info', result)
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_get_company_info_success(self, mock_ticker):
        """Test successful company info retrieval."""
        mock_info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'country': 'United States',
            'currency': 'USD',
            'exchange': 'NASDAQ'
        }
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.client.get_company_info('AAPL')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['info'], mock_info)
    
    def test_get_incremental_data_no_new_data(self):
        """Test incremental data when no new data is available."""
        last_date = datetime.now() - timedelta(hours=1)  # Recent date
        
        result = self.client.get_incremental_data('AAPL', last_date)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_fetch_multiple_symbols(self, mock_ticker):
        """Test fetching data for multiple symbols."""
        # Mock data for different symbols
        mock_data_aapl = pd.DataFrame({
            'Open': [150.0], 'High': [155.0], 'Low': [149.0], 
            'Close': [154.0], 'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2024-01-01']))
        
        mock_data_googl = pd.DataFrame({
            'Open': [2800.0], 'High': [2850.0], 'Low': [2790.0], 
            'Close': [2840.0], 'Volume': [500000]
        }, index=pd.DatetimeIndex(['2024-01-01']))
        
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.history.return_value = mock_data_aapl
            elif symbol == 'GOOGL':
                mock_instance.history.return_value = mock_data_googl
            else:
                mock_instance.history.side_effect = Exception("Invalid symbol")
            return mock_instance
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        symbols = ['AAPL', 'GOOGL', 'INVALID']
        result = self.client.fetch_multiple_symbols(symbols, period='1mo')
        
        self.assertEqual(len(result), 2)  # Only valid symbols
        self.assertIn('AAPL', result)
        self.assertIn('GOOGL', result)
        self.assertNotIn('INVALID', result)
    
    def test_convert_to_stock_data(self):
        """Test conversion of DataFrame to StockData objects."""
        df = pd.DataFrame({
            'open': [150.0, 151.0],
            'high': [155.0, 156.0],
            'low': [149.0, 150.0],
            'close': [154.0, 155.0],
            'volume': [1000000, 1100000],
            'dividends': [0.0, 0.5],
            'stock_splits': [1.0, 1.0]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))
        
        result = self.client.convert_to_stock_data(df, 'AAPL')
        
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], StockData)
        self.assertEqual(result[0].symbol, 'AAPL')
        self.assertEqual(result[0].open, 150.0)
        self.assertEqual(result[0].close, 154.0)
        self.assertEqual(result[0].volume, 1000000)
    
    def test_convert_to_financial_data(self):
        """Test conversion of financial dict to FinancialData objects."""
        financial_dict = {
            'symbol': 'AAPL',
            'financials': pd.DataFrame({
                pd.Timestamp('2023-12-31'): [100000000, 40000000, 30000000, 25000000],
                pd.Timestamp('2022-12-31'): [90000000, 35000000, 25000000, 20000000]
            }, index=['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']),
            'balance_sheet': pd.DataFrame({
                pd.Timestamp('2023-12-31'): [350000000, 200000000, 150000000],
                pd.Timestamp('2022-12-31'): [320000000, 180000000, 140000000]
            }, index=['Total Assets', 'Total Liab', 'Total Stockholder Equity']),
            'cash_flow': pd.DataFrame({
                pd.Timestamp('2023-12-31'): [28000000, 25000000],
                pd.Timestamp('2022-12-31'): [24000000, 21000000]
            }, index=['Total Cash From Operating Activities', 'Free Cash Flow']),
            'info': {
                'trailingPE': 25.0,
                'priceToBook': 3.5,
                'returnOnEquity': 0.167,
                'sharesOutstanding': 4000000000
            }
        }
        
        result = self.client.convert_to_financial_data(financial_dict)
        
        self.assertEqual(len(result), 2)  # Two years of data
        self.assertIsInstance(result[0], FinancialData)
        self.assertEqual(result[0].symbol, 'AAPL')
        self.assertEqual(result[0].revenue, 100000000)
        self.assertEqual(result[0].per, 25.0)
    
    def test_convert_to_company_info(self):
        """Test conversion of company dict to CompanyInfo object."""
        company_dict = {
            'symbol': 'AAPL',
            'info': {
                'longName': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'marketCap': 3000000000000,
                'country': 'United States',
                'currency': 'USD',
                'exchange': 'NASDAQ'
            }
        }
        
        result = self.client.convert_to_company_info(company_dict)
        
        self.assertIsInstance(result, CompanyInfo)
        self.assertEqual(result.symbol, 'AAPL')
        self.assertEqual(result.company_name, 'Apple Inc.')
        self.assertEqual(result.sector, 'Technology')
        self.assertEqual(result.market_cap, 3000000000000)
    
    @patch('stock_database.utils.yahoo_finance_client.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting functionality."""
        # Set a longer delay for this test
        self.client.request_delay = 1.0
        
        # First call should not sleep
        self.client._rate_limit()
        mock_sleep.assert_not_called()
        
        # Second call immediately after should sleep
        self.client._rate_limit()
        mock_sleep.assert_called_once()
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    @patch('stock_database.utils.yahoo_finance_client.time.sleep')
    def test_retry_mechanism(self, mock_sleep, mock_ticker):
        """Test retry mechanism on failures."""
        # Set max_retries to 3 for this test to allow 2 failures + 1 success
        self.client.max_retries = 3
        
        # Mock ticker that fails twice then succeeds
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            pd.DataFrame({
                'Open': [150.0], 'High': [155.0], 'Low': [149.0], 
                'Close': [154.0], 'Volume': [1000000]
            }, index=pd.DatetimeIndex(['2024-01-01']))
        ]
        mock_ticker.return_value = mock_ticker_instance
        
        # Should succeed after retries
        result = self.client.get_stock_data('AAPL')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(mock_ticker_instance.history.call_count, 3)
        # Sleep is called for rate limiting + retry backoff, so we just check it was called
        self.assertGreater(mock_sleep.call_count, 0)
    
    @patch('stock_database.utils.yahoo_finance_client.yf.Ticker')
    def test_retry_mechanism_all_fail(self, mock_ticker):
        """Test retry mechanism when all attempts fail."""
        # Mock ticker that always fails
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("Persistent error")
        mock_ticker.return_value = mock_ticker_instance
        
        with self.assertRaises(YahooFinanceError):
            self.client.get_stock_data('AAPL')
        
        # Should have tried max_retries times
        self.assertEqual(mock_ticker_instance.history.call_count, self.client.max_retries)


if __name__ == '__main__':
    unittest.main()