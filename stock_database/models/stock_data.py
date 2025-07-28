"""
Stock data model for daily candlestick data with technical indicators.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class StockData:
    """
    Data model for daily stock price data including OHLCV and technical indicators.
    
    Attributes:
        symbol: Stock symbol (e.g., 'AAPL')
        date: Trading date
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        adjusted_close: Adjusted closing price for splits/dividends
        dividend: Dividend amount (if any)
        stock_split: Stock split ratio (if any)
        sma_20: 20-day Simple Moving Average
        sma_50: 50-day Simple Moving Average
        rsi: Relative Strength Index
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: float
    dividend: Optional[float] = None
    stock_split: Optional[float] = None
    
    # Technical indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi: Optional[float] = None
    
    # Additional technical indicators
    bb_upper: Optional[float] = None  # Bollinger Bands Upper
    bb_middle: Optional[float] = None  # Bollinger Bands Middle
    bb_lower: Optional[float] = None  # Bollinger Bands Lower
    macd: Optional[float] = None  # MACD Line
    macd_signal: Optional[float] = None  # MACD Signal Line
    macd_histogram: Optional[float] = None  # MACD Histogram
    stoch_k: Optional[float] = None  # Stochastic %K
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """
        Validate the stock data for consistency and correctness.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self.symbol or not isinstance(self.symbol, str):
                return False
            
            if not isinstance(self.date, datetime):
                return False
            
            # Check price values are non-negative
            price_fields = [self.open, self.high, self.low, self.close, self.adjusted_close]
            if any(price < 0 for price in price_fields if price is not None):
                return False
            
            # Check volume is non-negative
            if self.volume < 0:
                return False
            
            # Check OHLC relationships
            if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
                return False
            
            # Check technical indicators are within valid ranges
            if self.rsi is not None and (self.rsi < 0 or self.rsi > 100):
                return False
            
            return True
        except (TypeError, ValueError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the stock data to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the stock data
        """
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close,
            'dividend': self.dividend,
            'stock_split': self.stock_split,
            'sma_20': self.sma_20,
            'sma_50': self.sma_50,
            'rsi': self.rsi,
            'bb_upper': self.bb_upper,
            'bb_middle': self.bb_middle,
            'bb_lower': self.bb_lower,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'macd_histogram': self.macd_histogram,
            'stoch_k': self.stoch_k,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockData':
        """
        Create a StockData instance from a dictionary.
        
        Args:
            data: Dictionary containing stock data
            
        Returns:
            StockData: New instance created from the dictionary
        """
        # Convert date strings back to datetime objects
        data_copy = data.copy()
        data_copy['date'] = datetime.fromisoformat(data['date'])
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        data_copy['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data_copy)
    
    def to_json(self) -> str:
        """
        Convert the stock data to JSON string.
        
        Returns:
            str: JSON representation of the stock data
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StockData':
        """
        Create a StockData instance from a JSON string.
        
        Args:
            json_str: JSON string containing stock data
            
        Returns:
            StockData: New instance created from the JSON
        """
        data = json.loads(json_str)
        return cls.from_dict(data)