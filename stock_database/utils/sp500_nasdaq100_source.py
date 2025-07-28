"""
S&P 500 and NASDAQ 100 symbol data source implementation.
"""
import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from ..models.symbol_info import SymbolInfo
from .symbol_data_source import (DataValidationError, FilterCriteria,
                                 NetworkError, RateLimitError,
                                 SymbolDataSource, SymbolDataSourceError)

logger = logging.getLogger(__name__)


class SP500Nasdaq100Source(SymbolDataSource):
    """
    Symbol data source for S&P 500 and NASDAQ 100 symbols.
    
    This implementation fetches symbols from:
    1. S&P 500 list (Wikipedia or other sources)
    2. NASDAQ 100 list (Wikipedia or other sources)
    3. Static lists as fallback
    """
    
    def __init__(self, rate_limit: int = 60, request_delay: float = 1.0):
        """
        Initialize S&P 500 and NASDAQ 100 symbol source.
        
        Args:
            rate_limit: Maximum requests per minute
            request_delay: Delay between requests in seconds
        """
        self.rate_limit = rate_limit
        self.request_delay = request_delay
        self.last_request_time = 0.0
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        return "S&P 500 & NASDAQ 100 Source"
    
    def get_rate_limit(self) -> Optional[int]:
        """Get the rate limit for this data source."""
        return self.rate_limit
    
    def is_available(self) -> bool:
        """Check if the data source is available."""
        try:
            # Test with a simple request to Wikipedia
            response = self._session.get(
                "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"S&P 500/NASDAQ 100 source availability check failed: {e}")
            return False
    
    def _rate_limit_delay(self):
        """Apply rate limiting delay."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_symbols(self, **kwargs) -> List[SymbolInfo]:
        """
        Fetch S&P 500 and NASDAQ 100 symbols.
        
        Args:
            **kwargs: Additional parameters (limit, criteria, etc.)
            
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        logger.info("Fetching S&P 500 and NASDAQ 100 symbols")
        
        try:
            all_symbols = []
            
            # Fetch S&P 500 symbols
            try:
                sp500_symbols = self._fetch_sp500_symbols()
                all_symbols.extend(sp500_symbols)
                logger.info(f"Fetched {len(sp500_symbols)} S&P 500 symbols")
            except Exception as e:
                logger.warning(f"S&P 500 fetch failed: {e}")
            
            # Fetch NASDAQ 100 symbols
            try:
                nasdaq100_symbols = self._fetch_nasdaq100_symbols()
                all_symbols.extend(nasdaq100_symbols)
                logger.info(f"Fetched {len(nasdaq100_symbols)} NASDAQ 100 symbols")
            except Exception as e:
                logger.warning(f"NASDAQ 100 fetch failed: {e}")
            
            # If both failed, use static list
            if not all_symbols:
                logger.info("Using static symbol list as fallback")
                all_symbols = self._get_static_symbols()
            
            # Remove duplicates
            unique_symbols = self._deduplicate_symbols(all_symbols)
            logger.info(f"Total unique symbols: {len(unique_symbols)}")
            
            # Apply filters if provided
            criteria = kwargs.get('criteria')
            if criteria and isinstance(criteria, FilterCriteria):
                unique_symbols = [s for s in unique_symbols if criteria.matches(s)]
                logger.info(f"Filtered to {len(unique_symbols)} symbols based on criteria")
            
            # Apply limit if provided
            limit = kwargs.get('limit')
            if limit and isinstance(limit, int) and limit > 0:
                unique_symbols = unique_symbols[:limit]
                logger.info(f"Limited to {len(unique_symbols)} symbols")
            
            return unique_symbols
            
        except Exception as e:
            raise SymbolDataSourceError(f"Failed to fetch symbols: {e}")
    
    def _fetch_sp500_symbols(self) -> List[SymbolInfo]:
        """
        Fetch S&P 500 symbols from Wikipedia.
        
        Returns:
            List[SymbolInfo]: List of S&P 500 symbols
        """
        self._rate_limit_delay()
        
        try:
            # Use pandas to read the Wikipedia table
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            
            # The first table contains the S&P 500 companies
            sp500_table = tables[0]
            
            symbols = []
            for _, row in sp500_table.iterrows():
                try:
                    symbol = str(row['Symbol']).strip().replace('.', '-')  # Handle special characters
                    company_name = str(row['Security']).strip()
                    sector = str(row['GICS Sector']).strip() if 'GICS Sector' in row else None
                    industry = str(row['GICS Sub-Industry']).strip() if 'GICS Sub-Industry' in row else None
                    
                    if symbol and company_name and symbol != 'nan' and company_name != 'nan':
                        symbol_info = SymbolInfo(
                            symbol=symbol,
                            company_name=company_name,
                            exchange="NYSE/NASDAQ",  # S&P 500 includes both
                            sector=sector if sector != 'nan' else None,
                            industry=industry if industry != 'nan' else None,
                            is_active=True
                        )
                        symbols.append(symbol_info)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse S&P 500 row: {e}")
                    continue
            
            return symbols
            
        except Exception as e:
            raise NetworkError(f"Failed to fetch S&P 500 symbols: {e}")
    
    def _fetch_nasdaq100_symbols(self) -> List[SymbolInfo]:
        """
        Fetch NASDAQ 100 symbols from Wikipedia.
        
        Returns:
            List[SymbolInfo]: List of NASDAQ 100 symbols
        """
        self._rate_limit_delay()
        
        try:
            # Use pandas to read the Wikipedia table
            url = "https://en.wikipedia.org/wiki/NASDAQ-100"
            tables = pd.read_html(url)
            
            # Find the table with NASDAQ 100 companies
            nasdaq100_table = None
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    nasdaq100_table = table
                    break
            
            if nasdaq100_table is None:
                raise DataValidationError("Could not find NASDAQ 100 table")
            
            symbols = []
            for _, row in nasdaq100_table.iterrows():
                try:
                    # Handle different column names
                    symbol_col = 'Ticker' if 'Ticker' in row else 'Symbol'
                    company_col = 'Company' if 'Company' in row else 'Name'
                    
                    symbol = str(row[symbol_col]).strip()
                    company_name = str(row[company_col]).strip()
                    sector = str(row['Sector']).strip() if 'Sector' in row else None
                    industry = str(row['Industry']).strip() if 'Industry' in row else None
                    
                    if symbol and company_name and symbol != 'nan' and company_name != 'nan':
                        symbol_info = SymbolInfo(
                            symbol=symbol,
                            company_name=company_name,
                            exchange="NASDAQ",
                            sector=sector if sector != 'nan' else None,
                            industry=industry if industry != 'nan' else None,
                            is_active=True
                        )
                        symbols.append(symbol_info)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse NASDAQ 100 row: {e}")
                    continue
            
            return symbols
            
        except Exception as e:
            raise NetworkError(f"Failed to fetch NASDAQ 100 symbols: {e}")
    
    def _get_static_symbols(self) -> List[SymbolInfo]:
        """
        Get static list of major S&P 500 and NASDAQ 100 symbols.
        
        Returns:
            List[SymbolInfo]: Static list of symbols
        """
        # Major S&P 500 and NASDAQ 100 symbols
        static_data = [
            # Technology (NASDAQ 100)
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "GOOG", "name": "Alphabet Inc. Class C", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "exchange": "NASDAQ"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "exchange": "NASDAQ"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services", "exchange": "NASDAQ"},
            {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "exchange": "NYSE"},
            {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "PYPL", "name": "PayPal Holdings Inc.", "sector": "Financial Services", "exchange": "NASDAQ"},
            {"symbol": "CMCSA", "name": "Comcast Corporation", "sector": "Communication Services", "exchange": "NASDAQ"},
            {"symbol": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Staples", "exchange": "NASDAQ"},
            {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "TXN", "name": "Texas Instruments Incorporated", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "QCOM", "name": "QUALCOMM Incorporated", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "TMUS", "name": "T-Mobile US Inc.", "sector": "Communication Services", "exchange": "NASDAQ"},
            
            # Major S&P 500 (NYSE)
            {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc. Class B", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "UNH", "name": "UnitedHealth Group Incorporated", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "PG", "name": "The Procter & Gamble Company", "sector": "Consumer Staples", "exchange": "NYSE"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "HD", "name": "The Home Depot Inc.", "sector": "Consumer Discretionary", "exchange": "NYSE"},
            {"symbol": "MA", "name": "Mastercard Incorporated", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "BAC", "name": "Bank of America Corporation", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy", "exchange": "NYSE"},
            {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy", "exchange": "NYSE"},
            {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "KO", "name": "The Coca-Cola Company", "sector": "Consumer Staples", "exchange": "NYSE"},
            {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Staples", "exchange": "NASDAQ"},
            {"symbol": "TMO", "name": "Thermo Fisher Scientific Inc.", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology", "exchange": "NYSE"},
            {"symbol": "ACN", "name": "Accenture plc", "sector": "Technology", "exchange": "NYSE"},
            {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples", "exchange": "NYSE"},
            {"symbol": "DIS", "name": "The Walt Disney Company", "sector": "Communication Services", "exchange": "NYSE"},
            {"symbol": "VZ", "name": "Verizon Communications Inc.", "sector": "Communication Services", "exchange": "NYSE"},
            {"symbol": "NKE", "name": "NIKE Inc.", "sector": "Consumer Discretionary", "exchange": "NYSE"},
            {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "BMY", "name": "Bristol-Myers Squibb Company", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "T", "name": "AT&T Inc.", "sector": "Communication Services", "exchange": "NYSE"},
            {"symbol": "MDT", "name": "Medtronic plc", "sector": "Healthcare", "exchange": "NYSE"},
            {"symbol": "UPS", "name": "United Parcel Service Inc.", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "HON", "name": "Honeywell International Inc.", "sector": "Industrials", "exchange": "NASDAQ"},
            {"symbol": "IBM", "name": "International Business Machines Corporation", "sector": "Technology", "exchange": "NYSE"},
            {"symbol": "AMGN", "name": "Amgen Inc.", "sector": "Healthcare", "exchange": "NASDAQ"},
            {"symbol": "LOW", "name": "Lowe's Companies Inc.", "sector": "Consumer Discretionary", "exchange": "NYSE"},
            {"symbol": "SPGI", "name": "S&P Global Inc.", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "GS", "name": "The Goldman Sachs Group Inc.", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "MS", "name": "Morgan Stanley", "sector": "Financial Services", "exchange": "NYSE"},
            {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "DE", "name": "Deere & Company", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "MMM", "name": "3M Company", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "BA", "name": "The Boeing Company", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "GE", "name": "General Electric Company", "sector": "Industrials", "exchange": "NYSE"},
            {"symbol": "F", "name": "Ford Motor Company", "sector": "Consumer Discretionary", "exchange": "NYSE"},
            {"symbol": "GM", "name": "General Motors Company", "sector": "Consumer Discretionary", "exchange": "NYSE"},
        ]
        
        symbols = []
        for data in static_data:
            try:
                symbol_info = SymbolInfo(
                    symbol=data["symbol"],
                    company_name=data["name"],
                    exchange=data["exchange"],
                    sector=data.get("sector"),
                    is_active=True
                )
                symbols.append(symbol_info)
            except Exception as e:
                logger.debug(f"Failed to create static symbol {data}: {e}")
                continue
        
        return symbols
    
    def _deduplicate_symbols(self, symbols: List[SymbolInfo]) -> List[SymbolInfo]:
        """
        Remove duplicate symbols, keeping the first occurrence.
        
        Args:
            symbols: List of symbols that may contain duplicates
            
        Returns:
            List[SymbolInfo]: List of unique symbols
        """
        seen = set()
        unique_symbols = []
        
        for symbol in symbols:
            if symbol.symbol not in seen:
                seen.add(symbol.symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols
    
    def get_supported_filters(self) -> List[str]:
        """Get list of supported filter parameters."""
        return [
            'sector',
            'exchange',
            'active_only',
            'limit'
        ]