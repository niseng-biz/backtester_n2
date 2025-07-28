"""
Backtester integration adapter for converting stock database data to backtester format.

This module provides the BacktesterDataAdapter class that bridges the stock database
with the backtester system by converting StockData objects to MarketData format
and providing optimized data retrieval for backtesting operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from ..database_factory import DatabaseManager
from ..models.stock_data import StockData
from ..repositories.data_access_api import DataAccessAPI

logger = logging.getLogger(__name__)

# Import MarketData from backtester if available, otherwise define a compatible version
try:
    from backtester.models import MarketData
except ImportError:
    # Define a compatible MarketData class for testing
    from dataclasses import dataclass
    
    @dataclass
    class MarketData:
        """Compatible MarketData class for testing purposes."""
        timestamp: datetime
        open: float
        high: float
        low: float
        close: float
        volume: int


class BacktesterDataAdapter:
    """
    Adapter for integrating stock database with backtester system.
    
    This adapter provides efficient data conversion and retrieval optimized for
    backtesting operations, including:
    - StockData to MarketData conversion
    - Date range queries with performance optimization
    - Memory-efficient data streaming for large datasets
    - Batch processing for multiple symbols
    - Caching for frequently accessed data
    
    Features:
    - Lazy loading for memory efficiency
    - Optimized queries with proper indexing
    - Data validation and error handling
    - Performance monitoring and logging
    """
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        cache_ttl: int = 600,
        batch_size: int = 1000
    ):
        """
        Initialize the backtester data adapter.
        
        Args:
            db_manager: MongoDB manager instance (creates new if None)
            cache_ttl: Cache time-to-live in seconds (default: 10 minutes)
            batch_size: Batch size for bulk operations (default: 1000)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.data_api = DataAccessAPI(self.db_manager, stock_cache_ttl=cache_ttl)
        self.batch_size = batch_size
        self.cache_ttl = cache_ttl
        
        # Performance tracking
        self._query_count = 0
        self._conversion_count = 0
        self._cache_hits = 0
        
        logger.info(f"BacktesterDataAdapter initialized with batch_size={batch_size}, cache_ttl={cache_ttl}")
    
    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        """
        Get market data for backtesting in MarketData format.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date for data retrieval (inclusive)
            end_date: End date for data retrieval (inclusive)
            limit: Maximum number of records to return
            
        Returns:
            List[MarketData]: List of market data records sorted by date (oldest first)
            
        Raises:
            ValueError: If symbol is invalid or no data found
            Exception: If database operation fails
        """
        try:
            self._query_count += 1
            
            # Validate inputs
            if not symbol or not isinstance(symbol, str):
                raise ValueError("Symbol must be a non-empty string")
            
            # Get stock data from repository
            stock_data = self.data_api.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not stock_data:
                logger.warning(f"No stock data found for symbol {symbol}")
                return []
            
            # Convert to MarketData format
            market_data = self.convert_to_market_data(stock_data)
            
            # Sort by timestamp (oldest first for backtesting)
            market_data.sort(key=lambda x: x.timestamp)
            
            logger.info(f"Retrieved {len(market_data)} market data records for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            raise
    
    def convert_to_market_data(self, stock_data: List[StockData]) -> List[MarketData]:
        """
        Convert StockData objects to MarketData format.
        
        Args:
            stock_data: List of StockData objects to convert
            
        Returns:
            List[MarketData]: Converted market data objects
            
        Raises:
            ValueError: If stock_data is invalid
        """
        if not stock_data:
            return []
        
        try:
            market_data = []
            
            for stock_item in stock_data:
                # Validate stock data
                if not stock_item.validate():
                    logger.warning(f"Invalid stock data for {stock_item.symbol} on {stock_item.date}")
                    continue
                
                # Convert to MarketData
                market_item = MarketData(
                    timestamp=stock_item.date,
                    open=stock_item.open,
                    high=stock_item.high,
                    low=stock_item.low,
                    close=stock_item.close,
                    volume=stock_item.volume
                )
                
                market_data.append(market_item)
                self._conversion_count += 1
            
            logger.debug(f"Converted {len(market_data)} stock data records to market data")
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to convert stock data to market data: {e}")
            raise
    
    def get_market_data_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[MarketData]:
        """
        Get market data for a specific date range with optimized performance.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List[MarketData]: Market data for the specified range
        """
        try:
            # Validate date range
            if start_date > end_date:
                raise ValueError("Start date must be before or equal to end date")
            
            # Calculate expected number of trading days (rough estimate)
            total_days = (end_date - start_date).days + 1
            expected_trading_days = int(total_days * 5/7)  # Rough estimate excluding weekends
            
            # Use streaming approach for large datasets
            if expected_trading_days > self.batch_size:
                return self._get_market_data_streaming(symbol, start_date, end_date)
            else:
                return self.get_market_data(symbol, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Failed to get market data range for {symbol}: {e}")
            raise
    
    def _get_market_data_streaming(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[MarketData]:
        """
        Get market data using streaming approach for memory efficiency.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            List[MarketData]: Market data retrieved in batches
        """
        market_data = []
        current_start = start_date
        
        while current_start <= end_date:
            # Calculate batch end date
            batch_end = min(
                current_start + timedelta(days=self.batch_size // 5 * 7),  # Approximate trading days to calendar days
                end_date
            )
            
            # Get batch data
            batch_stock_data = self.data_api.get_stock_data(
                symbol=symbol,
                start_date=current_start,
                end_date=batch_end
            )
            
            if batch_stock_data:
                batch_market_data = self.convert_to_market_data(batch_stock_data)
                market_data.extend(batch_market_data)
            
            # Move to next batch
            current_start = batch_end + timedelta(days=1)
        
        # Sort final result
        market_data.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Retrieved {len(market_data)} records using streaming approach for {symbol}")
        return market_data
    
    def get_multiple_symbols_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[MarketData]]:
        """
        Get market data for multiple symbols efficiently.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            Dict[str, List[MarketData]]: Market data by symbol
        """
        try:
            result = {}
            
            for symbol in symbols:
                try:
                    market_data = self.get_market_data(symbol, start_date, end_date)
                    result[symbol] = market_data
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
                    result[symbol] = []
            
            logger.info(f"Retrieved data for {len(symbols)} symbols")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get multiple symbols data: {e}")
            raise
    
    def get_latest_market_data(self, symbol: str, days: int = 1) -> List[MarketData]:
        """
        Get the most recent market data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of recent days to retrieve (default: 1)
            
        Returns:
            List[MarketData]: Recent market data
        """
        try:
            stock_data = self.data_api.get_recent_stock_data(symbol, days)
            return self.convert_to_market_data(stock_data)
            
        except Exception as e:
            logger.error(f"Failed to get latest market data for {symbol}: {e}")
            raise
    
    def validate_data_availability(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        min_data_points: int = 1
    ) -> Dict[str, Any]:
        """
        Validate data availability for backtesting requirements.
        
        Args:
            symbol: Stock symbol
            start_date: Required start date
            end_date: Required end date
            min_data_points: Minimum required data points
            
        Returns:
            Dict[str, Any]: Validation results including availability status and gaps
        """
        try:
            # Get data summary
            data_summary = self.data_api.stock_repo.get_data_summary(symbol)
            
            validation_result = {
                "symbol": symbol,
                "is_available": False,
                "data_points": 0,
                "date_range_available": None,
                "missing_dates": [],
                "data_completeness": 0.0,
                "warnings": []
            }
            
            if data_summary["total_records"] == 0:
                validation_result["warnings"].append("No data available for symbol")
                return validation_result
            
            # Check date range availability
            available_range = data_summary["date_range"]
            if available_range:
                available_start, available_end = available_range
                
                if available_start > start_date:
                    validation_result["warnings"].append(
                        f"Data starts later than required: {available_start} > {start_date}"
                    )
                
                if available_end < end_date:
                    validation_result["warnings"].append(
                        f"Data ends earlier than required: {available_end} < {end_date}"
                    )
                
                # Get actual data in range
                market_data = self.get_market_data(symbol, start_date, end_date)
                validation_result["data_points"] = len(market_data)
                validation_result["is_available"] = len(market_data) >= min_data_points
                validation_result["date_range_available"] = (
                    market_data[0].timestamp if market_data else None,
                    market_data[-1].timestamp if market_data else None
                )
                
                # Find missing dates
                if market_data:
                    missing_dates = self.data_api.stock_repo.get_missing_dates(
                        symbol, start_date, end_date
                    )
                    validation_result["missing_dates"] = missing_dates
                
                validation_result["data_completeness"] = data_summary["data_completeness"]
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate data availability for {symbol}: {e}")
            raise
    
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive data statistics for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Any]: Data statistics including volume, price ranges, etc.
        """
        try:
            # Get recent data for statistics
            recent_data = self.data_api.get_recent_stock_data(symbol, days=252)  # ~1 year
            
            if not recent_data:
                return {"symbol": symbol, "error": "No data available"}
            
            # Calculate statistics
            prices = [data.close for data in recent_data]
            volumes = [data.volume for data in recent_data]
            
            stats = {
                "symbol": symbol,
                "data_points": len(recent_data),
                "date_range": (recent_data[-1].date, recent_data[0].date),  # Oldest to newest
                "price_statistics": {
                    "min": min(prices),
                    "max": max(prices),
                    "mean": sum(prices) / len(prices),
                    "current": prices[0]  # Most recent (first in list)
                },
                "volume_statistics": {
                    "min": min(volumes),
                    "max": max(volumes),
                    "mean": sum(volumes) / len(volumes),
                    "current": volumes[0]
                }
            }
            
            # Calculate volatility (standard deviation of returns)
            if len(prices) > 1:
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                mean_return = sum(returns) / len(returns)
                variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                stats["volatility"] = variance ** 0.5
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get data statistics for {symbol}: {e}")
            raise
    
    def optimize_for_backtesting(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        preload: bool = True
    ) -> Dict[str, Any]:
        """
        Optimize data access for backtesting by preloading and caching data.
        
        Args:
            symbol: Stock symbol
            start_date: Backtesting start date
            end_date: Backtesting end date
            preload: Whether to preload all data into memory
            
        Returns:
            Dict[str, Any]: Optimization results and cached data info
        """
        try:
            optimization_result = {
                "symbol": symbol,
                "date_range": (start_date, end_date),
                "preloaded": False,
                "data_points": 0,
                "memory_usage_mb": 0,
                "optimization_time": 0
            }
            
            start_time = datetime.now()
            
            if preload:
                # Preload all data for the backtesting period
                market_data = self.get_market_data(symbol, start_date, end_date)
                optimization_result["data_points"] = len(market_data)
                optimization_result["preloaded"] = True
                
                # Estimate memory usage (rough calculation)
                # Each MarketData object: ~8 bytes * 6 fields = 48 bytes + overhead
                estimated_memory = len(market_data) * 64 / (1024 * 1024)  # MB
                optimization_result["memory_usage_mb"] = round(estimated_memory, 2)
            
            optimization_result["optimization_time"] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Optimized data access for {symbol}: {optimization_result}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Failed to optimize for backtesting {symbol}: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get adapter performance statistics.
        
        Returns:
            Dict[str, Any]: Performance statistics
        """
        return {
            "query_count": self._query_count,
            "conversion_count": self._conversion_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": self._cache_hits / max(self._query_count, 1),
            "batch_size": self.batch_size,
            "cache_ttl": self.cache_ttl
        }
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear adapter cache.
        
        Args:
            symbol: Specific symbol to clear (clears all if None)
        """
        self.data_api.clear_cache(symbol)
        logger.info(f"Cleared adapter cache for {'all symbols' if symbol is None else symbol}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the adapter and underlying systems.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            # Check underlying data API health
            api_health = self.data_api.health_check()
            
            adapter_health = {
                "adapter_status": "healthy",
                "data_api_status": api_health["overall_status"],
                "performance_stats": self.get_performance_stats(),
                "errors": []
            }
            
            # Test basic functionality
            try:
                symbols = self.data_api.get_available_symbols()["stock_data"]
                if symbols:
                    test_symbol = symbols[0]
                    test_data = self.get_latest_market_data(test_symbol, days=1)
                    adapter_health["test_conversion"] = len(test_data) > 0
                else:
                    adapter_health["test_conversion"] = False
                    adapter_health["errors"].append("No symbols available for testing")
            except Exception as e:
                adapter_health["test_conversion"] = False
                adapter_health["errors"].append(f"Test conversion failed: {e}")
            
            # Determine overall status
            if api_health["overall_status"] != "healthy" or not adapter_health["test_conversion"]:
                adapter_health["adapter_status"] = "degraded"
            
            return adapter_health
            
        except Exception as e:
            return {
                "adapter_status": "unhealthy",
                "error": str(e)
            }