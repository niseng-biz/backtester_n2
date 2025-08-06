"""
Yahoo Finance data client using curl_cffi for improved performance and reliability.

This module provides a more robust alternative to the yfinance library by using
curl_cffi for HTTP requests, which offers better performance and fewer rate limiting issues.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import pandas as pd
from curl_cffi import requests

from ..config import get_config_manager, with_config
from ..logger import LoggerMixin


class YahooFinanceError(Exception):
    """Custom exception for Yahoo Finance related errors."""
    pass


class RateLimitError(YahooFinanceError):
    """Exception raised when rate limit is exceeded."""
    pass


class YahooFinanceCurlClient(LoggerMixin):
    """
    Enhanced Yahoo Finance client using curl_cffi for better performance and reliability.
    
    This client provides direct access to Yahoo Finance APIs with:
    - Better rate limit handling
    - Improved error recovery
    - Faster data fetching
    - More reliable connection handling
    """
    
    # Yahoo Finance API endpoints
    BASE_URL = "https://query1.finance.yahoo.com"
    CHART_URL = f"{BASE_URL}/v8/finance/chart"
    QUOTE_URL = f"{BASE_URL}/v7/finance/quote"
    FUNDAMENTALS_URL = f"{BASE_URL}/v10/finance/quoteSummary"
    
    def __init__(self, config_manager=None):
        """
        Initialize the Yahoo Finance curl client.
        
        Args:
            config_manager: Configuration manager instance. If None, uses global instance.
        """
        if config_manager is None:
            config_manager = get_config_manager()
        self.config_manager = config_manager
        self._load_config()
        self._last_request_time = 0.0
        
        # Initialize session with curl_cffi
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _load_config(self) -> None:
        """Load configuration settings."""
        yahoo_config = self.config_manager.get("data_fetching.yahoo_finance", {})
        
        self.request_delay = yahoo_config.get("request_delay", 0.5)  # Faster with curl_cffi
        self.max_retries = yahoo_config.get("max_retries", 3)
        self.timeout = yahoo_config.get("timeout", 30)
        self.batch_size = yahoo_config.get("batch_size", 20)  # Can handle larger batches
        
        self.logger.info(f"Yahoo Finance curl client configured: delay={self.request_delay}s, "
                        f"retries={self.max_retries}, timeout={self.timeout}s")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting to avoid overwhelming Yahoo Finance API."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            url: URL to request
            params: Query parameters
            
        Returns:
            Dict[str, Any]: JSON response data
            
        Raises:
            YahooFinanceError: If request fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    impersonate="chrome110"  # Use Chrome impersonation for better success rate
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = (2 ** attempt) * self.request_delay * 2
                    self.logger.warning(f"Rate limited, waiting {wait_time:.1f} seconds")
                    time.sleep(wait_time)
                    continue
                else:
                    raise YahooFinanceError(f"HTTP {response.status_code}: {response.text}")
            
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Request attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    sleep_time = (2 ** attempt) * self.request_delay
                    self.logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
        
        raise YahooFinanceError(f"All {self.max_retries} attempts failed. Last error: {last_exception}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a stock symbol exists and is tradeable.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            bool: True if symbol is valid, False otherwise
        """
        try:
            params = {
                'symbols': symbol.upper(),
                'fields': 'symbol,regularMarketPrice'
            }
            
            data = self._make_request(self.QUOTE_URL, params)
            
            if 'quoteResponse' in data and 'result' in data['quoteResponse']:
                results = data['quoteResponse']['result']
                return len(results) > 0 and 'symbol' in results[0]
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Symbol validation failed for {symbol}: {e}")
            return False
    
    def get_stock_data(self, symbol: str, period: str = "max", 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch stock price data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            start_date: Start date for data (optional, overrides period)
            end_date: End date for data (optional, overrides period)
            
        Returns:
            pd.DataFrame: Stock price data with OHLCV columns
            
        Raises:
            YahooFinanceError: If data fetching fails
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'interval': '1d',
                'includePrePost': 'false',
                'events': 'div,splits'
            }
            
            if start_date and end_date:
                params['period1'] = int(start_date.timestamp())
                params['period2'] = int(end_date.timestamp())
            else:
                params['range'] = period
            
            url = f"{self.CHART_URL}/{symbol.upper()}"
            data = self._make_request(url, params)
            
            if 'chart' not in data or 'result' not in data['chart']:
                raise YahooFinanceError(f"No chart data found for symbol {symbol}")
            
            chart_data = data['chart']['result'][0]
            
            if 'timestamp' not in chart_data:
                raise YahooFinanceError(f"No timestamp data found for symbol {symbol}")
            
            # Extract data
            timestamps = chart_data['timestamp']
            indicators = chart_data['indicators']['quote'][0]
            
            # Create DataFrame
            df_data = {
                'open': indicators.get('open', []),
                'high': indicators.get('high', []),
                'low': indicators.get('low', []),
                'close': indicators.get('close', []),
                'volume': indicators.get('volume', [])
            }
            
            # Handle adjusted close if available
            if 'adjclose' in chart_data['indicators']:
                df_data['adj_close'] = chart_data['indicators']['adjclose'][0]['adjclose']
            else:
                df_data['adj_close'] = df_data['close']
            
            # Handle dividends and splits
            events = chart_data.get('events', {})
            dividends = [0.0] * len(timestamps)
            splits = [1.0] * len(timestamps)
            
            if 'dividends' in events:
                for div_timestamp, div_data in events['dividends'].items():
                    try:
                        idx = timestamps.index(int(div_timestamp))
                        dividends[idx] = div_data['amount']
                    except (ValueError, KeyError):
                        pass
            
            if 'splits' in events:
                for split_timestamp, split_data in events['splits'].items():
                    try:
                        idx = timestamps.index(int(split_timestamp))
                        splits[idx] = split_data['splitRatio']
                    except (ValueError, KeyError):
                        pass
            
            df_data['dividends'] = dividends
            df_data['stock_splits'] = splits
            
            # Convert timestamps to datetime index
            dates = [datetime.fromtimestamp(ts) for ts in timestamps]
            
            df = pd.DataFrame(df_data, index=dates)
            
            # Clean up column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Add symbol column
            df['symbol'] = symbol.upper()
            
            # Remove rows with all NaN values
            df = df.dropna(how='all', subset=['open', 'high', 'low', 'close'])
            
            if df.empty:
                raise YahooFinanceError(f"No valid data found for symbol {symbol}")
            
            self.logger.info(f"Fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            error_msg = f"Failed to fetch stock data for {symbol}: {e}"
            self.logger.error(error_msg)
            raise YahooFinanceError(error_msg)
    
    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch financial data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dict[str, Any]: Financial data including income statement, balance sheet, and cash flow
            
        Raises:
            YahooFinanceError: If data fetching fails
        """
        try:
            modules = [
                'incomeStatementHistory',
                'balanceSheetHistory', 
                'cashflowStatementHistory',
                'defaultKeyStatistics',
                'financialData',
                'summaryProfile'
            ]
            
            params = {
                'symbol': symbol.upper(),
                'modules': ','.join(modules)
            }
            
            url = f"{self.FUNDAMENTALS_URL}/{symbol.upper()}"
            data = self._make_request(url, params)
            
            if 'quoteSummary' not in data or 'result' not in data['quoteSummary']:
                raise YahooFinanceError(f"No financial data found for symbol {symbol}")
            
            result = data['quoteSummary']['result'][0]
            
            financial_data = {
                'symbol': symbol.upper(),
                'income_statements': result.get('incomeStatementHistory', {}),
                'balance_sheets': result.get('balanceSheetHistory', {}),
                'cash_flows': result.get('cashflowStatementHistory', {}),
                'key_statistics': result.get('defaultKeyStatistics', {}),
                'financial_data': result.get('financialData', {}),
                'profile': result.get('summaryProfile', {})
            }
            
            self.logger.info(f"Fetched financial data for {symbol}")
            return financial_data
            
        except Exception as e:
            error_msg = f"Failed to fetch financial data for {symbol}: {e}"
            self.logger.error(error_msg)
            raise YahooFinanceError(error_msg)
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch company information from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dict[str, Any]: Company information including name, sector, industry, etc.
            
        Raises:
            YahooFinanceError: If data fetching fails
        """
        try:
            modules = ['summaryProfile', 'price', 'defaultKeyStatistics']
            
            params = {
                'symbol': symbol.upper(),
                'modules': ','.join(modules)
            }
            
            url = f"{self.FUNDAMENTALS_URL}/{symbol.upper()}"
            data = self._make_request(url, params)
            
            if 'quoteSummary' not in data or 'result' not in data['quoteSummary']:
                raise YahooFinanceError(f"No company info found for symbol {symbol}")
            
            result = data['quoteSummary']['result'][0]
            
            company_info = {
                'symbol': symbol.upper(),
                'profile': result.get('summaryProfile', {}),
                'price': result.get('price', {}),
                'statistics': result.get('defaultKeyStatistics', {})
            }
            
            self.logger.info(f"Fetched company info for {symbol}")
            return company_info
            
        except Exception as e:
            error_msg = f"Failed to fetch company info for {symbol}: {e}"
            self.logger.error(error_msg)
            raise YahooFinanceError(error_msg)
    
    def get_incremental_data(self, symbol: str, last_date: datetime) -> pd.DataFrame:
        """
        Fetch incremental stock data since the last update.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            last_date: Last date in the database
            
        Returns:
            pd.DataFrame: New stock price data since last_date
            
        Raises:
            YahooFinanceError: If data fetching fails
        """
        try:
            # Add one day to last_date to avoid duplicates
            start_date = last_date + timedelta(days=1)
            end_date = datetime.now()
            
            # Only fetch if there's a meaningful time gap
            if start_date >= end_date:
                self.logger.info(f"No new data to fetch for {symbol}")
                return pd.DataFrame()
            
            return self.get_stock_data(symbol, start_date=start_date, end_date=end_date)
            
        except Exception as e:
            error_msg = f"Failed to fetch incremental data for {symbol}: {e}"
            self.logger.error(error_msg)
            raise YahooFinanceError(error_msg)
    
    def fetch_multiple_symbols(self, symbols: List[str], period: str = "max") -> Dict[str, pd.DataFrame]:
        """
        Fetch stock data for multiple symbols with batch processing.
        
        Args:
            symbols: List of stock symbols
            period: Time period for data fetching
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping symbols to their data
        """
        results = {}
        failed_symbols = []
        
        # Process symbols in batches
        for i in range(0, len(symbols), self.batch_size):
            batch = symbols[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}: {batch}")
            
            for symbol in batch:
                try:
                    data = self.get_stock_data(symbol, period=period)
                    results[symbol] = data
                except YahooFinanceError as e:
                    self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                    failed_symbols.append(symbol)
        
        if failed_symbols:
            self.logger.warning(f"Failed to fetch data for symbols: {failed_symbols}")
        
        self.logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def __del__(self):
        """Clean up session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()