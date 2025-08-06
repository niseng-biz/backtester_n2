"""
Financial data repository for efficient financial metrics access and management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..sqlite_database import SQLiteManager
from ..models.financial_data import FinancialData
from .base_repository import (BaseRepository, with_caching,
                              with_performance_monitoring)

logger = logging.getLogger(__name__)


class FinancialDataRepository(BaseRepository):
    """
    Repository for financial data operations with caching and performance optimization.
    
    Provides efficient access to financial data with features like:
    - Cached queries for frequently accessed data
    - Fiscal year and quarter-based queries
    - Financial ratio calculations and trends
    - Performance monitoring
    """
    
    def __init__(self, db_manager: Optional[SQLiteManager] = None, cache_ttl: int = 600):
        """
        Initialize financial data repository.
        
        Args:
            db_manager: MongoDB manager instance
            cache_ttl: Cache time-to-live in seconds (default: 10 minutes for financial data)
        """
        super().__init__(db_manager, cache_ttl)
        self.collection_name = self.db_manager.FINANCIAL_DATA_COLLECTION
    
    def get_collection_name(self) -> str:
        """Get the collection name for this repository."""
        return self.collection_name
    
    @with_performance_monitoring("save_financial_data")
    def save_financial_data(self, data: List[FinancialData]) -> None:
        """
        Save financial data to the database using upsert operations.
        
        Args:
            data: List of FinancialData instances to save
            
        Raises:
            ValueError: If data validation fails
        """
        if not data:
            logger.warning("No financial data provided to save")
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
            logger.warning(f"Found {len(invalid_data)} invalid financial data records")
            for item in invalid_data:
                logger.debug(f"Invalid data: {item.symbol} FY{item.fiscal_year}")
        
        if not valid_data:
            raise ValueError("No valid financial data to save")
        
        # Use upsert to handle duplicates gracefully
        self.db_manager.upsert_financial_data(valid_data)
        
        # Clear cache for affected symbols
        symbols = {item.symbol for item in valid_data}
        for symbol in symbols:
            self._clear_cache(symbol)
        
        logger.info(f"Saved {len(valid_data)} financial data records")
    
    @with_caching()
    @with_performance_monitoring("get_financial_data")
    def get_financial_data(
        self,
        symbol: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[FinancialData]:
        """
        Retrieve financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year (optional)
            fiscal_quarter: Specific fiscal quarter (optional)
            limit: Maximum number of records to return
            
        Returns:
            List[FinancialData]: List of financial data records sorted by fiscal year/quarter (newest first)
        """
        data = self.db_manager.get_financial_data(symbol, fiscal_year, fiscal_quarter)
        
        if limit and len(data) > limit:
            return data[:limit]
        
        return data
    
    @with_caching()
    @with_performance_monitoring("get_latest_financial_data")
    def get_latest_financial_data(self, symbol: str, annual_only: bool = False) -> Optional[FinancialData]:
        """
        Get the most recent financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            annual_only: If True, only return annual data (fiscal_quarter is None)
            
        Returns:
            Optional[FinancialData]: Latest financial data or None if not found
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            query = {"symbol": symbol}
            if annual_only:
                query["fiscal_quarter"] = None
            
            doc = collection.find_one(
                query,
                sort=[("fiscal_year", -1), ("fiscal_quarter", -1)]
            )
            
            if doc:
                return self.db_manager._doc_to_financial_data(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest financial data for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_annual_data")
    def get_annual_data(self, symbol: str, years: Optional[int] = None) -> List[FinancialData]:
        """
        Get annual financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            years: Number of recent years to retrieve (optional)
            
        Returns:
            List[FinancialData]: Annual financial data records
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            query = {"symbol": symbol, "fiscal_quarter": None}
            
            cursor = collection.find(query).sort("fiscal_year", -1)
            
            if years:
                cursor = cursor.limit(years)
            
            results = []
            for doc in cursor:
                financial_data = self.db_manager._doc_to_financial_data(doc)
                results.append(financial_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get annual data for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_quarterly_data")
    def get_quarterly_data(self, symbol: str, fiscal_year: Optional[int] = None) -> List[FinancialData]:
        """
        Get quarterly financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year (optional, if None returns all quarters)
            
        Returns:
            List[FinancialData]: Quarterly financial data records
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            query = {
                "symbol": symbol,
                "fiscal_quarter": {"$ne": None}
            }
            
            if fiscal_year:
                query["fiscal_year"] = fiscal_year
            
            cursor = collection.find(query).sort([
                ("fiscal_year", -1),
                ("fiscal_quarter", -1)
            ])
            
            results = []
            for doc in cursor:
                financial_data = self.db_manager._doc_to_financial_data(doc)
                results.append(financial_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get quarterly data for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_fiscal_year_range")
    def get_fiscal_year_range(self, symbol: str) -> Optional[Tuple[int, int]]:
        """
        Get the fiscal year range (earliest and latest) for a symbol's data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[Tuple[int, int]]: (earliest_year, latest_year) or None if no data
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Get earliest year
            earliest_doc = collection.find_one(
                {"symbol": symbol},
                sort=[("fiscal_year", 1)]
            )
            
            # Get latest year
            latest_doc = collection.find_one(
                {"symbol": symbol},
                sort=[("fiscal_year", -1)]
            )
            
            if earliest_doc and latest_doc:
                return (earliest_doc["fiscal_year"], latest_doc["fiscal_year"])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get fiscal year range for {symbol}: {e}")
            raise
    
    @with_performance_monitoring("get_symbols")
    def get_symbols(self) -> List[str]:
        """
        Get all unique symbols in the financial data collection.
        
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
    
    @with_caching()
    @with_performance_monitoring("calculate_growth_rates")
    def calculate_growth_rates(
        self,
        symbol: str,
        metric: str,
        periods: int = 5,
        annual_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Calculate growth rates for a specific financial metric.
        
        Args:
            symbol: Stock symbol
            metric: Financial metric field name (e.g., 'revenue', 'net_income')
            periods: Number of periods to analyze
            annual_only: If True, only use annual data
            
        Returns:
            List[Dict[str, Any]]: Growth rate data with fiscal year and growth rate
        """
        if annual_only:
            data = self.get_annual_data(symbol, periods + 1)  # Need one extra for calculation
        else:
            data = self.get_financial_data(symbol, limit=periods + 1)
        
        if len(data) < 2:
            return []
        
        # Sort by fiscal year (oldest first for growth calculation)
        data.sort(key=lambda x: (x.fiscal_year, x.fiscal_quarter or 0))
        
        growth_rates = []
        
        for i in range(1, len(data)):
            current = data[i]
            previous = data[i - 1]
            
            current_value = getattr(current, metric, None)
            previous_value = getattr(previous, metric, None)
            
            if current_value is not None and previous_value is not None and previous_value != 0:
                growth_rate = ((current_value - previous_value) / abs(previous_value)) * 100
                
                growth_rates.append({
                    "fiscal_year": current.fiscal_year,
                    "fiscal_quarter": current.fiscal_quarter,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "growth_rate": growth_rate
                })
        
        return growth_rates
    
    @with_caching()
    @with_performance_monitoring("get_financial_ratios")
    def get_financial_ratios(self, symbol: str, fiscal_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get financial ratios for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year (if None, uses latest data)
            
        Returns:
            Dict[str, Any]: Financial ratios and metrics
        """
        if fiscal_year:
            data_list = self.get_financial_data(symbol, fiscal_year=fiscal_year)
            if not data_list:
                return {}
            data = data_list[0]  # Get the first (and likely only) record for that year
        else:
            data = self.get_latest_financial_data(symbol, annual_only=True)
            if not data:
                return {}
        
        ratios = {
            "fiscal_year": data.fiscal_year,
            "fiscal_quarter": data.fiscal_quarter,
            "symbol": data.symbol
        }
        
        # Add available ratios
        ratio_fields = [
            "per", "pbr", "roe", "roa", "debt_to_equity", "current_ratio"
        ]
        
        for field in ratio_fields:
            value = getattr(data, field, None)
            if value is not None:
                ratios[field] = value
        
        # Calculate additional ratios if data is available
        if data.revenue and data.net_income:
            ratios["net_margin"] = (data.net_income / data.revenue) * 100
        
        if data.total_assets and data.revenue:
            ratios["asset_turnover"] = data.revenue / data.total_assets
        
        if data.shareholders_equity and data.total_assets:
            ratios["equity_ratio"] = (data.shareholders_equity / data.total_assets) * 100
        
        return ratios
    
    @with_performance_monitoring("compare_metrics")
    def compare_metrics(
        self,
        symbols: List[str],
        metric: str,
        fiscal_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare a financial metric across multiple symbols.
        
        Args:
            symbols: List of stock symbols to compare
            metric: Financial metric field name
            fiscal_year: Specific fiscal year (if None, uses latest data for each symbol)
            
        Returns:
            Dict[str, Any]: Comparison data with statistics
        """
        comparison_data = {}
        values = []
        
        for symbol in symbols:
            if fiscal_year:
                data_list = self.get_financial_data(symbol, fiscal_year=fiscal_year)
                data = data_list[0] if data_list else None
            else:
                data = self.get_latest_financial_data(symbol, annual_only=True)
            
            if data:
                value = getattr(data, metric, None)
                if value is not None:
                    comparison_data[symbol] = {
                        "value": value,
                        "fiscal_year": data.fiscal_year,
                        "fiscal_quarter": data.fiscal_quarter
                    }
                    values.append(value)
        
        # Calculate statistics
        statistics = {}
        if values:
            statistics = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "average": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2] if values else 0
            }
        
        return {
            "metric": metric,
            "fiscal_year": fiscal_year,
            "data": comparison_data,
            "statistics": statistics
        }
    
    @with_caching()
    @with_performance_monitoring("get_data_summary")
    def get_data_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get a summary of available financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Any]: Summary including fiscal year range, record count, etc.
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Get basic stats
            total_count = collection.count_documents({"symbol": symbol})
            annual_count = collection.count_documents({"symbol": symbol, "fiscal_quarter": None})
            quarterly_count = collection.count_documents({"symbol": symbol, "fiscal_quarter": {"$ne": None}})
            
            if total_count == 0:
                return {
                    "symbol": symbol,
                    "total_records": 0,
                    "annual_records": 0,
                    "quarterly_records": 0,
                    "fiscal_year_range": None,
                    "latest_annual_year": None,
                    "latest_quarterly_year": None
                }
            
            # Get fiscal year range
            fiscal_year_range = self.get_fiscal_year_range(symbol)
            
            # Get latest years
            latest_annual = self.get_latest_financial_data(symbol, annual_only=True)
            latest_quarterly = collection.find_one(
                {"symbol": symbol, "fiscal_quarter": {"$ne": None}},
                sort=[("fiscal_year", -1), ("fiscal_quarter", -1)]
            )
            
            return {
                "symbol": symbol,
                "total_records": total_count,
                "annual_records": annual_count,
                "quarterly_records": quarterly_count,
                "fiscal_year_range": fiscal_year_range,
                "latest_annual_year": latest_annual.fiscal_year if latest_annual else None,
                "latest_quarterly_year": latest_quarterly["fiscal_year"] if latest_quarterly else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get data summary for {symbol}: {e}")
            raise
    
    def clear_symbol_cache(self, symbol: str) -> None:
        """
        Clear cache entries for a specific symbol.
        
        Args:
            symbol: Stock symbol to clear cache for
        """
        self._clear_cache(symbol)
        logger.debug(f"Cleared financial data cache for symbol: {symbol}")