"""
Unit tests for the DataFetcher class.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pandas as pd

from stock_database.models.stock_data import StockData
from stock_database.utils.data_fetcher import DataFetcher, DataFetchError
from stock_database.utils.yahoo_finance_curl_client import \
    YahooFinanceCurlClient


class TestDataFetcher(unittest.TestCase):
    """Test cases for DataFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_config = Mock()
        self.mock_db_manager = Mock()
        self.mock_yahoo_client = Mock()
        
        # Configure mock config
        self.mock_config.get.return_value = {
            'max_workers': 2,
            'incremental_update': True,
            'fetch_financial_data': True,
            'fetch_company_info': True,
            'progress_interval': 5,
            'yahoo_finance': {
                'batch_size': 5,
                'max_retries': 2,
                'retry_delay': 1.0
            }
        }
        
        # Configure mock database manager
        self.mock_db_manager.is_connected.return_value = True
        self.mock_db_manager.get_latest_stock_date.return_value = None
        
        # Create DataFetcher instance with mocked dependencies
        self.data_fetcher = DataFetcher(
            config_manager=self.mock_config,
            db_manager=self.mock_db_manager,
            yahoo_client=self.mock_yahoo_client,
            use_curl_client=False  # Use traditional client for tests
        )
    
    def test_initialization(self):
        """Test DataFetcher initialization."""
        self.assertIsNotNone(self.data_fetcher)
        self.assertEqual(self.data_fetcher.max_workers, 2)
        self.assertEqual(self.data_fetcher.batch_size, 5)
        self.assertTrue(self.data_fetcher.incremental_update)
    
    def test_reset_stats(self):
        """Test statistics reset functionality."""
        # Modify some stats
        self.data_fetcher.stats['symbols_processed'] = 5
        self.data_fetcher.stats['symbols_successful'] = 3
        
        # Reset stats
        self.data_fetcher.reset_stats()
        
        # Verify reset
        self.assertEqual(self.data_fetcher.stats['symbols_processed'], 0)
        self.assertEqual(self.data_fetcher.stats['symbols_successful'], 0)
        self.assertEqual(self.data_fetcher.stats['symbols_failed'], 0)
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        # Set some stats
        self.data_fetcher.stats['symbols_processed'] = 10
        self.data_fetcher.stats['symbols_successful'] = 8
        self.data_fetcher.stats['symbols_failed'] = 2
        self.data_fetcher.stats['start_time'] = datetime.now() - timedelta(seconds=30)
        self.data_fetcher.stats['end_time'] = datetime.now()
        
        stats = self.data_fetcher.get_stats()
        
        self.assertEqual(stats['symbols_processed'], 10)
        self.assertEqual(stats['symbols_successful'], 8)
        self.assertEqual(stats['symbols_failed'], 2)
        self.assertIn('duration', stats)
        self.assertGreater(stats['duration'], 0)
    
    def test_fetch_stock_data_success(self):
        """Test successful stock data fetching."""
        # Mock the _fetch_single_stock_data method directly to avoid ThreadPoolExecutor complexity
        with patch.object(self.data_fetcher, '_fetch_single_stock_data') as mock_fetch:
            mock_fetch.return_value = True
            
            # Test fetch_stock_data
            symbols = ['AAPL']
            results = self.data_fetcher.fetch_stock_data(symbols)
            
            # Verify results
            self.assertIn('AAPL', results)
            self.assertTrue(results['AAPL'])
            
            # Verify the method was called
            mock_fetch.assert_called_once_with('AAPL', False)
    
    def test_get_failed_symbols(self):
        """Test failed symbols identification."""
        results = {
            'AAPL': True,
            'GOOGL': False,
            'MSFT': True,
            'INVALID': False
        }
        
        failed_symbols = self.data_fetcher.get_failed_symbols(results)
        
        self.assertEqual(set(failed_symbols), {'GOOGL', 'INVALID'})
    
    def test_incremental_update_logic(self):
        """Test incremental update logic."""
        # Mock existing data
        last_date = datetime.now() - timedelta(days=5)
        self.mock_db_manager.get_latest_stock_date.return_value = last_date
        
        # Mock incremental data
        mock_df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000]
        }, index=[datetime.now()])
        
        self.data_fetcher.yahoo_client.get_incremental_data.return_value = mock_df
        
        # Test that incremental data is requested
        symbol = 'AAPL'
        self.data_fetcher._fetch_single_stock_data(symbol, force_full_update=False)
        
        # Verify incremental data was requested
        self.data_fetcher.yahoo_client.get_incremental_data.assert_called_once_with(symbol, last_date)
    
    def test_force_full_update(self):
        """Test force full update functionality."""
        # Mock full historical data
        mock_df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000000, 1100000]
        }, index=[datetime.now() - timedelta(days=1), datetime.now()])
        
        self.data_fetcher.yahoo_client.get_stock_data.return_value = mock_df
        
        # Test force full update
        symbol = 'AAPL'
        self.data_fetcher._fetch_single_stock_data(symbol, force_full_update=True)
        
        # Verify full data was requested
        self.data_fetcher.yahoo_client.get_stock_data.assert_called_once_with(symbol, period="max")
    
    def test_batch_processing(self):
        """Test batch processing logic."""
        # Set small batch size for testing
        self.data_fetcher.batch_size = 2
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']  # 4 symbols, should create 2 batches
        
        with patch.object(self.data_fetcher, '_fetch_stock_data_batch') as mock_batch:
            mock_batch.return_value = {'AAPL': True, 'GOOGL': True}
            
            results = self.data_fetcher.fetch_stock_data(symbols)
            
            # Verify batch method was called twice (2 batches)
            self.assertEqual(mock_batch.call_count, 2)
            
            # Verify correct batch sizes were used
            call_args_list = mock_batch.call_args_list
            self.assertEqual(len(call_args_list[0][0][0]), 2)  # First batch: 2 symbols
            self.assertEqual(len(call_args_list[1][0][0]), 2)  # Second batch: 2 symbols
    
    def test_error_recovery(self):
        """Test error recovery and retry logic."""
        from stock_database.utils.yahoo_finance_client import YahooFinanceError

        # Mock Yahoo Finance error on first attempt, success on second
        self.data_fetcher.yahoo_client.get_stock_data.side_effect = [
            YahooFinanceError("Network error"),
            pd.DataFrame({
                'open': [100.0],
                'high': [102.0],
                'low': [99.0],
                'close': [101.0],
                'volume': [1000000]
            }, index=[datetime.now()])
        ]
        
        # Mock successful transformation
        mock_stock_data = [StockData(
            symbol='AAPL',
            date=datetime.now(),
            open=100.0, high=102.0, low=99.0, close=101.0, volume=1000000,
            adjusted_close=101.0
        )]
        
        self.data_fetcher.transformer.transform_stock_data.return_value = mock_stock_data
        self.data_fetcher.validator.validate_stock_data_object.return_value = True
        
        # Test error recovery
        result = self.data_fetcher._fetch_single_stock_data('AAPL', force_full_update=False)
        
        # Should succeed after retry
        self.assertTrue(result)
        
        # Verify retry occurred
        self.assertEqual(self.data_fetcher.yahoo_client.get_stock_data.call_count, 2)
    
    def test_schedule_incremental_update(self):
        """Test scheduled incremental update functionality."""
        # Mock database responses for different scenarios
        self.mock_db_manager.get_latest_stock_date.side_effect = [
            None,  # AAPL: No existing data
            datetime.now() - timedelta(days=2),  # GOOGL: Outdated data
            datetime.now(),  # MSFT: Current data
        ]
        
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        with patch.object(self.data_fetcher, 'fetch_stock_data') as mock_fetch:
            mock_fetch.return_value = {'AAPL': True, 'GOOGL': True}
            
            results = self.data_fetcher.schedule_incremental_update(symbols)
            
            # Should only fetch AAPL and GOOGL (MSFT is current)
            mock_fetch.assert_called_once_with(['AAPL', 'GOOGL'], force_full_update=False)
            
            # Should return success for all symbols
            self.assertIn('AAPL', results)
            self.assertIn('GOOGL', results)
            self.assertIn('MSFT', results)
    
    def test_get_update_status(self):
        """Test update status checking functionality."""
        # Mock database responses
        self.mock_db_manager.get_latest_stock_date.side_effect = [
            None,  # AAPL: No data
            datetime.now() - timedelta(days=3),  # GOOGL: Outdated
            datetime.now(),  # MSFT: Current
        ]
        
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        status_info = self.data_fetcher.get_update_status(symbols)
        
        # Verify status for each symbol
        self.assertFalse(status_info['AAPL']['has_data'])
        self.assertTrue(status_info['AAPL']['needs_update'])
        self.assertEqual(status_info['AAPL']['update_type'], 'full')
        
        self.assertTrue(status_info['GOOGL']['has_data'])
        self.assertTrue(status_info['GOOGL']['needs_update'])
        self.assertEqual(status_info['GOOGL']['update_type'], 'incremental')
        
        self.assertTrue(status_info['MSFT']['has_data'])
        self.assertFalse(status_info['MSFT']['needs_update'])
        self.assertEqual(status_info['MSFT']['update_type'], 'none')
    
    def test_validate_symbols_before_fetch(self):
        """Test symbol validation before fetching."""
        # Mock validation results
        self.data_fetcher.yahoo_client.validate_symbol.side_effect = [
            True,   # AAPL: Valid
            False,  # INVALID: Invalid
            True,   # GOOGL: Valid
        ]
        
        symbols = ['AAPL', 'INVALID', 'GOOGL']
        valid_symbols, invalid_symbols = self.data_fetcher.validate_symbols_before_fetch(symbols)
        
        self.assertEqual(set(valid_symbols), {'AAPL', 'GOOGL'})
        self.assertEqual(set(invalid_symbols), {'INVALID'})
    
    def test_batch_recovery_fetch(self):
        """Test batch recovery fetch with retries."""
        # Mock fetch results: first attempt fails for GOOGL, second succeeds
        with patch.object(self.data_fetcher, 'fetch_stock_data') as mock_fetch:
            mock_fetch.side_effect = [
                {'AAPL': True, 'GOOGL': False},  # First attempt
                {'GOOGL': True}  # Retry attempt
            ]
            
            # Mock sleep to speed up test
            with patch('time.sleep'):
                results = self.data_fetcher.batch_recovery_fetch(['AAPL', 'GOOGL'], max_attempts=2)
            
            # Verify results
            self.assertEqual(results['final_results']['AAPL'], True)
            self.assertEqual(results['final_results']['GOOGL'], True)
            self.assertEqual(len(results['successful_symbols']), 2)
            self.assertEqual(len(results['permanently_failed_symbols']), 0)
            self.assertEqual(results['total_attempts'], 2)
            
            # Verify fetch was called twice
            self.assertEqual(mock_fetch.call_count, 2)
    
    def test_curl_client_initialization(self):
        """Test DataFetcher initialization with curl client."""
        # Create DataFetcher with curl client enabled
        curl_data_fetcher = DataFetcher(
            config_manager=self.mock_config,
            db_manager=self.mock_db_manager,
            use_curl_client=True
        )
        
        # Verify curl client is used
        self.assertTrue(curl_data_fetcher.use_curl_client)
        self.assertIsInstance(curl_data_fetcher.yahoo_client, YahooFinanceCurlClient)
    
    def test_default_client_from_config(self):
        """Test DataFetcher uses curl client by default from config."""
        # Mock config to return True for use_curl_client
        self.mock_config.get.side_effect = lambda key, default=None: {
            'data_fetching': {
                'max_workers': 2,
                'incremental_update': True,
                'fetch_financial_data': True,
                'fetch_company_info': True,
                'progress_interval': 5,
                'yahoo_finance': {
                    'batch_size': 5,
                    'max_retries': 2,
                    'retry_delay': 1.0
                }
            },
            'data_fetching.use_curl_client': True
        }.get(key, default)
        
        # Create DataFetcher without specifying client type
        default_data_fetcher = DataFetcher(
            config_manager=self.mock_config,
            db_manager=self.mock_db_manager
        )
        
        # Verify curl client is used by default
        self.assertTrue(default_data_fetcher.use_curl_client)
        self.assertIsInstance(default_data_fetcher.yahoo_client, YahooFinanceCurlClient)
    
    def test_traditional_client_initialization(self):
        """Test DataFetcher initialization with traditional client."""
        # Create DataFetcher with traditional client
        traditional_data_fetcher = DataFetcher(
            config_manager=self.mock_config,
            db_manager=self.mock_db_manager,
            use_curl_client=False
        )
        
        # Verify traditional client is used
        self.assertFalse(traditional_data_fetcher.use_curl_client)
        self.assertNotIsInstance(traditional_data_fetcher.yahoo_client, YahooFinanceCurlClient)


if __name__ == '__main__':
    unittest.main()