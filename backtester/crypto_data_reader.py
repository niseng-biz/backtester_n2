"""
Cryptocurrency data reader for handling unix timestamp data.
"""

from datetime import datetime
from .data_reader import CSVDataReader


class CryptoDataReader(CSVDataReader):
    """Data reader for cryptocurrency data with unix timestamps."""

    def __init__(self):
        """Initialize crypto data reader with appropriate column mappings."""
        super().__init__(
            date_column="time",
            open_column="open",
            high_column="high",
            low_column="low",
            close_column="close",
            volume_column="Volume",
        )

    def _parse_date(self, timestamp_str) -> datetime:
        """
        Parse unix timestamp to datetime object.

        Args:
            timestamp_str: Unix timestamp as string or number

        Returns:
            datetime object
        """
        try:
            # Convert to integer (unix timestamp)
            timestamp = int(float(timestamp_str))
            # Convert to datetime
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Unable to parse unix timestamp '{timestamp_str}': {e}")
