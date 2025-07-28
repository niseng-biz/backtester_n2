"""
Stock data repository for efficient stock price data access and management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..database import MongoDBManager
from ..models.stock_data import StockData
from .base_repository import (BaseRepository, with_caching,
                              with_performance_monitoring)

logger = logging.getLogger(__name__)


class StockDataRepository(BaseRepository):
    """
    Repository for stock data operations with caching and performance optimization.
    
    Provides efficient access to stock price data with features like:
    - Cached queries for frequently accessed data
    - Batch operations for bulk data handling
    - Date range queries with optimization
    - Latest data retrieval
    - Performance monitoring
    """
    
    def __init__(self, db_manager: Optional[MongoDBManager] = None, cache_ttl: int = 300):
        """
        Initialize stock data repository.
        
        Args:
            db_manager: MongoDB manager instance
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        super().__init__(db_manager, cache_ttl)
        self.collection_name = self.db_manager.STOCK_DATA_COLLECTION
    
    def get_collection_name(self) -> str:
        """Get the collection name for this repository."""
        return self.collection_name
    
    @with_performance_monitoring("save_stock_data")
    def save_stock_data(self, data: List[StockData]) -> None:
        """
        Save stock data to the database using upsert operations.
        
        Args:
            data: List of StockData instances to save
            
        Raises:
            ValueError: If data validation fails
        """
        if not data:
            logger.warning("No stock data provided to save")
            return
        
        # Validate all data before saving
        invalid_data = []
        valid_data = []
        
        for item in data:
            if item.validate():
                valid_data.append(item)
            else:
                invalid_data.append(item)
        
        if invalid_data:
            logger.warning(f"Found {len(invalid_data)} invalid stock data records")
            for item in invalid_data:
                logger.debug(f"Invalid data: {item.symbol} on {item.date}")
        
        if not valid_data:
            raise ValueError("No valid stock data to save")
        
        # Use upsert to handle duplicates gracefully
        self.db_manager.upsert_stock_data(valid_data)
        
        # Clear cache for affected symbols
        symbols = {item.symbol for item in valid_data}
        for symbol in symbols:
            self._clear_cache(symbol)
        
        logger.info(f"Saved {len(valid_data)} stock data records")
    
    @with_caching()
    @with_performance_monitoring("get_stock_data")
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StockData]:
        """
        Retrieve stock data for a symbol within a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of records to return
            
        Returns:
            List[StockData]: List of stock data records sorted by date (newest first)
        """
        return self.db_manager.get_stock_data(symbol, start_date, end_date, limit)
    
    @with_caching()
    @with_performance_monitoring("get_latest_date")
    def get_latest_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the latest date for which stock data exists for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[datetime]: Latest date or None if no data exists
        """
        return self.db_manager.get_latest_stock_date(symbol)
    
    @with_performance_monitoring("update_stock_data")
    def update_stock_data(self, symbol: str, date: datetime, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields of stock data for a symbol and date.
        
        Args:
            symbol: Stock symbol
            date: Trading date
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if document was updated, False if not found
        """
        result = self.db_manager.update_stock_data(symbol, date, updates)
        
        if result:
            # Clear cache for this symbol
            self._clear_cache(symbol)
        
        return result
    
    @with_caching()
    @with_performance_monitoring("get_recent_data")
    def get_recent_data(self, symbol: str, days: int = 30) -> List[StockData]:
        """
        Get recent stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of recent days to retrieve (default: 30)
            
        Returns:
            List[StockData]: Recent stock data records
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_stock_data(symbol, start_date, end_date)
    
    @with_caching()
    @with_performance_monitoring("get_data_range")
    def get_data_range(self, symbol: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the date range (earliest and latest dates) for a symbol's data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[Tuple[datetime, datetime]]: (earliest_date, latest_date) or None if no data
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Get earliest date
            earliest_doc = collection.find_one(
                {"symbol": symbol},
                sort=[("date", 1)]  # Ascending for earliest
            )
            
            # Get latest date
            latest_doc = collection.find_one(
                {"symbol": symbol},
                sort=[("date", -1)]  # Descending for latest
            )
            
            if earliest_doc and latest_doc:
                return (earliest_doc["date"], latest_doc["date"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get data range for {symbol}: {e}")
            raise
    
    @with_performance_monitoring("get_symbols")
    def get_symbols(self) -> List[str]:
        """
        Get all unique symbols in the database.
        
        Returns:
            List[str]: List of unique stock symbols
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            symbols = collection.distinct("symbol")
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            raise
    
    @with_performance_monitoring("get_missing_dates")
    def get_missing_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        exclude_weekends: bool = True
    ) -> List[datetime]:
        """
        Find missing trading dates for a symbol within a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date to check
            end_date: End date to check
            exclude_weekends: Whether to exclude weekends from missing dates
            
        Returns:
            List[datetime]: List of missing dates
        """
        # Get existing dates
        existing_data = self.get_stock_data(symbol, start_date, end_date)
        existing_dates = {data.date.date() for data in existing_data}
        
        # Generate expected dates
        expected_dates = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            if exclude_weekends and current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
                continue
            
            expected_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Find missing dates
        missing_dates = []
        for expected_date in expected_dates:
            if expected_date not in existing_dates:
                missing_dates.append(datetime.combine(expected_date, datetime.min.time()))
        
        return missing_dates
    
    @with_performance_monitoring("delete_old_data")
    def delete_old_data(self, symbol: str, before_date: datetime) -> int:
        """
        Delete stock data older than a specified date.
        
        Args:
            symbol: Stock symbol
            before_date: Delete data before this date
            
        Returns:
            int: Number of records deleted
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            result = collection.delete_many({
                "symbol": symbol,
                "date": {"$lt": before_date}
            })
            
            if result.deleted_count > 0:
                # Clear cache for this symbol
                self._clear_cache(symbol)
                logger.info(f"Deleted {result.deleted_count} old records for {symbol}")
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete old data for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_data_summary")
    def get_data_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get a summary of available data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Any]: Summary including date range, record count, etc.
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Get basic stats
            total_count = collection.count_documents({"symbol": symbol})
            
            if total_count == 0:
                return {
                    "symbol": symbol,
                    "total_records": 0,
                    "date_range": None,
                    "latest_date": None,
                    "data_completeness": 0.0
                }
            
            # Get date range
            date_range = self.get_data_range(symbol)
            latest_date = self.get_latest_date(symbol)
            
            # Calculate data completeness (excluding weekends)
            completeness = 0.0
            if date_range:
                start_date, end_date = date_range
                expected_days = 0
                current_date = start_date.date()
                end_date_only = end_date.date()
                
                while current_date <= end_date_only:
                    if current_date.weekday() < 5:  # Weekdays only
                        expected_days += 1
                    current_date += timedelta(days=1)
                
                if expected_days > 0:
                    completeness = total_count / expected_days
            
            return {
                "symbol": symbol,
                "total_records": total_count,
                "date_range": date_range,
                "latest_date": latest_date,
                "data_completeness": min(completeness, 1.0)  # Cap at 100%
            }
            
        except Exception as e:
            logger.error(f"Failed to get data summary for {symbol}: {e}")
            raise
    
    @with_performance_monitoring("bulk_get_latest_dates")
    def bulk_get_latest_dates(self, symbols: List[str]) -> Dict[str, Optional[datetime]]:
        """
        Get latest dates for multiple symbols efficiently.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict[str, Optional[datetime]]: Mapping of symbol to latest date
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Use aggregation pipeline for efficient bulk operation
            pipeline = [
                {"$match": {"symbol": {"$in": symbols}}},
                {"$group": {
                    "_id": "$symbol",
                    "latest_date": {"$max": "$date"}
                }}
            ]
            
            results = {}
            for doc in collection.aggregate(pipeline):
                results[doc["_id"]] = doc["latest_date"]
            
            # Ensure all symbols are in the result (with None for missing ones)
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to bulk get latest dates: {e}")
            raise
    
    def clear_symbol_cache(self, symbol: str) -> None:
        """
        Clear cache entries for a specific symbol.
        
        Args:
            symbol: Stock symbol to clear cache for
        """
        self._clear_cache(symbol)
        logger.debug(f"Cleared cache for symbol: {symbol}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics including hit rate, size, etc.
        """
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
        active_entries = total_entries - expired_entries
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl
        }