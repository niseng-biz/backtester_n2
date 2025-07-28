"""
Unit tests for the YahooFinanceCurlClient class.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pandas as pd

from stock_database.utils.yahoo_finance_curl_client import (
    YahooFinanceCurlClient, YahooFinanceError)


class TestYahooFinanceCurlClient(unittest.TestCase):
    """Test cases for YahooFinanceCurlClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_config = Mock()
        
        # Configure mock config
        self.mock_config.get.return_value = {
            'request_delay': 0.1,
            'max_retries': 2,
            'timeout': 10,
            'batch_size': 5
        }
        
        # Create client instance with mocked config
        self.client = YahooFinanceCurlClient(config_manager=self.mock_config)
    
    def test_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.request_delay, 0.1)
        self.assertEqual(self.client.max_retries, 2)
        self.assertEqual(self.client.timeout, 10)
        self.assertEqual(self.client.batch_size, 5)
    
    @patch('stock_database.utils.yahoo_finance_curl_client.requests.Session')
    def test_make_request_success(self, mock_session_class):
        """Test successful HTTP request."""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'test': 'data'}
        
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Create new client to use mocked session
        client = YahooFinanceCurlClient(config_manager=self.mock_config)
        client.session = mock_session
        
        # Test request
        result = client._make_request('http://test.com', {'param': 'value'})
        
        self.assertEqual(result, {'test': 'data'})
        mock_session.get.assert_called_once()
    
    @patch('stock_database.utils.yahoo_finance_curl_client.requests.Session')
    def test_make_request_retry_on_429(self, mock_session_class):
        """Test retry logic on rate limit (429) response."""
        # Mock session and responses
        mock_session = Mock()
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'success': 'data'}
        
        mock_session.get.side_effect = [mock_response_429, mock_response_200]
        mock_session_class.return_value = mock_session
        
        # Create new client to use mocked session
        client = YahooFinanceCurlClient(config_manager=self.mock_config)
        client.session = mock_session
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = client._make_request('http://test.com')
        
        self.assertEqual(result, {'success': 'data'})
        self.assertEqual(mock_session.get.call_count, 2)
    
    def test_validate_symbol_success(self):
        """Test successful symbol validation."""
        # Mock successful response
        mock_response_data = {
            'quoteResponse': {
                'result': [{'symbol': 'AAPL', 'regularMarketPrice': 150.0}]
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response_data):
            result = self.client.validate_symbol('AAPL')
            self.assertTrue(result)
    
    def test_validate_symbol_failure(self):
        """Test symbol validation failure."""
        # Mock empty response
        mock_response_data = {
            'quoteResponse': {
                'result': []
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response_data):
            result = self.client.validate_symbol('INVALID')
            self.assertFalse(result)
    
    def test_get_stock_data_success(self):
        """Test successful stock data fetching."""
        # Mock chart response
        mock_chart_data = {
            'chart': {
                'result': [{
                    'timestamp': [1640995200, 1641081600],  # 2022-01-01, 2022-01-02
                    'indicators': {
                        'quote': [{
                            'open': [100.0, 101.0],
                            'high': [102.0, 103.0],
                            'low': [99.0, 100.0],
                            'close': [101.0, 102.0],
                            'volume': [1000000, 1100000]
                        }],
                        'adjclose': [{
                            'adjclose': [101.0, 102.0]
                        }]
                    },
                    'events': {}
                }]
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_chart_data):
            df = self.client.get_stock_data('AAPL')
            
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 2)
            self.assertIn('open', df.columns)
            self.assertIn('high', df.columns)
            self.assertIn('low', df.columns)
            self.assertIn('close', df.columns)
            self.assertIn('volume', df.columns)
    
    def test_get_stock_data_with_date_range(self):
        """Test stock data fetching with date range."""
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2022, 1, 31)
        
        mock_chart_data = {
            'chart': {
                'result': [{
                    'timestamp': [1640995200],
                    'indicators': {
                        'quote': [{
                            'open': [100.0],
                            'high': [102.0],
                            'low': [99.0],
                            'close': [101.0],
                            'volume': [1000000]
                        }]
                    },
                    'events': {}
                }]
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_chart_data) as mock_request:
            df = self.client.get_stock_data('AAPL', start_date=start_date, end_date=end_date)
            
            # Verify that period1 and period2 parameters were used
            call_args = mock_request.call_args
            if len(call_args) > 1 and 'params' in call_args[1]:
                params = call_args[1]['params']
            else:
                # Check positional arguments
                params = call_args[0][1] if len(call_args[0]) > 1 else {}
            
            self.assertIn('period1', params)
            self.assertIn('period2', params)
            self.assertEqual(params['period1'], int(start_date.timestamp()))
            self.assertEqual(params['period2'], int(end_date.timestamp()))
    
    def test_get_financial_data_success(self):
        """Test successful financial data fetching."""
        mock_financial_data = {
            'quoteSummary': {
                'result': [{
                    'incomeStatementHistory': {
                        'incomeStatementHistory': [{
                            'endDate': {'raw': 1640995200},
                            'totalRevenue': {'raw': 1000000000},
                            'netIncome': {'raw': 100000000}
                        }]
                    },
                    'balanceSheetHistory': {
                        'balanceSheetHistory': [{
                            'endDate': {'raw': 1640995200},
                            'totalAssets': {'raw': 5000000000}
                        }]
                    },
                    'cashflowStatementHistory': {
                        'cashFlowStatementHistory': [{
                            'endDate': {'raw': 1640995200},
                            'freeCashFlow': {'raw': 50000000}
                        }]
                    },
                    'defaultKeyStatistics': {
                        'trailingEps': {'raw': 5.0}
                    },
                    'financialData': {
                        'returnOnEquity': {'raw': 0.15}
                    },
                    'summaryProfile': {
                        'sector': 'Technology'
                    }
                }]
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_financial_data):
            result = self.client.get_financial_data('AAPL')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['symbol'], 'AAPL')
            self.assertIn('income_statements', result)
            self.assertIn('balance_sheets', result)
            self.assertIn('cash_flows', result)
    
    def test_get_company_info_success(self):
        """Test successful company info fetching."""
        mock_company_data = {
            'quoteSummary': {
                'result': [{
                    'summaryProfile': {
                        'longName': 'Apple Inc.',
                        'sector': 'Technology',
                        'industry': 'Consumer Electronics',
                        'country': 'United States'
                    },
                    'price': {
                        'marketCap': {'raw': 3000000000000},
                        'currency': 'USD',
                        'exchangeName': 'NASDAQ'
                    },
                    'defaultKeyStatistics': {
                        'marketCap': {'raw': 3000000000000}
                    }
                }]
            }
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_company_data):
            result = self.client.get_company_info('AAPL')
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['symbol'], 'AAPL')
            self.assertIn('profile', result)
            self.assertIn('price', result)
            self.assertIn('statistics', result)
    
    def test_get_incremental_data(self):
        """Test incremental data fetching."""
        last_date = datetime(2022, 1, 1)
        
        mock_chart_data = {
            'chart': {
                'result': [{
                    'timestamp': [1641081600],  # 2022-01-02
                    'indicators': {
                        'quote': [{
                            'open': [101.0],
                            'high': [103.0],
                            'low': [100.0],
                            'close': [102.0],
                            'volume': [1100000]
                        }]
                    },
                    'events': {}
                }]
            }
        }
        
        with patch.object(self.client, 'get_stock_data', return_value=pd.DataFrame({'close': [102.0]})) as mock_get_stock:
            result = self.client.get_incremental_data('AAPL', last_date)
            
            # Verify get_stock_data was called with correct date range
            call_args = mock_get_stock.call_args
            start_date_arg = call_args[1]['start_date']
            self.assertEqual(start_date_arg.date(), (last_date + timedelta(days=1)).date())
    
    def test_get_incremental_data_no_new_data(self):
        """Test incremental data fetching when no new data is available."""
        last_date = datetime.now()  # Current date, so no new data
        
        result = self.client.get_incremental_data('AAPL', last_date)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)
    
    def test_fetch_multiple_symbols(self):
        """Test fetching multiple symbols."""
        symbols = ['AAPL', 'GOOGL']
        
        # Mock successful responses for both symbols
        mock_df = pd.DataFrame({'close': [100.0, 101.0]})
        
        with patch.object(self.client, 'get_stock_data', return_value=mock_df):
            results = self.client.fetch_multiple_symbols(symbols)
            
            self.assertEqual(len(results), 2)
            self.assertIn('AAPL', results)
            self.assertIn('GOOGL', results)
    
    def test_error_handling(self):
        """Test error handling for failed requests."""
        with patch.object(self.client, '_make_request', side_effect=YahooFinanceError("Test error")):
            with self.assertRaises(YahooFinanceError):
                self.client.get_stock_data('AAPL')


if __name__ == '__main__':
    unittest.main()