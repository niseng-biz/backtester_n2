"""
Company information model for company metadata and basic information.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class CompanyInfo:
    """
    Data model for company information and metadata based on yfinance fields.
    
    Attributes:
        symbol: Stock symbol (e.g., 'AAPL')
        long_name: Full company name (longName)
        short_name: Short company name (shortName)
        sector: Business sector
        industry: Industry classification
        market_cap: Market capitalization
        country: Country of incorporation
        currency: Trading currency
        exchange: Stock exchange
        website: Company website
        business_summary: Long business summary
        full_time_employees: Number of full-time employees
        city: City location
        state: State location
        zip_code: ZIP code
        phone: Phone number
        address1: Primary address
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    symbol: str
    long_name: str
    short_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    website: Optional[str] = None
    business_summary: Optional[str] = None
    full_time_employees: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    address1: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """
        Validate the company information for consistency and correctness.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self.symbol or not isinstance(self.symbol, str):
                return False
            
            if not self.long_name or not isinstance(self.long_name, str):
                return False
            
            # Check market cap is non-negative if provided
            if self.market_cap is not None and self.market_cap < 0:
                return False
            
            # Check currency format if provided (should be 3-letter code)
            if self.currency is not None:
                if not isinstance(self.currency, str) or len(self.currency) != 3:
                    return False
            
            return True
        except (TypeError, ValueError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the company info to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the company info
        """
        return {
            'symbol': self.symbol,
            'long_name': self.long_name,
            'short_name': self.short_name,
            'sector': self.sector,
            'industry': self.industry,
            'market_cap': self.market_cap,
            'country': self.country,
            'currency': self.currency,
            'exchange': self.exchange,
            'website': self.website,
            'business_summary': self.business_summary,
            'full_time_employees': self.full_time_employees,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'address1': self.address1,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyInfo':
        """
        Create a CompanyInfo instance from a dictionary.
        
        Args:
            data: Dictionary containing company info
            
        Returns:
            CompanyInfo: New instance created from the dictionary
        """
        # Convert date strings back to datetime objects
        data_copy = data.copy()
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        data_copy['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data_copy)
    
    def to_json(self) -> str:
        """
        Convert the company info to JSON string.
        
        Returns:
            str: JSON representation of the company info
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CompanyInfo':
        """
        Create a CompanyInfo instance from a JSON string.
        
        Args:
            json_str: JSON string containing company info
            
        Returns:
            CompanyInfo: New instance created from the JSON
        """
        data = json.loads(json_str)
        return cls.from_dict(data)