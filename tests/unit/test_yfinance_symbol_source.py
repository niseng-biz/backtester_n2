"""
Unit tests for YFinanceSymbolSource.
"""
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add the parent directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent.parent))

from stock_database.models.symbol_info import SymbolInfo
from stock_database.utils.symbol_data_source import (DataValidationError,
                                                     FilterCriteria,
                                                     NetworkError)
from stock_database.utils.yfinance_symbol_source import YFinanceSymbolSource


class TestYFinanceSymbolSource(unittest.TestCase):
    """Test cases for YFinanceSymbolSource."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.source = YFinanceSymbolSource(rate_limit=60, request_delay=0.1)
    
    def test_get_source_name(self):
        """Test get_source_name method."""
        self.assertEqual(self.source.get_source_name(), "YFinance Symbol Source")
    
    def test_get_rate_limit(self):
        """Test get_rate_limit method."""
        self.assertEqual(self.source.get_rate_limit(), 60)
    
    def test_get_supported_filters(self):
        """Test get_supported_filters method."""
        filters = self.source.get_supported_filters()
        expected_filters = ['sector', 'min_market_cap', 'max_market_cap', 'active_only', 'limit']
        self.assertEqual(set(filters), set(expected_filters))
    
    @patch('requests.Session.get')
    def test_is_available_success(self, mock_get):
        """Test is_available method when service is available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        self.assertTrue(self.source.is_available())
    
    @patch('requests.Session.get')
    def test_is_available_failure(self, mock_get):
        """Test is_available method when service is unavailable."""
        mock_get.side_effect = Exception("Network error")
        
        self.assertFalse(self.source.is_available())
    
    def test_parse_nasdaq_row_valid(self):
        """Test _parse_nasdaq_row with valid data."""
        row = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'marketCap': '$2.5T',
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        
        symbol_info = self.source._parse_nasdaq_row(row)
        
        self.assertIsNotNone(symbol_info)
        self.assertEqual(symbol_info.symbol, 'AAPL')
        self.assertEqual(symbol_info.company_name, 'Apple Inc.')
        self.assertEqual(symbol_info.exchange, 'NASDAQ')
        self.assertEqual(symbol_info.sector, 'Technology')
        self.assertEqual(symbol_info.industry, 'Consumer Electronics')
        self.assertTrue(symbol_info.is_active)
    
    def test_parse_nasdaq_row_market_cap_formats(self):
        """Test _parse_nasdaq_row with different market cap formats."""
        test_cases = [
            ('$1.5B', 1_500_000_000),
            ('$500M', 500_000_000),
            ('$2.3T', 2_300_000_000_000),
            ('$100K', 100_000),
            ('N/A', None),
            ('', None)
        ]
        
        for market_cap_str, expected_value in test_cases:
            row = {
                'symbol': 'TEST',
                'name': 'Test Company',
                'marketCap': market_cap_str
            }
            
            symbol_info = self.source._parse_nasdaq_row(row)
            self.assertEqual(symbol_info.market_cap, expected_value)
    
    def test_parse_nasdaq_row_invalid(self):
        """Test _parse_nasdaq_row with invalid data."""
        # Missing symbol
        row1 = {'name': 'Test Company'}
        self.assertIsNone(self.source._parse_nasdaq_row(row1))
        
        # Missing name
        row2 = {'symbol': 'TEST'}
        self.assertIsNone(self.source._parse_nasdaq_row(row2))
        
        # Empty symbol
        row3 = {'symbol': '', 'name': 'Test Company'}
        self.assertIsNone(self.source._parse_nasdaq_row(row3))
    
    def test_fetch_static_symbols(self):
        """Test _fetch_static_symbols method."""
        symbols = self.source._fetch_static_symbols()
        
        self.assertGreater(len(symbols), 0)
        
        # Check that all symbols are valid
        for symbol in symbols:
            self.assertIsInstance(symbol, SymbolInfo)
            self.assertTrue(symbol.symbol)
            self.assertTrue(symbol.company_name)
            self.assertEqual(symbol.exchange, 'NASDAQ')
            self.assertTrue(symbol.is_active)
    
    @patch('stock_database.utils.yfinance_symbol_source.YFinanceSymbolSource._fetch_nasdaq_screener')
    def test_fetch_symbols_with_screener(self, mock_screener):
        """Test fetch_symbols using NASDAQ screener."""
        mock_symbols = [
            SymbolInfo(symbol='AAPL', company_name='Apple Inc.', exchange='NASDAQ'),
            SymbolInfo(symbol='MSFT', company_name='Microsoft Corp.', exchange='NASDAQ')
        ]
        mock_screener.return_value = mock_symbols
        
        symbols = self.source.fetch_symbols()
        
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0].symbol, 'AAPL')
        self.assertEqual(symbols[1].symbol, 'MSFT')
    
    @patch('stock_database.utils.yfinance_symbol_source.YFinanceSymbolSource._fetch_static_symbols')
    @patch('stock_database.utils.yfinance_symbol_source.YFinanceSymbolSource._fetch_nasdaq_screener')
    def test_fetch_symbols_fallback_to_static(self, mock_screener, mock_static):
        """Test fetch_symbols falling back to static symbols."""
        mock_screener.side_effect = Exception("Screener failed")
        mock_static.return_value = [
            SymbolInfo(symbol='AAPL', company_name='Apple Inc.', exchange='NASDAQ')
        ]
        
        symbols = self.source.fetch_symbols()
        
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].symbol, 'AAPL')
        mock_static.assert_called_once()
    
    @patch('stock_database.utils.yfinance_symbol_source.YFinanceSymbolSource._fetch_nasdaq_screener')
    def test_fetch_symbols_with_filter(self, mock_screener):
        """Test fetch_symbols with filter criteria."""
        mock_symbols = [
            SymbolInfo(symbol='AAPL', company_name='Apple Inc.', exchange='NASDAQ', 
                      sector='Technology', market_cap=2_500_000_000_000),
            SymbolInfo(symbol='XOM', company_name='Exxon Mobil', exchange='NYSE', 
                      sector='Energy', market_cap=400_000_000_000)
        ]
        mock_screener.return_value = mock_symbols
        
        criteria = FilterCriteria(sector='Technology', min_market_cap=1_000_000_000_000)
        symbols = self.source.fetch_symbols(criteria=criteria)
        
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].symbol, 'AAPL')
    
    @patch('stock_database.utils.yfinance_symbol_source.YFinanceSymbolSource._fetch_nasdaq_screener')
    def test_fetch_symbols_with_limit(self, mock_screener):
        """Test fetch_symbols with limit."""
        mock_symbols = [
            SymbolInfo(symbol='AAPL', company_name='Apple Inc.', exchange='NASDAQ'),
            SymbolInfo(symbol='MSFT', company_name='Microsoft Corp.', exchange='NASDAQ'),
            SymbolInfo(symbol='GOOGL', company_name='Alphabet Inc.', exchange='NASDAQ')
        ]
        mock_screener.return_value = mock_symbols
        
        symbols = self.source.fetch_symbols(limit=2)
        
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0].symbol, 'AAPL')
        self.assertEqual(symbols[1].symbol, 'MSFT')
    
    @patch('requests.Session.get')
    def test_fetch_nasdaq_screener_success(self, mock_get):
        """Test _fetch_nasdaq_screener with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'rows': [
                    {
                        'symbol': 'AAPL',
                        'name': 'Apple Inc.',
                        'marketCap': '$2.5T',
                        'sector': 'Technology'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        symbols = self.source._fetch_nasdaq_screener()
        
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].symbol, 'AAPL')
    
    @patch('requests.Session.get')
    def test_fetch_nasdaq_screener_network_error(self, mock_get):
        """Test _fetch_nasdaq_screener with network error."""
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(NetworkError):
            self.source._fetch_nasdaq_screener()
    
    @patch('requests.Session.get')
    def test_fetch_nasdaq_screener_invalid_response(self, mock_get):
        """Test _fetch_nasdaq_screener with invalid response format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'invalid': 'format'}
        mock_get.return_value = mock_response
        
        with self.assertRaises(DataValidationError):
            self.source._fetch_nasdaq_screener()
    
    @patch('yfinance.Ticker')
    def test_enrich_symbol_with_yfinance(self, mock_ticker_class):
        """Test enrich_symbol_with_yfinance method."""
        # Mock yfinance ticker
        mock_ticker = Mock()
        mock_ticker.info = {
            'marketCap': 2_500_000_000_000,
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'longName': 'Apple Inc.'
        }
        mock_ticker_class.return_value = mock_ticker
        
        symbol_info = SymbolInfo(symbol='AAPL', company_name='Apple', exchange='NASDAQ')
        enriched = self.source.enrich_symbol_with_yfinance(symbol_info)
        
        self.assertEqual(enriched.market_cap, 2_500_000_000_000)
        self.assertEqual(enriched.sector, 'Technology')
        self.assertEqual(enriched.industry, 'Consumer Electronics')
        self.assertEqual(enriched.company_name, 'Apple Inc.')


if __name__ == '__main__':
    unittest.main()