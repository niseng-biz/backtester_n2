"""
Base repository class with common functionality for all repositories.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Generic, Optional, TypeVar

from ..database_factory import DatabaseManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry(Generic[T]):
    """Cache entry with expiration time."""
    
    def __init__(self, data: T, ttl_seconds: int = 300):
        """
        Initialize cache entry.
        
        Args:
            data: Data to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def get_data(self) -> Optional[T]:
        """Get cached data if not expired."""
        if self.is_expired():
            return None
        return self.data


class BaseRepository(ABC):
    """
    Base repository class providing common functionality for all repositories.
    
    Features:
    - Database connection management
    - Basic caching functionality
    - Query performance monitoring
    - Error handling and logging
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, cache_ttl: int = 300):
        """
        Initialize base repository.
        
        Args:
            db_manager: MongoDB manager instance. If None, creates new instance.
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._query_stats: Dict[str, Dict[str, Any]] = {}
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: Cache key
        """
        # Create a simple cache key from arguments
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, datetime):
                key_parts.append(f"{k}={v.isoformat()}")
            else:
                key_parts.append(f"{k}={v}")
        
        return "|".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if available and not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Optional[Any]: Cached data or None if not found/expired
        """
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            data = entry.get_data()
            if data is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return data
            else:
                # Remove expired entry
                del self._cache[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """
        Store data in cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        self._cache[cache_key] = CacheEntry(data, self.cache_ttl)
        logger.debug(f"Cached data for key: {cache_key}")
    
    def _clear_cache(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys. If None, clears all cache.
        """
        if pattern is None:
            self._cache.clear()
            logger.debug("Cleared all cache entries")
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
    
    def _record_query_stats(self, operation: str, duration: float, result_count: int = 0) -> None:
        """
        Record query performance statistics.
        
        Args:
            operation: Operation name
            duration: Query duration in seconds
            result_count: Number of results returned
        """
        if operation not in self._query_stats:
            self._query_stats[operation] = {
                'count': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'total_results': 0
            }
        
        stats = self._query_stats[operation]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['max_duration'] = max(stats['max_duration'], duration)
        stats['total_results'] += result_count
        
        logger.debug(f"Query stats for {operation}: {duration:.3f}s, {result_count} results")
    
    def get_query_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get query performance statistics.
        
        Returns:
            Dict[str, Dict[str, Any]]: Query statistics by operation
        """
        return self._query_stats.copy()
    
    def clear_query_stats(self) -> None:
        """Clear query performance statistics."""
        self._query_stats.clear()
        logger.debug("Cleared query statistics")
    
    def ensure_connection(self) -> None:
        """Ensure database connection is established."""
        self.db_manager.ensure_connection()
    
    @abstractmethod
    def get_collection_name(self) -> str:
        """
        Get the collection name for this repository.
        
        Returns:
            str: Collection name
        """
        pass
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the repository's collection.
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        return self.db_manager.get_collection_stats(self.get_collection_name())


def with_performance_monitoring(operation_name: str):
    """
    Decorator to monitor query performance.
    
    Args:
        operation_name: Name of the operation for statistics
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                duration = time.time() - start_time
                
                # Count results if it's a list
                result_count = len(result) if isinstance(result, list) else (1 if result is not None else 0)
                
                self._record_query_stats(operation_name, duration, result_count)
                return result
            except Exception as e:
                duration = time.time() - start_time
                self._record_query_stats(f"{operation_name}_error", duration, 0)
                raise
        return wrapper
    return decorator


def with_caching(cache_key_func=None):
    """
    Decorator to add caching to repository methods.
    
    Args:
        cache_key_func: Function to generate cache key. If None, uses default key generation.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(self, *args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{self._get_cache_key(*args, **kwargs)}"
            
            # Try to get from cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            if result is not None:
                self._set_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator