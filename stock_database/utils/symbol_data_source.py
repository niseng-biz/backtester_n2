"""
Abstract interface for stock symbol data sources.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.symbol_info import SymbolInfo


class SymbolDataSourceError(Exception):
    """Exception raised by symbol data sources."""
    pass


class RateLimitError(SymbolDataSourceError):
    """Exception raised when rate limit is exceeded."""
    pass


class NetworkError(SymbolDataSourceError):
    """Exception raised for network-related issues."""
    pass


class DataValidationError(SymbolDataSourceError):
    """Exception raised when data validation fails."""
    pass


class SymbolDataSource(ABC):
    """
    Abstract base class for stock symbol data sources.
    
    This interface defines the contract that all symbol data sources must implement.
    Data sources can be APIs, files, web scrapers, or any other mechanism for
    retrieving stock symbol information.
    """
    
    @abstractmethod
    def fetch_symbols(self, **kwargs) -> List[SymbolInfo]:
        """
        Fetch stock symbols from the data source.
        
        Args:
            **kwargs: Additional parameters specific to the data source
            
        Returns:
            List[SymbolInfo]: List of symbol information
            
        Raises:
            SymbolDataSourceError: If fetching fails
            RateLimitError: If rate limit is exceeded
            NetworkError: If network issues occur
            DataValidationError: If data validation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data source is currently available.
        
        Returns:
            bool: True if the data source is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of the data source.
        
        Returns:
            str: Human-readable name of the data source
        """
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> Optional[int]:
        """
        Get the rate limit for this data source (requests per minute).
        
        Returns:
            Optional[int]: Rate limit in requests per minute, or None if no limit
        """
        pass
    
    def validate_symbol_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate raw symbol data before conversion to SymbolInfo.
        
        Args:
            data: Raw symbol data dictionary
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Basic validation - must have symbol and company name
            if not data.get('symbol') or not isinstance(data['symbol'], str):
                return False
            
            if not data.get('company_name') or not isinstance(data['company_name'], str):
                return False
            
            # Market cap should be numeric if provided
            if 'market_cap' in data and data['market_cap'] is not None:
                if not isinstance(data['market_cap'], (int, float)) or data['market_cap'] < 0:
                    return False
            
            return True
        except (TypeError, KeyError):
            return False
    
    def convert_to_symbol_info(self, data: Dict[str, Any]) -> SymbolInfo:
        """
        Convert raw data dictionary to SymbolInfo object.
        
        Args:
            data: Raw symbol data dictionary
            
        Returns:
            SymbolInfo: Converted symbol information
            
        Raises:
            DataValidationError: If data cannot be converted
        """
        try:
            if not self.validate_symbol_data(data):
                raise DataValidationError(f"Invalid symbol data: {data}")
            
            return SymbolInfo(
                symbol=data['symbol'].upper().strip(),
                company_name=data['company_name'].strip(),
                exchange=data.get('exchange', 'NASDAQ'),
                market_cap=data.get('market_cap'),
                sector=data.get('sector'),
                industry=data.get('industry'),
                is_active=data.get('is_active', True),
                first_listed=data.get('first_listed')
            )
        except Exception as e:
            raise DataValidationError(f"Failed to convert data to SymbolInfo: {e}")
    
    def get_supported_filters(self) -> List[str]:
        """
        Get list of supported filter parameters for this data source.
        
        Returns:
            List[str]: List of supported filter parameter names
        """
        return []
    
    def supports_filter(self, filter_name: str) -> bool:
        """
        Check if a specific filter is supported by this data source.
        
        Args:
            filter_name: Name of the filter parameter
            
        Returns:
            bool: True if filter is supported, False otherwise
        """
        return filter_name in self.get_supported_filters()


class FilterCriteria:
    """
    Container for symbol filtering criteria.
    """
    
    def __init__(
        self,
        sector: Optional[str] = None,
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        active_only: bool = True,
        exchange: Optional[str] = None,
        industry: Optional[str] = None
    ):
        """
        Initialize filter criteria.
        
        Args:
            sector: Filter by sector
            min_market_cap: Minimum market capitalization
            max_market_cap: Maximum market capitalization
            active_only: Only include active symbols
            exchange: Filter by exchange
            industry: Filter by industry
        """
        self.sector = sector
        self.min_market_cap = min_market_cap
        self.max_market_cap = max_market_cap
        self.active_only = active_only
        self.exchange = exchange
        self.industry = industry
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter criteria to dictionary.
        
        Returns:
            Dict[str, Any]: Filter criteria as dictionary
        """
        return {
            'sector': self.sector,
            'min_market_cap': self.min_market_cap,
            'max_market_cap': self.max_market_cap,
            'active_only': self.active_only,
            'exchange': self.exchange,
            'industry': self.industry
        }
    
    def matches(self, symbol_info: SymbolInfo) -> bool:
        """
        Check if a symbol matches the filter criteria.
        
        Args:
            symbol_info: Symbol information to check
            
        Returns:
            bool: True if symbol matches criteria, False otherwise
        """
        if self.active_only and not symbol_info.is_active:
            return False
        
        if self.sector and symbol_info.sector != self.sector:
            return False
        
        if self.industry and symbol_info.industry != self.industry:
            return False
        
        if self.exchange and symbol_info.exchange != self.exchange:
            return False
        
        if self.min_market_cap is not None:
            if symbol_info.market_cap is None or symbol_info.market_cap < self.min_market_cap:
                return False
        
        if self.max_market_cap is not None:
            if symbol_info.market_cap is None or symbol_info.market_cap > self.max_market_cap:
                return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of filter criteria."""
        filters = []
        if self.sector:
            filters.append(f"sector={self.sector}")
        if self.industry:
            filters.append(f"industry={self.industry}")
        if self.exchange:
            filters.append(f"exchange={self.exchange}")
        if self.min_market_cap:
            filters.append(f"min_market_cap=${self.min_market_cap:,.0f}")
        if self.max_market_cap:
            filters.append(f"max_market_cap=${self.max_market_cap:,.0f}")
        if not self.active_only:
            filters.append("include_inactive=True")
        
        return f"FilterCriteria({', '.join(filters)})" if filters else "FilterCriteria(no filters)"