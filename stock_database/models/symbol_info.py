"""
Symbol information model for stock symbols and metadata.
"""
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Optional


@dataclass
class SymbolInfo:
    """
    Data model for stock symbol information.
    
    Attributes:
        symbol: Stock symbol (e.g., 'AAPL')
        company_name: Full company name
        exchange: Stock exchange (e.g., 'NASDAQ', 'NYSE')
        market_cap: Market capitalization in USD
        sector: Business sector
        industry: Industry classification
        is_active: Whether the symbol is currently active/listed
        first_listed: Date when the symbol was first listed
        last_updated: Last update timestamp
        created_at: Record creation timestamp
    """
    symbol: str
    company_name: str
    exchange: str = "NASDAQ"
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = True
    first_listed: Optional[date] = None
    last_updated: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """
        Validate the symbol information for consistency and correctness.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self.symbol or not isinstance(self.symbol, str):
                return False
            
            if not self.company_name or not isinstance(self.company_name, str):
                return False
            
            if not self.exchange or not isinstance(self.exchange, str):
                return False
            
            # Check symbol format (basic validation)
            if not self.symbol.replace('.', '').replace('-', '').isalnum():
                return False
            
            # Check market cap is non-negative if provided
            if self.market_cap is not None and self.market_cap < 0:
                return False
            
            # Check dates are valid
            if self.first_listed is not None and self.first_listed > date.today():
                return False
            
            return True
        except (TypeError, ValueError):
            return False
    
    def is_large_cap(self, threshold: float = 10_000_000_000) -> bool:
        """
        Check if the symbol represents a large-cap stock.
        
        Args:
            threshold: Market cap threshold for large-cap (default: $10B)
            
        Returns:
            bool: True if large-cap, False otherwise
        """
        return self.market_cap is not None and self.market_cap >= threshold
    
    def is_mid_cap(self, min_threshold: float = 2_000_000_000, max_threshold: float = 10_000_000_000) -> bool:
        """
        Check if the symbol represents a mid-cap stock.
        
        Args:
            min_threshold: Minimum market cap for mid-cap (default: $2B)
            max_threshold: Maximum market cap for mid-cap (default: $10B)
            
        Returns:
            bool: True if mid-cap, False otherwise
        """
        return (self.market_cap is not None and 
                min_threshold <= self.market_cap < max_threshold)
    
    def is_small_cap(self, threshold: float = 2_000_000_000) -> bool:
        """
        Check if the symbol represents a small-cap stock.
        
        Args:
            threshold: Market cap threshold for small-cap (default: $2B)
            
        Returns:
            bool: True if small-cap, False otherwise
        """
        return self.market_cap is not None and self.market_cap < threshold
    
    def get_market_cap_category(self) -> str:
        """
        Get the market capitalization category.
        
        Returns:
            str: Market cap category ('large', 'mid', 'small', 'unknown')
        """
        if self.market_cap is None:
            return 'unknown'
        elif self.is_large_cap():
            return 'large'
        elif self.is_mid_cap():
            return 'mid'
        else:
            return 'small'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the symbol info to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the symbol info
        """
        return {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'exchange': self.exchange,
            'market_cap': self.market_cap,
            'sector': self.sector,
            'industry': self.industry,
            'is_active': self.is_active,
            'first_listed': self.first_listed.isoformat() if self.first_listed else None,
            'last_updated': self.last_updated.isoformat(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolInfo':
        """
        Create a SymbolInfo instance from a dictionary.
        
        Args:
            data: Dictionary containing symbol info
            
        Returns:
            SymbolInfo: New instance created from the dictionary
        """
        # Convert date strings back to datetime/date objects
        data_copy = data.copy()
        
        if data_copy.get('first_listed'):
            data_copy['first_listed'] = date.fromisoformat(data['first_listed'])
        
        data_copy['last_updated'] = datetime.fromisoformat(data['last_updated'])
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data_copy)
    
    def to_json(self) -> str:
        """
        Convert the symbol info to JSON string.
        
        Returns:
            str: JSON representation of the symbol info
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SymbolInfo':
        """
        Create a SymbolInfo instance from a JSON string.
        
        Args:
            json_str: JSON string containing symbol info
            
        Returns:
            SymbolInfo: New instance created from the JSON
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """String representation of the symbol info."""
        market_cap_str = f"${self.market_cap:,.0f}" if self.market_cap else "N/A"
        return f"{self.symbol}: {self.company_name} ({self.exchange}) - Market Cap: {market_cap_str}"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"SymbolInfo(symbol='{self.symbol}', company_name='{self.company_name}', "
                f"exchange='{self.exchange}', market_cap={self.market_cap}, "
                f"sector='{self.sector}', is_active={self.is_active})")