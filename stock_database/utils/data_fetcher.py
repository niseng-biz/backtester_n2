"""
Data fetching orchestration for managing multiple stock data retrieval operations.

This module provides the DataFetcher class that orchestrates data fetching operations
with support for parallel processing, incremental updates, and error recovery.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config import get_config_manager
from ..database_factory import DatabaseManager
from ..logger import LoggerMixin
from ..models.company_info import CompanyInfo
from ..models.curl_transformer import CurlDataTransformer
from ..models.financial_data import FinancialData
from ..models.stock_data import StockData
from ..models.transformer import DataTransformer
from ..models.validation import DataValidator
from .yahoo_finance_client import YahooFinanceClient, YahooFinanceError
from .yahoo_finance_curl_client import YahooFinanceCurlClient


class DataFetchError(Exception):
    """Exception raised during data fetching operations."""
    pass


class DataFetcher(LoggerMixin):
    """
    Orchestrates data fetching operations with parallel processing and error recovery.
    
    This class manages the fetching of stock data, financial data, and company information
    from Yahoo Finance with support for:
    - Parallel processing of multiple symbols
    - Incremental updates (fetching only new data)
    - Batch processing with configurable batch sizes
    - Error recovery and retry mechanisms
    - Progress tracking and reporting
    """
    
    def __init__(self, config_manager=None, db_manager=None, yahoo_client=None, use_curl_client=None):
        """
        Initialize the DataFetcher.
        
        Args:
            config_manager: Configuration manager instance
            db_manager: MongoDB manager instance
            yahoo_client: Yahoo Finance client instance
            use_curl_client: Whether to use curl_cffi client (None=auto from config, True=force curl_cffi, False=force yfinance)
        """
        self.config_manager = config_manager or get_config_manager()
        self.db_manager = db_manager or DatabaseManager(self.config_manager)
        
        # Choose client based on configuration
        if yahoo_client:
            self.yahoo_client = yahoo_client
            self.use_curl_client = isinstance(yahoo_client, YahooFinanceCurlClient)
        else:
            # Determine which client to use
            if use_curl_client is None:
                # Read from configuration file (default: True for production)
                self.use_curl_client = self.config_manager.get("data_fetching.use_curl_client", True)
            else:
                self.use_curl_client = use_curl_client
            
            if self.use_curl_client:
                self.yahoo_client = YahooFinanceCurlClient(self.config_manager)
            else:
                self.yahoo_client = YahooFinanceClient(self.config_manager)
        
        # Initialize data processing components
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.curl_transformer = CurlDataTransformer()
        
        # Load configuration
        self._load_config()
        
        # Track fetching statistics
        self.stats = {
            'symbols_processed': 0,
            'symbols_successful': 0,
            'symbols_failed': 0,
            'records_fetched': 0,
            'records_inserted': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
    
    def _load_config(self) -> None:
        """Load configuration settings for data fetching."""
        fetching_config = self.config_manager.get("data_fetching", {})
        yahoo_config = fetching_config.get("yahoo_finance", {})
        
        # Parallel processing settings (disable for SQLite)
        db_type = self.config_manager.get("database.type", "sqlite")
        if db_type == "sqlite":
            self.max_workers = 1  # SQLite doesn't handle multi-threading well
        else:
            self.max_workers = fetching_config.get("max_workers", 4)
        self.batch_size = yahoo_config.get("batch_size", 10)
        
        # Error handling settings
        self.max_retries = yahoo_config.get("max_retries", 3)
        self.retry_delay = yahoo_config.get("retry_delay", 5.0)
        
        # Data fetching settings
        self.incremental_update = fetching_config.get("incremental_update", True)
        self.fetch_financial_data_enabled = fetching_config.get("fetch_financial_data", True)
        self.fetch_company_info_enabled = fetching_config.get("fetch_company_info", True)
        
        # Progress reporting
        self.progress_interval = fetching_config.get("progress_interval", 10)
        
        client_type = "curl_cffi" if self.use_curl_client else "yfinance"
        self.logger.info(f"DataFetcher configured: client={client_type}, max_workers={self.max_workers}, "
                        f"batch_size={self.batch_size}, incremental={self.incremental_update}")
    
    def reset_stats(self) -> None:
        """Reset fetching statistics."""
        self.stats = {
            'symbols_processed': 0,
            'symbols_successful': 0,
            'symbols_failed': 0,
            'records_fetched': 0,
            'records_inserted': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current fetching statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing fetching statistics
        """
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        elif stats['start_time']:
            stats['duration'] = (datetime.now() - stats['start_time']).total_seconds()
        else:
            stats['duration'] = 0
        
        return stats
    
    def fetch_stock_data(self, symbols: List[str], force_full_update: bool = False) -> Dict[str, bool]:
        """
        Fetch stock data for multiple symbols with parallel processing.
        
        Args:
            symbols: List of stock symbols to fetch
            force_full_update: If True, fetch all historical data regardless of existing data
            
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to success status
        """
        self.logger.info(f"Starting stock data fetch for {len(symbols)} symbols")
        self.reset_stats()
        self.stats['start_time'] = datetime.now()
        
        # Ensure database connection
        if not self.db_manager.is_connected():
            self.db_manager.connect()
        
        results = {}
        
        try:
            # Process symbols in batches with parallel processing
            for batch_start in range(0, len(symbols), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(symbols))
                batch_symbols = symbols[batch_start:batch_end]
                
                self.logger.info(f"Processing batch {batch_start//self.batch_size + 1}: "
                               f"symbols {batch_start+1}-{batch_end} of {len(symbols)}")
                
                batch_results = self._fetch_stock_data_batch(batch_symbols, force_full_update)
                results.update(batch_results)
                
                # Report progress
                if batch_end % self.progress_interval == 0 or batch_end == len(symbols):
                    self._report_progress(batch_end, len(symbols))
        
        except Exception as e:
            self.logger.error(f"Error during stock data fetching: {e}")
            self.stats['errors'].append(f"Batch processing error: {e}")
        
        finally:
            self.stats['end_time'] = datetime.now()
            self._log_final_stats()
        
        return results
    
    def _fetch_stock_data_batch(self, symbols: List[str], force_full_update: bool) -> Dict[str, bool]:
        """
        Fetch stock data for a batch of symbols using parallel processing.
        
        Args:
            symbols: List of symbols in the batch
            force_full_update: Whether to force full historical data fetch
            
        Returns:
            Dict[str, bool]: Results for the batch
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks for parallel execution
            future_to_symbol = {
                executor.submit(self._fetch_single_stock_data, symbol, force_full_update): symbol
                for symbol in symbols
            }
            
            # Process completed tasks
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                self.stats['symbols_processed'] += 1
                
                try:
                    success = future.result()
                    results[symbol] = success
                    
                    if success:
                        self.stats['symbols_successful'] += 1
                        self.logger.debug(f"Successfully fetched data for {symbol}")
                    else:
                        self.stats['symbols_failed'] += 1
                        self.logger.warning(f"Failed to fetch data for {symbol}")
                
                except Exception as e:
                    results[symbol] = False
                    self.stats['symbols_failed'] += 1
                    error_msg = f"Exception fetching {symbol}: {e}"
                    self.logger.error(error_msg)
                    self.stats['errors'].append(error_msg)
        
        return results
    
    def _fetch_single_stock_data(self, symbol: str, force_full_update: bool) -> bool:
        """
        Fetch stock data for a single symbol with error recovery.
        
        Args:
            symbol: Stock symbol to fetch
            force_full_update: Whether to force full historical data fetch
            
        Returns:
            bool: True if successful, False otherwise
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Determine if we need incremental or full update
                if not force_full_update and self.incremental_update:
                    last_date = self.db_manager.get_latest_stock_date(symbol)
                    if last_date:
                        # Fetch incremental data
                        self.logger.debug(f"Fetching incremental data for {symbol} since {last_date}")
                        df = self.yahoo_client.get_incremental_data(symbol, last_date)
                        
                        if df.empty:
                            self.logger.debug(f"No new data available for {symbol}")
                            return True
                    else:
                        # No existing data, fetch all historical data
                        self.logger.debug(f"Fetching full historical data for {symbol}")
                        df = self.yahoo_client.get_stock_data(symbol, period="max")
                else:
                    # Force full update
                    self.logger.debug(f"Fetching full historical data for {symbol} (forced)")
                    df = self.yahoo_client.get_stock_data(symbol, period="max")
                
                if df.empty:
                    self.logger.warning(f"No data returned for {symbol}")
                    return False
                
                # Convert to StockData objects
                stock_data_list = self.transformer.transform_stock_data(df, symbol)
                
                if not stock_data_list:
                    self.logger.warning(f"No valid stock data converted for {symbol}")
                    return False
                
                # Validate data
                valid_data = []
                for stock_data in stock_data_list:
                    if self.validator.validate_stock_data_object(stock_data):
                        valid_data.append(stock_data)
                    else:
                        self.logger.warning(f"Invalid stock data for {symbol} on {stock_data.date}")
                
                if not valid_data:
                    self.logger.warning(f"No valid stock data after validation for {symbol}")
                    return False
                
                # Store in database
                self.db_manager.upsert_stock_data(valid_data)
                
                self.stats['records_fetched'] += len(stock_data_list)
                self.stats['records_inserted'] += len(valid_data)
                
                self.logger.info(f"Successfully processed {len(valid_data)} records for {symbol}")
                return True
            
            except YahooFinanceError as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"All attempts failed for {symbol}: {e}")
                    return False
            
            except Exception as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"Unexpected error for {symbol} (attempt {attempt + 1}): {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    self.logger.error(f"Unexpected error for {symbol} after all retries: {e}")
                    return False
        
        return False
    
    def fetch_financial_data(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Fetch financial data for multiple symbols.
        
        Args:
            symbols: List of stock symbols to fetch financial data for
            
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to success status
        """
        if not self.fetch_financial_data_enabled:
            self.logger.info("Financial data fetching is disabled in configuration")
            return {symbol: False for symbol in symbols}
        
        self.logger.info(f"Starting financial data fetch for {len(symbols)} symbols")
        
        # Ensure database connection
        if not self.db_manager.is_connected():
            self.db_manager.connect()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._fetch_single_financial_data, symbol): symbol
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    success = future.result()
                    results[symbol] = success
                    
                    if success:
                        self.logger.debug(f"Successfully fetched financial data for {symbol}")
                    else:
                        self.logger.warning(f"Failed to fetch financial data for {symbol}")
                
                except Exception as e:
                    results[symbol] = False
                    self.logger.error(f"Exception fetching financial data for {symbol}: {e}")
        
        return results
    
    def _fetch_single_financial_data(self, symbol: str) -> bool:
        """
        Fetch financial data for a single symbol.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Fetch financial data from Yahoo Finance
            financial_dict = self.yahoo_client.get_financial_data(symbol)
            
            # Convert to FinancialData objects using appropriate transformer
            if self.use_curl_client:
                financial_data_list = self.curl_transformer.transform_financial_data_curl(financial_dict)
            else:
                financial_data_list = self.transformer.transform_financial_data(financial_dict)
            
            if not financial_data_list:
                self.logger.warning(f"No financial data converted for {symbol}")
                return False
            
            # Validate and store data
            valid_data = []
            for financial_data in financial_data_list:
                if self.validator.validate_financial_data_object(financial_data):
                    valid_data.append(financial_data)
                else:
                    self.logger.warning(f"Invalid financial data for {symbol} FY{financial_data.fiscal_year}")
            
            if valid_data:
                self.db_manager.upsert_financial_data(valid_data)
                self.logger.info(f"Successfully processed {len(valid_data)} financial records for {symbol}")
                return True
            else:
                self.logger.warning(f"No valid financial data after validation for {symbol}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error fetching financial data for {symbol}: {e}")
            return False
    
    def fetch_company_info(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Fetch company information for multiple symbols.
        
        Args:
            symbols: List of stock symbols to fetch company info for
            
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to success status
        """
        if not self.fetch_company_info_enabled:
            self.logger.info("Company info fetching is disabled in configuration")
            return {symbol: False for symbol in symbols}
        
        self.logger.info(f"Starting company info fetch for {len(symbols)} symbols")
        
        # Ensure database connection
        if not self.db_manager.is_connected():
            self.db_manager.connect()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._fetch_single_company_info, symbol): symbol
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    success = future.result()
                    results[symbol] = success
                    
                    if success:
                        self.logger.debug(f"Successfully fetched company info for {symbol}")
                    else:
                        self.logger.warning(f"Failed to fetch company info for {symbol}")
                
                except Exception as e:
                    results[symbol] = False
                    self.logger.error(f"Exception fetching company info for {symbol}: {e}")
        
        return results
    
    def _fetch_single_company_info(self, symbol: str) -> bool:
        """
        Fetch company information for a single symbol.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Fetch company info from Yahoo Finance
            company_dict = self.yahoo_client.get_company_info(symbol)
            
            # Convert to CompanyInfo object using appropriate transformer
            if self.use_curl_client:
                company_info = self.curl_transformer.transform_company_info_curl(company_dict)
            else:
                company_info = self.transformer.transform_company_info(company_dict)
            
            # Validate and store data
            if self.validator.validate_company_info_object(company_info):
                # Store in database
                self.db_manager.upsert_company_info([company_info])
                self.logger.info(f"Successfully processed company info for {symbol}")
                return True
            else:
                self.logger.warning(f"Invalid company info for {symbol}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {e}")
            return False
    
    def fetch_all_data(self, symbols: List[str], force_full_update: bool = False) -> Dict[str, Dict[str, bool]]:
        """
        Fetch all types of data (stock, financial, company) for multiple symbols.
        
        Args:
            symbols: List of stock symbols to fetch
            force_full_update: Whether to force full historical data fetch for stock data
            
        Returns:
            Dict[str, Dict[str, bool]]: Nested dictionary with results for each data type
        """
        self.logger.info(f"Starting comprehensive data fetch for {len(symbols)} symbols")
        
        results = {
            'stock_data': {},
            'financial_data': {},
            'company_info': {}
        }
        
        # Fetch stock data
        self.logger.info("Fetching stock data...")
        results['stock_data'] = self.fetch_stock_data(symbols, force_full_update)
        
        # Fetch financial data
        self.logger.info("Fetching financial data...")
        results['financial_data'] = self.fetch_financial_data(symbols)
        
        # Fetch company info
        self.logger.info("Fetching company information...")
        results['company_info'] = self.fetch_company_info(symbols)
        
        # Log summary
        self._log_comprehensive_summary(results)
        
        return results
    
    def schedule_incremental_update(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Schedule and execute incremental updates for symbols that need updating.
        
        This method checks which symbols need updates based on their last update time
        and only fetches data for symbols that are outdated.
        
        Args:
            symbols: List of stock symbols to check and update
            
        Returns:
            Dict[str, bool]: Dictionary mapping symbols to update success status
        """
        self.logger.info(f"Checking {len(symbols)} symbols for incremental updates")
        
        symbols_to_update = []
        
        # Check which symbols need updating
        for symbol in symbols:
            try:
                last_date = self.db_manager.get_latest_stock_date(symbol)
                if last_date is None:
                    # No data exists, needs full fetch
                    symbols_to_update.append(symbol)
                    self.logger.debug(f"{symbol}: No existing data, scheduling full fetch")
                else:
                    # Check if data is outdated (more than 1 day old for daily data)
                    days_since_update = (datetime.now() - last_date).days
                    if days_since_update > 1:
                        symbols_to_update.append(symbol)
                        self.logger.debug(f"{symbol}: Data is {days_since_update} days old, scheduling update")
                    else:
                        self.logger.debug(f"{symbol}: Data is current (last update: {last_date})")
            except Exception as e:
                self.logger.warning(f"Error checking update status for {symbol}: {e}")
                symbols_to_update.append(symbol)  # Include in update to be safe
        
        if not symbols_to_update:
            self.logger.info("All symbols are up to date, no updates needed")
            return {symbol: True for symbol in symbols}
        
        self.logger.info(f"Updating {len(symbols_to_update)} symbols: {symbols_to_update}")
        update_results = self.fetch_stock_data(symbols_to_update, force_full_update=False)
        
        # Create complete results including symbols that didn't need updates
        complete_results = {}
        for symbol in symbols:
            if symbol in symbols_to_update:
                complete_results[symbol] = update_results.get(symbol, False)
            else:
                complete_results[symbol] = True  # Already up to date
        
        return complete_results
    
    def get_update_status(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get update status information for a list of symbols.
        
        Args:
            symbols: List of stock symbols to check
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary with update status for each symbol
        """
        status_info = {}
        
        for symbol in symbols:
            try:
                last_date = self.db_manager.get_latest_stock_date(symbol)
                
                if last_date is None:
                    status_info[symbol] = {
                        'has_data': False,
                        'last_update': None,
                        'days_since_update': None,
                        'needs_update': True,
                        'update_type': 'full'
                    }
                else:
                    days_since_update = (datetime.now() - last_date).days
                    needs_update = days_since_update > 1
                    
                    status_info[symbol] = {
                        'has_data': True,
                        'last_update': last_date,
                        'days_since_update': days_since_update,
                        'needs_update': needs_update,
                        'update_type': 'incremental' if needs_update else 'none'
                    }
            except Exception as e:
                status_info[symbol] = {
                    'has_data': False,
                    'last_update': None,
                    'days_since_update': None,
                    'needs_update': True,
                    'update_type': 'full',
                    'error': str(e)
                }
        
        return status_info
    
    def _report_progress(self, completed: int, total: int) -> None:
        """
        Report progress of data fetching operation.
        
        Args:
            completed: Number of symbols completed
            total: Total number of symbols
        """
        percentage = (completed / total) * 100
        stats = self.get_stats()
        
        self.logger.info(f"Progress: {completed}/{total} symbols ({percentage:.1f}%) - "
                        f"Success: {stats['symbols_successful']}, "
                        f"Failed: {stats['symbols_failed']}, "
                        f"Records: {stats['records_inserted']}")
    
    def _log_final_stats(self) -> None:
        """Log final statistics for the fetching operation."""
        stats = self.get_stats()
        
        self.logger.info("=== Data Fetching Summary ===")
        self.logger.info(f"Duration: {stats['duration']:.2f} seconds")
        self.logger.info(f"Symbols processed: {stats['symbols_processed']}")
        self.logger.info(f"Symbols successful: {stats['symbols_successful']}")
        self.logger.info(f"Symbols failed: {stats['symbols_failed']}")
        self.logger.info(f"Records fetched: {stats['records_fetched']}")
        self.logger.info(f"Records inserted: {stats['records_inserted']}")
        
        if stats['errors']:
            self.logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Log first 5 errors
                self.logger.warning(f"  - {error}")
            if len(stats['errors']) > 5:
                self.logger.warning(f"  ... and {len(stats['errors']) - 5} more errors")
    
    def _log_comprehensive_summary(self, results: Dict[str, Dict[str, bool]]) -> None:
        """
        Log summary for comprehensive data fetching.
        
        Args:
            results: Results dictionary from fetch_all_data
        """
        self.logger.info("=== Comprehensive Data Fetch Summary ===")
        
        for data_type, type_results in results.items():
            successful = sum(1 for success in type_results.values() if success)
            total = len(type_results)
            self.logger.info(f"{data_type}: {successful}/{total} symbols successful")
    
    def get_failed_symbols(self, results: Dict[str, bool]) -> List[str]:
        """
        Get list of symbols that failed during fetching.
        
        Args:
            results: Results dictionary from fetch operation
            
        Returns:
            List[str]: List of failed symbols
        """
        return [symbol for symbol, success in results.items() if not success]
    
    def retry_failed_symbols(self, failed_symbols: List[str], force_full_update: bool = False) -> Dict[str, bool]:
        """
        Retry fetching data for symbols that previously failed.
        
        Args:
            failed_symbols: List of symbols that failed
            force_full_update: Whether to force full historical data fetch
            
        Returns:
            Dict[str, bool]: Results for retry operation
        """
        if not failed_symbols:
            self.logger.info("No failed symbols to retry")
            return {}
        
        self.logger.info(f"Retrying data fetch for {len(failed_symbols)} failed symbols")
        return self.fetch_stock_data(failed_symbols, force_full_update)
    
    def batch_recovery_fetch(self, symbols: List[str], max_attempts: int = 3) -> Dict[str, Any]:
        """
        Perform batch fetching with automatic recovery for failed symbols.
        
        This method attempts to fetch data for all symbols, then retries failed symbols
        up to max_attempts times with exponential backoff.
        
        Args:
            symbols: List of stock symbols to fetch
            max_attempts: Maximum number of retry attempts for failed symbols
            
        Returns:
            Dict[str, Any]: Comprehensive results including final status and retry history
        """
        self.logger.info(f"Starting batch recovery fetch for {len(symbols)} symbols (max {max_attempts} attempts)")
        
        results = {
            'final_results': {},
            'attempt_history': [],
            'successful_symbols': set(),
            'permanently_failed_symbols': set(),
            'total_attempts': 0
        }
        
        remaining_symbols = symbols.copy()
        attempt = 1
        
        while remaining_symbols and attempt <= max_attempts:
            self.logger.info(f"Attempt {attempt}/{max_attempts}: Fetching {len(remaining_symbols)} symbols")
            
            # Fetch data for remaining symbols
            attempt_results = self.fetch_stock_data(remaining_symbols, force_full_update=False)
            
            # Record attempt results
            results['attempt_history'].append({
                'attempt': attempt,
                'symbols': remaining_symbols.copy(),
                'results': attempt_results.copy(),
                'successful': sum(1 for success in attempt_results.values() if success),
                'failed': sum(1 for success in attempt_results.values() if not success)
            })
            
            # Update final results and track successful symbols
            for symbol, success in attempt_results.items():
                results['final_results'][symbol] = success
                if success:
                    results['successful_symbols'].add(symbol)
            
            # Prepare for next attempt with only failed symbols
            remaining_symbols = [symbol for symbol, success in attempt_results.items() if not success]
            
            if remaining_symbols and attempt < max_attempts:
                # Exponential backoff before retry
                backoff_time = (2 ** (attempt - 1)) * self.retry_delay
                self.logger.info(f"Waiting {backoff_time:.1f} seconds before retry attempt {attempt + 1}")
                time.sleep(backoff_time)
            
            attempt += 1
        
        # Mark permanently failed symbols
        results['permanently_failed_symbols'] = set(remaining_symbols)
        results['total_attempts'] = attempt - 1
        
        # Log final summary
        self._log_batch_recovery_summary(results)
        
        return results
    
    def _log_batch_recovery_summary(self, results: Dict[str, Any]) -> None:
        """
        Log summary of batch recovery operation.
        
        Args:
            results: Results from batch_recovery_fetch
        """
        total_symbols = len(results['final_results'])
        successful_count = len(results['successful_symbols'])
        failed_count = len(results['permanently_failed_symbols'])
        
        self.logger.info("=== Batch Recovery Summary ===")
        self.logger.info(f"Total symbols: {total_symbols}")
        self.logger.info(f"Successful: {successful_count}")
        self.logger.info(f"Permanently failed: {failed_count}")
        self.logger.info(f"Total attempts made: {results['total_attempts']}")
        
        if results['permanently_failed_symbols']:
            self.logger.warning(f"Permanently failed symbols: {list(results['permanently_failed_symbols'])}")
        
        # Log attempt history
        for attempt_info in results['attempt_history']:
            self.logger.info(f"Attempt {attempt_info['attempt']}: "
                           f"{attempt_info['successful']}/{len(attempt_info['symbols'])} successful")
    
    def validate_symbols_before_fetch(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate symbols before fetching to avoid unnecessary API calls.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            Tuple[List[str], List[str]]: (valid_symbols, invalid_symbols)
        """
        self.logger.info(f"Validating {len(symbols)} symbols before fetch")
        
        valid_symbols = []
        invalid_symbols = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.yahoo_client.validate_symbol, symbol): symbol
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    is_valid = future.result()
                    if is_valid:
                        valid_symbols.append(symbol)
                        self.logger.debug(f"Symbol {symbol} is valid")
                    else:
                        invalid_symbols.append(symbol)
                        self.logger.warning(f"Symbol {symbol} is invalid")
                
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.error(f"Error validating symbol {symbol}: {e}")
        
        self.logger.info(f"Validation complete: {len(valid_symbols)} valid, {len(invalid_symbols)} invalid")
        
        if invalid_symbols:
            self.logger.warning(f"Invalid symbols will be skipped: {invalid_symbols}")
        
        return valid_symbols, invalid_symbols