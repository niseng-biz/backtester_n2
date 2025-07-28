"""
Yahoo Finance data client for fetching stock data, financial data, and company information.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
from yfinance import Ticker

from ..config import get_config_manager
from ..logger import LoggerMixin
from ..models.company_info import CompanyInfo
from ..models.financial_data import FinancialData
from ..models.stock_data import StockData


class YahooFinanceError(Exception):
    """Custom exception for Yahoo Finance related errors."""
    pass


class RateLimitError(YahooFinanceError):
    """Exception raised when rate limit is exceeded."""
    pass


class YahooFinanceClient(LoggerMixin):
    """
    Client for fetching data from Yahoo Finance using yfinance library.
    
    This class provides methods to fetch stock price data, financial data,
    and company information with built-in rate limiting and error handling.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the Yahoo Finance client.
        
        Args:
            config_manager: Configuration manager instance. If None, uses global instance.
        """
        self.config_manager = config_manager or get_config_manager()
        self._load_config()
        self._last_request_time = 0.0
    
    def _load_config(self) -> None:
        """Load configuration settings."""
        yahoo_config = self.config_manager.get("data_fetching.yahoo_finance", {})
        
        self.request_delay = yahoo_config.get("request_delay", 1.0)
        self.max_retries = yahoo_config.get("max_retries", 3)
        self.timeout = yahoo_config.get("timeout", 30)
        self.batch_size = yahoo_config.get("batch_size", 10)
        
        self.logger.info(f"Yahoo Finance client configured: delay={self.request_delay}s, "
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
    
    def _retry_request(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            YahooFinanceError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
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
            ticker = yf.Ticker(symbol)
            info = self._retry_request(lambda: ticker.info)
            return info is not None and len(info) > 0 and 'symbol' in info
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
            ticker = yf.Ticker(symbol)
            
            if start_date and end_date:
                data = self._retry_request(
                    ticker.history,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    back_adjust=True
                )
            else:
                data = self._retry_request(
                    ticker.history,
                    period=period,
                    auto_adjust=True,
                    back_adjust=True
                )
            
            if data.empty:
                raise YahooFinanceError(f"No data found for symbol {symbol}")
            
            # Clean up column names and ensure proper data types
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
            
            # Add symbol column
            data['symbol'] = symbol.upper()
            
            self.logger.info(f"Fetched {len(data)} records for {symbol}")
            return data
            
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
            ticker = yf.Ticker(symbol)
            
            # Fetch different types of financial data
            financials = self._retry_request(lambda: ticker.financials)
            balance_sheet = self._retry_request(lambda: ticker.balance_sheet)
            cash_flow = self._retry_request(lambda: ticker.cashflow)
            info = self._retry_request(lambda: ticker.info)
            
            financial_data = {
                'symbol': symbol.upper(),
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cash_flow': cash_flow,
                'info': info
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
            ticker = yf.Ticker(symbol)
            info = self._retry_request(lambda: ticker.info)
            
            if not info:
                raise YahooFinanceError(f"No company info found for symbol {symbol}")
            
            company_info = {
                'symbol': symbol.upper(),
                'info': info
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
    
    def convert_to_stock_data(self, df: pd.DataFrame, symbol: str) -> List[StockData]:
        """
        Convert pandas DataFrame to list of StockData objects.
        
        Args:
            df: DataFrame with stock price data
            symbol: Stock symbol
            
        Returns:
            List[StockData]: List of StockData objects
        """
        stock_data_list = []
        
        for index, row in df.iterrows():
            try:
                stock_data = StockData(
                    symbol=symbol.upper(),
                    date=index.to_pydatetime() if hasattr(index, 'to_pydatetime') else index,
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=int(row.get('volume', 0)),
                    adjusted_close=float(row.get('close', 0)),  # yfinance auto-adjusts
                    dividend=float(row.get('dividends', 0)) if 'dividends' in row else None,
                    stock_split=float(row.get('stock_splits', 1)) if 'stock_splits' in row else None
                )
                
                # Validate the data before adding
                if stock_data.validate():
                    stock_data_list.append(stock_data)
                else:
                    self.logger.warning(f"Invalid stock data for {symbol} on {index}")
                    
            except Exception as e:
                self.logger.error(f"Error converting data for {symbol} on {index}: {e}")
        
        return stock_data_list
    
    def convert_to_financial_data(self, financial_dict: Dict[str, Any]) -> List[FinancialData]:
        """
        Convert financial data dictionary to list of FinancialData objects.
        
        Args:
            financial_dict: Dictionary containing financial data from Yahoo Finance
            
        Returns:
            List[FinancialData]: List of FinancialData objects
        """
        financial_data_list = []
        symbol = financial_dict['symbol']
        info = financial_dict.get('info', {})
        financials = financial_dict.get('financials', pd.DataFrame())
        balance_sheet = financial_dict.get('balance_sheet', pd.DataFrame())
        cash_flow = financial_dict.get('cash_flow', pd.DataFrame())
        
        # Process annual data from financials DataFrame
        if not financials.empty:
            for date_col in financials.columns:
                try:
                    fiscal_year = date_col.year
                    
                    financial_data = FinancialData(
                        symbol=symbol,
                        fiscal_year=fiscal_year,
                        # Income statement data
                        revenue=self._safe_get_financial_value(financials, 'Total Revenue', date_col),
                        gross_profit=self._safe_get_financial_value(financials, 'Gross Profit', date_col),
                        operating_income=self._safe_get_financial_value(financials, 'Operating Income', date_col),
                        net_income=self._safe_get_financial_value(financials, 'Net Income', date_col),
                        # Balance sheet data
                        total_assets=self._safe_get_financial_value(balance_sheet, 'Total Assets', date_col),
                        total_liabilities=self._safe_get_financial_value(balance_sheet, 'Total Liab', date_col),
                        shareholders_equity=self._safe_get_financial_value(balance_sheet, 'Total Stockholder Equity', date_col),
                        # Cash flow data
                        operating_cash_flow=self._safe_get_financial_value(cash_flow, 'Total Cash From Operating Activities', date_col),
                        free_cash_flow=self._safe_get_financial_value(cash_flow, 'Free Cash Flow', date_col),
                        # Ratios from info
                        per=info.get('trailingPE'),
                        pbr=info.get('priceToBook'),
                        roe=info.get('returnOnEquity'),
                        roa=info.get('returnOnAssets'),
                        debt_to_equity=info.get('debtToEquity'),
                        current_ratio=info.get('currentRatio')
                    )
                    
                    # Calculate EPS if we have net income and shares outstanding
                    shares_outstanding = info.get('sharesOutstanding')
                    if financial_data.net_income and shares_outstanding:
                        financial_data.eps = financial_data.net_income / shares_outstanding
                    else:
                        financial_data.eps = info.get('trailingEps')
                    
                    if financial_data.validate():
                        financial_data_list.append(financial_data)
                    else:
                        self.logger.warning(f"Invalid financial data for {symbol} year {fiscal_year}")
                        
                except Exception as e:
                    self.logger.error(f"Error converting financial data for {symbol}: {e}")
        
        return financial_data_list
    
    def convert_to_company_info(self, company_dict: Dict[str, Any]) -> CompanyInfo:
        """
        Convert company info dictionary to CompanyInfo object.
        
        Args:
            company_dict: Dictionary containing company info from Yahoo Finance
            
        Returns:
            CompanyInfo: CompanyInfo object
        """
        symbol = company_dict['symbol']
        info = company_dict.get('info', {})
        
        company_info = CompanyInfo(
            symbol=symbol,
            company_name=info.get('longName', info.get('shortName', symbol)),
            sector=info.get('sector'),
            industry=info.get('industry'),
            market_cap=info.get('marketCap'),
            country=info.get('country'),
            currency=info.get('currency'),
            exchange=info.get('exchange')
        )
        
        return company_info
    
    def _safe_get_financial_value(self, df: pd.DataFrame, key: str, date_col) -> Optional[float]:
        """
        Safely get a financial value from DataFrame.
        
        Args:
            df: Financial data DataFrame
            key: Row key to look for
            date_col: Column (date) to get value from
            
        Returns:
            Optional[float]: Financial value or None if not found
        """
        try:
            if df.empty or key not in df.index or date_col not in df.columns:
                return None
            
            value = df.loc[key, date_col]
            return float(value) if pd.notna(value) else None
        except (KeyError, ValueError, TypeError):
            return None