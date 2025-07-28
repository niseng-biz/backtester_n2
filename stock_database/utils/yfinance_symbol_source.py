"""
YFinance-based symbol data source implementation.
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


class YFinanceSymbolSource(SymbolDataSource):
    """
    Symbol data source using yfinance and NASDAQ screener data.
    
    This implementation fetches NASDAQ symbols using multiple approaches:
    1. NASDAQ screener API (primary)
    2. yfinance ticker info (for validation and additional data)
    3. Static symbol lists (fallback)
    """
    
    def __init__(self, rate_limit: int = 60, request_delay: float = 1.0):
        """
        Initialize YFinance symbol source.
        
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
        return "YFinance Symbol Source"
    
    def get_rate_limit(self) -> Optional[int]:
        """Get the rate limit for this data source."""
        return self.rate_limit
    
    def is_available(self) -> bool:
        """Check if the data source is available."""
        try:
            # Test with a simple request
            response = self._session.get(
                "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"YFinance source availability check failed: {e}")
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
        Fetch NASDAQ symbols using multiple methods.
        
        Args:
            **kwargs: Additional parameters (limit, sector, etc.)
            
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        logger.info("Fetching NASDAQ symbols from YFinance source")
        
        try:
            # Try multiple methods to get symbols
            symbols = []
            
            # Method 1: NASDAQ screener
            try:
                nasdaq_symbols = self._fetch_nasdaq_screener()
                symbols.extend(nasdaq_symbols)
                logger.info(f"Fetched {len(nasdaq_symbols)} symbols from NASDAQ screener")
            except Exception as e:
                logger.warning(f"NASDAQ screener failed: {e}")
            
            # Method 2: Static symbol list (fallback)
            if not symbols:
                try:
                    static_symbols = self._fetch_static_symbols()
                    symbols.extend(static_symbols)
                    logger.info(f"Using {len(static_symbols)} symbols from static list")
                except Exception as e:
                    logger.warning(f"Static symbol list failed: {e}")
            
            # Apply filters if provided
            criteria = kwargs.get('criteria')
            if criteria and isinstance(criteria, FilterCriteria):
                symbols = [s for s in symbols if criteria.matches(s)]
                logger.info(f"Filtered to {len(symbols)} symbols based on criteria")
            
            # Apply limit if provided
            limit = kwargs.get('limit')
            if limit and isinstance(limit, int) and limit > 0:
                symbols = symbols[:limit]
                logger.info(f"Limited to {len(symbols)} symbols")
            
            return symbols
            
        except Exception as e:
            raise SymbolDataSourceError(f"Failed to fetch symbols: {e}")
    
    def _fetch_nasdaq_screener(self) -> List[SymbolInfo]:
        """
        Fetch symbols from NASDAQ screener API.
        
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        self._rate_limit_delay()
        
        try:
            # NASDAQ screener endpoint
            url = "https://api.nasdaq.com/api/screener/stocks"
            params = {
                'tableonly': 'true',
                'limit': '5000',
                'offset': '0',
                'download': 'true'
            }
            
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or 'rows' not in data['data']:
                raise DataValidationError("Invalid response format from NASDAQ API")
            
            symbols = []
            for row in data['data']['rows']:
                try:
                    symbol_info = self._parse_nasdaq_row(row)
                    if symbol_info:
                        symbols.append(symbol_info)
                except Exception as e:
                    logger.debug(f"Failed to parse row {row}: {e}")
                    continue
            
            return symbols
            
        except requests.RequestException as e:
            raise NetworkError(f"NASDAQ screener request failed: {e}")
        except Exception as e:
            raise SymbolDataSourceError(f"NASDAQ screener parsing failed: {e}")
    
    def _parse_nasdaq_row(self, row: Dict[str, Any]) -> Optional[SymbolInfo]:
        """
        Parse a row from NASDAQ screener data.
        
        Args:
            row: Raw row data from NASDAQ API
            
        Returns:
            Optional[SymbolInfo]: Parsed symbol info or None if invalid
        """
        try:
            symbol = row.get('symbol', '').strip().upper()
            company_name = row.get('name', '').strip()
            
            if not symbol or not company_name:
                return None
            
            # Parse market cap
            market_cap = None
            market_cap_str = row.get('marketCap', '')
            if market_cap_str and market_cap_str != 'N/A':
                try:
                    # Handle formats like "$1.23B", "$456.78M", etc.
                    market_cap_str = market_cap_str.replace('$', '').replace(',', '')
                    if market_cap_str.endswith('B'):
                        market_cap = float(market_cap_str[:-1]) * 1_000_000_000
                    elif market_cap_str.endswith('M'):
                        market_cap = float(market_cap_str[:-1]) * 1_000_000
                    elif market_cap_str.endswith('K'):
                        market_cap = float(market_cap_str[:-1]) * 1_000
                    else:
                        market_cap = float(market_cap_str)
                except (ValueError, TypeError):
                    market_cap = None
            
            return SymbolInfo(
                symbol=symbol,
                company_name=company_name,
                exchange="NASDAQ",
                market_cap=market_cap,
                sector=row.get('sector'),
                industry=row.get('industry'),
                is_active=True
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse NASDAQ row: {e}")
            return None
    
    def _fetch_static_symbols(self) -> List[SymbolInfo]:
        """
        Fetch symbols from a static list (fallback method).
        
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        # Major NASDAQ symbols as fallback
        static_symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
            {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
            {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
            {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
            {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
            {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "sector": "Technology"},
            {"symbol": "PYPL", "name": "PayPal Holdings Inc.", "sector": "Financial Services"},
            {"symbol": "CMCSA", "name": "Comcast Corporation", "sector": "Communication Services"},
            {"symbol": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Staples"},
            {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology"},
            {"symbol": "TXN", "name": "Texas Instruments Incorporated", "sector": "Technology"},
            {"symbol": "QCOM", "name": "QUALCOMM Incorporated", "sector": "Technology"},
            {"symbol": "TMUS", "name": "T-Mobile US Inc.", "sector": "Communication Services"},
            {"symbol": "AMGN", "name": "Amgen Inc.", "sector": "Healthcare"},
        ]
        
        symbols = []
        for data in static_symbols:
            try:
                symbol_info = SymbolInfo(
                    symbol=data["symbol"],
                    company_name=data["name"],
                    exchange="NASDAQ",
                    sector=data.get("sector"),
                    is_active=True
                )
                symbols.append(symbol_info)
            except Exception as e:
                logger.debug(f"Failed to create static symbol {data}: {e}")
                continue
        
        return symbols
    
    def get_supported_filters(self) -> List[str]:
        """Get list of supported filter parameters."""
        return [
            'sector',
            'min_market_cap',
            'max_market_cap',
            'active_only',
            'limit'
        ]
    
    def enrich_symbol_with_yfinance(self, symbol_info: SymbolInfo) -> SymbolInfo:
        """
        Enrich symbol information using yfinance data.
        
        Args:
            symbol_info: Basic symbol information
            
        Returns:
            SymbolInfo: Enriched symbol information
        """
        try:
            import yfinance as yf
            
            self._rate_limit_delay()
            
            ticker = yf.Ticker(symbol_info.symbol)
            info = ticker.info
            
            # Update with yfinance data if available
            if info:
                if 'marketCap' in info and info['marketCap']:
                    symbol_info.market_cap = info['marketCap']
                
                if 'sector' in info and info['sector']:
                    symbol_info.sector = info['sector']
                
                if 'industry' in info and info['industry']:
                    symbol_info.industry = info['industry']
                
                if 'longName' in info and info['longName']:
                    symbol_info.company_name = info['longName']
            
            return symbol_info
            
        except ImportError:
            logger.warning("yfinance not available for symbol enrichment")
            return symbol_info
        except Exception as e:
            logger.debug(f"Failed to enrich symbol {symbol_info.symbol}: {e}")
            return symbol_info