"""
Data reader implementations for loading market data from various sources.
"""

import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Any, Optional
from functools import wraps
import logging
from .models import MarketData

# Set up logger
logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def handle_validation_error(func):
    """
    Decorator for common data validation error handling.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with unified error handling
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {func.__name__}: {e}")
            raise DataValidationError(f"Data validation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper


class DataReader(ABC):
    """Abstract base class for data readers."""

    @abstractmethod
    def load_data(self, source: str) -> List[MarketData]:
        """Load market data from source."""
        pass

    @abstractmethod
    def validate_data(self, data: List[MarketData]) -> bool:
        """Validate loaded data integrity."""
        pass

    @handle_validation_error
    def _validate_columns(self, columns: List[str], required_columns: List[str]) -> None:
        """
        Validate that all required columns are present.
        
        Args:
            columns: Available columns in the data
            required_columns: List of required column names
            
        Raises:
            DataValidationError: If required columns are missing
        """
        missing_columns = []
        for required_col in required_columns:
            if required_col not in columns:
                missing_columns.append(required_col)

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns: {columns}"
            )

    @handle_validation_error
    def _validate_price_data(self, data: List[MarketData]) -> bool:
        """
        Validate price data integrity.
        
        Args:
            data: List of MarketData objects
            
        Returns:
            True if data is valid, False otherwise
            
        Raises:
            DataValidationError: If data validation fails
        """
        if not data:
            raise ValueError("No data provided for validation")

        # Check for chronological order
        for i in range(1, len(data)):
            if data[i].timestamp <= data[i - 1].timestamp:
                raise ValueError(f"Data not in chronological order at index {i}")

        # Check for reasonable price ranges (no extreme outliers)
        prices = []
        for d in data:
            prices.extend([d.open, d.high, d.low, d.close])

        if not prices:
            raise ValueError("No price data found")

        # Basic sanity checks
        min_price = min(prices)
        max_price = max(prices)

        # Prices should be positive and within reasonable range
        if min_price <= 0:
            raise ValueError(f"Invalid negative or zero price found: {min_price}")
            
        if max_price / min_price > 1000:  # 1000x price range seems unreasonable
            raise ValueError(f"Price range too extreme: {min_price} to {max_price}")

        return True

    @handle_validation_error
    def _parse_date_common(self, date_str: Any, date_format: Optional[str] = None) -> datetime:
        """
        Common date parsing logic with fallback mechanisms.
        
        Args:
            date_str: Date string or datetime object
            date_format: Optional specific date format to try first
            
        Returns:
            datetime object
            
        Raises:
            DataValidationError: If date cannot be parsed
        """
        if isinstance(date_str, datetime):
            return date_str

        if pd.isna(date_str):
            raise ValueError("Date cannot be null")

        date_str = str(date_str).strip()

        if date_format:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError as e:
                raise ValueError(
                    f"Date '{date_str}' doesn't match format '{date_format}': {e}"
                )

        # Try common date formats
        common_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

        for fmt in common_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try pandas date parser as fallback
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except Exception as e:
            raise ValueError(f"Unable to parse date '{date_str}': {e}")


class CSVDataReader(DataReader):
    """CSV data reader with configurable column mapping."""

    def __init__(
        self,
        date_column: str = "Date",
        open_column: str = "Open",
        high_column: str = "High",
        low_column: str = "Low",
        close_column: str = "Close",
        volume_column: str = "Volume",
        date_format: Optional[str] = None,
    ):
        """
        Initialize CSV reader with column mappings.

        Args:
            date_column: Name of date column
            open_column: Name of open price column
            high_column: Name of high price column
            low_column: Name of low price column
            close_column: Name of close price column
            volume_column: Name of volume column
            date_format: Date format string (auto-detected if None)
        """
        self.column_mapping = {
            "date": date_column,
            "open": open_column,
            "high": high_column,
            "low": low_column,
            "close": close_column,
            "volume": volume_column,
        }
        self.date_format = date_format

    def load_data(self, source: str) -> List[MarketData]:
        """
        Load market data from CSV file.

        Args:
            source: Path to CSV file

        Returns:
            List of MarketData objects sorted by timestamp

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing or data is invalid
        """
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")

        try:
            # Read CSV using pandas for better handling of various formats
            df = pd.read_csv(source)

            # Validate required columns exist
            self._validate_columns(df.columns.tolist(), list(self.column_mapping.values()))

            # Convert to MarketData objects
            market_data = []
            for _, row in df.iterrows():
                try:
                    timestamp = self._parse_date(row[self.column_mapping["date"]])

                    data = MarketData(
                        timestamp=timestamp,
                        open=float(row[self.column_mapping["open"]]),
                        high=float(row[self.column_mapping["high"]]),
                        low=float(row[self.column_mapping["low"]]),
                        close=float(row[self.column_mapping["close"]]),
                        volume=int(row[self.column_mapping["volume"]]),
                    )
                    market_data.append(data)

                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid data in row {len(market_data) + 1}: {e}")

            # Sort by timestamp
            market_data.sort(key=lambda x: x.timestamp)

            # Validate data integrity
            if not self.validate_data(market_data):
                raise ValueError("Data validation failed")

            return market_data

        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {source}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file: {e}")

    def validate_data(self, data: List[MarketData]) -> bool:
        """
        Validate data integrity.

        Args:
            data: List of MarketData objects

        Returns:
            True if data is valid, False otherwise
        """
        try:
            return self._validate_price_data(data)
        except DataValidationError:
            return False



    def _parse_date(self, date_str: Any) -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string or datetime object

        Returns:
            datetime object
        """
        return self._parse_date_common(date_str, self.date_format)


class DataReaderFactory:
    """Factory for creating data readers."""

    @staticmethod
    def create_csv_reader(**kwargs) -> CSVDataReader:
        """Create CSV data reader with custom configuration."""
        return CSVDataReader(**kwargs)

    @staticmethod
    def create_reader(source_type: str, **kwargs) -> DataReader:
        """
        Create appropriate data reader based on source type.

        Args:
            source_type: Type of data source ('csv', etc.)
            **kwargs: Configuration parameters for the reader

        Returns:
            DataReader instance
        """
        if source_type.lower() == "csv":
            return CSVDataReader(**kwargs)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
