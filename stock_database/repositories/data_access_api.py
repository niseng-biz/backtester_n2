"""
Unified data access API that provides a high-level interface to all repositories.

This module provides a single entry point for accessing stock data, financial data,
and company information with optimized query patterns and caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from ..database_factory import DatabaseManager
from ..models.company_info import CompanyInfo
from ..models.financial_data import FinancialData
from ..models.stock_data import StockData
from .company_info_repository import CompanyInfoRepository
from .financial_data_repository import FinancialDataRepository
from .stock_data_repository import StockDataRepository

logger = logging.getLogger(__name__)


class DataAccessAPI:
    """
    Unified data access API providing high-level interface to all stock data repositories.
    
    This class combines StockDataRepository, FinancialDataRepository, and CompanyInfoRepository
    to provide optimized data access patterns with intelligent caching and query optimization.
    
    Features:
    - Unified interface for all data types
    - Cross-repository data correlation
    - Optimized bulk operations
    - Intelligent caching strategies
    - Performance monitoring and statistics
    """
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        stock_cache_ttl: int = 300,
        financial_cache_ttl: int = 600,
        company_cache_ttl: int = 1800
    ):
        """
        Initialize the unified data access API.
        
        Args:
            db_manager: MongoDB manager instance (creates new if None)
            stock_cache_ttl: Cache TTL for stock data in seconds (default: 5 minutes)
            financial_cache_ttl: Cache TTL for financial data in seconds (default: 10 minutes)
            company_cache_ttl: Cache TTL for company info in seconds (default: 30 minutes)
        """
        self.db_manager = db_manager or DatabaseManager()
        
        # Initialize repositories with shared database manager
        self.stock_repo = StockDataRepository(self.db_manager, stock_cache_ttl)
        self.financial_repo = FinancialDataRepository(self.db_manager, financial_cache_ttl)
        self.company_repo = CompanyInfoRepository(self.db_manager, company_cache_ttl)
        
        logger.info("DataAccessAPI initialized with shared database connection")
    
    def ensure_connection(self) -> None:
        """Ensure database connection is established."""
        self.db_manager.ensure_connection()
    
    # === Stock Data Methods ===
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StockData]:
        """
        Get stock data for a symbol within a date range.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of records
            
        Returns:
            List[StockData]: Stock data records
        """
        return self.stock_repo.get_stock_data(symbol, start_date, end_date, limit)
    
    def get_latest_stock_data(self, symbol: str) -> Optional[StockData]:
        """
        Get the most recent stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[StockData]: Latest stock data or None
        """
        latest_data = self.stock_repo.get_stock_data(symbol, limit=1)
        return latest_data[0] if latest_data else None
    
    def get_recent_stock_data(self, symbol: str, days: int = 30) -> List[StockData]:
        """
        Get recent stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of recent days
            
        Returns:
            List[StockData]: Recent stock data
        """
        return self.stock_repo.get_recent_data(symbol, days)
    
    # === Financial Data Methods ===
    
    def get_financial_data(
        self,
        symbol: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[FinancialData]:
        """
        Get financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year
            fiscal_quarter: Specific fiscal quarter
            limit: Maximum number of records
            
        Returns:
            List[FinancialData]: Financial data records
        """
        return self.financial_repo.get_financial_data(symbol, fiscal_year, fiscal_quarter, limit)
    
    def get_latest_financial_data(self, symbol: str, annual_only: bool = False) -> Optional[FinancialData]:
        """
        Get the most recent financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            annual_only: If True, only return annual data
            
        Returns:
            Optional[FinancialData]: Latest financial data or None
        """
        return self.financial_repo.get_latest_financial_data(symbol, annual_only)
    
    def get_financial_ratios(self, symbol: str, fiscal_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get financial ratios for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year (uses latest if None)
            
        Returns:
            Dict[str, Any]: Financial ratios and metrics
        """
        return self.financial_repo.get_financial_ratios(symbol, fiscal_year)
    
    # === Company Info Methods ===
    
    def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """
        Get company information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[CompanyInfo]: Company information or None
        """
        return self.company_repo.get_company_info(symbol)
    
    def search_companies(
        self,
        query: str,
        search_fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[CompanyInfo]:
        """
        Search companies by name, symbol, or other fields.
        
        Args:
            query: Search query string
            search_fields: Fields to search in
            limit: Maximum number of results
            
        Returns:
            List[CompanyInfo]: Matching companies
        """
        return self.company_repo.search_companies(query, search_fields, limit)
    
    # === Cross-Repository Methods ===
    
    def get_complete_company_data(
        self,
        symbol: str,
        include_stock_days: int = 30,
        include_financial_years: int = 5
    ) -> Dict[str, Any]:
        """
        Get complete data for a company including stock data, financial data, and company info.
        
        Args:
            symbol: Stock symbol
            include_stock_days: Number of recent stock data days to include
            include_financial_years: Number of recent financial years to include
            
        Returns:
            Dict[str, Any]: Complete company data
        """
        result = {
            "symbol": symbol,
            "company_info": None,
            "latest_stock_data": None,
            "recent_stock_data": [],
            "latest_financial_data": None,
            "annual_financial_data": [],
            "financial_ratios": {},
            "data_summary": {}
        }
        
        try:
            # Get company info
            result["company_info"] = self.get_company_info(symbol)
            
            # Get stock data
            result["latest_stock_data"] = self.get_latest_stock_data(symbol)
            result["recent_stock_data"] = self.get_recent_stock_data(symbol, include_stock_days)
            
            # Get financial data
            result["latest_financial_data"] = self.get_latest_financial_data(symbol, annual_only=True)
            result["annual_financial_data"] = self.financial_repo.get_annual_data(symbol, include_financial_years)
            result["financial_ratios"] = self.get_financial_ratios(symbol)
            
            # Get data summaries
            result["data_summary"] = {
                "stock_data": self.stock_repo.get_data_summary(symbol),
                "financial_data": self.financial_repo.get_data_summary(symbol)
            }
            
            logger.info(f"Retrieved complete data for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get complete data for {symbol}: {e}")
            raise
    
    def bulk_get_latest_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Efficiently get latest data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict[str, Dict[str, Any]]: Latest data for each symbol
        """
        result = {}
        
        try:
            # Bulk get latest stock dates
            latest_stock_dates = self.stock_repo.bulk_get_latest_dates(symbols)
            
            # Bulk get company info
            company_infos = self.company_repo.bulk_get_company_info(symbols)
            
            # Process each symbol
            for symbol in symbols:
                symbol_data = {
                    "symbol": symbol,
                    "latest_stock_date": latest_stock_dates.get(symbol),
                    "company_info": company_infos.get(symbol),
                    "latest_financial_data": None
                }
                
                # Get latest financial data (individual calls for now)
                try:
                    symbol_data["latest_financial_data"] = self.get_latest_financial_data(symbol, annual_only=True)
                except Exception as e:
                    logger.warning(f"Failed to get financial data for {symbol}: {e}")
                
                result[symbol] = symbol_data
            
            logger.info(f"Retrieved bulk latest data for {len(symbols)} symbols")
            return result
            
        except Exception as e:
            logger.error(f"Failed to bulk get latest data: {e}")
            raise
    
    def get_sector_analysis(self, sector: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive analysis for companies in a specific sector.
        
        Args:
            sector: Business sector name
            limit: Maximum number of companies to analyze
            
        Returns:
            Dict[str, Any]: Sector analysis data
        """
        try:
            # Get companies in sector
            companies = self.company_repo.get_companies_by_sector(sector)
            
            if limit:
                companies = companies[:limit]
            
            symbols = [company.symbol for company in companies]
            
            # Get bulk latest data
            latest_data = self.bulk_get_latest_data(symbols)
            
            # Calculate sector statistics
            market_caps = []
            financial_ratios = {"per": [], "roe": [], "pbr": []}
            
            for symbol in symbols:
                company_info = latest_data[symbol]["company_info"]
                if company_info and company_info.market_cap:
                    market_caps.append(company_info.market_cap)
                
                # Get financial ratios
                try:
                    ratios = self.get_financial_ratios(symbol)
                    for ratio_name in financial_ratios:
                        if ratio_name in ratios and ratios[ratio_name] is not None:
                            financial_ratios[ratio_name].append(ratios[ratio_name])
                except Exception:
                    continue
            
            # Calculate statistics
            sector_stats = {
                "sector": sector,
                "company_count": len(companies),
                "companies": [company.to_dict() for company in companies],
                "latest_data": latest_data,
                "market_cap_stats": self._calculate_stats(market_caps) if market_caps else {},
                "financial_ratio_stats": {
                    ratio: self._calculate_stats(values) 
                    for ratio, values in financial_ratios.items() 
                    if values
                }
            }
            
            logger.info(f"Generated sector analysis for {sector} with {len(companies)} companies")
            return sector_stats
            
        except Exception as e:
            logger.error(f"Failed to get sector analysis for {sector}: {e}")
            raise
    
    def compare_companies(
        self,
        symbols: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple companies across various metrics.
        
        Args:
            symbols: List of stock symbols to compare
            metrics: List of metrics to compare (uses default set if None)
            
        Returns:
            Dict[str, Any]: Comparison data
        """
        if metrics is None:
            metrics = ["market_cap", "per", "roe", "pbr", "revenue", "net_income"]
        
        try:
            comparison_data = {
                "symbols": symbols,
                "metrics": metrics,
                "company_data": {},
                "metric_comparisons": {},
                "rankings": {}
            }
            
            # Get data for each company
            for symbol in symbols:
                try:
                    company_info = self.get_company_info(symbol)
                    financial_ratios = self.get_financial_ratios(symbol)
                    latest_financial = self.get_latest_financial_data(symbol, annual_only=True)
                    
                    comparison_data["company_data"][symbol] = {
                        "company_info": company_info.to_dict() if company_info else None,
                        "financial_ratios": financial_ratios,
                        "latest_financial": latest_financial.to_dict() if latest_financial else None
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
                    comparison_data["company_data"][symbol] = None
            
            # Compare metrics
            for metric in metrics:
                metric_values = {}
                
                for symbol in symbols:
                    data = comparison_data["company_data"][symbol]
                    if not data:
                        continue
                    
                    value = None
                    
                    # Try to get value from different sources
                    if data["company_info"] and metric in data["company_info"]:
                        value = data["company_info"][metric]
                    elif metric in data["financial_ratios"]:
                        value = data["financial_ratios"][metric]
                    elif data["latest_financial"] and metric in data["latest_financial"]:
                        value = data["latest_financial"][metric]
                    
                    if value is not None:
                        metric_values[symbol] = value
                
                if metric_values:
                    comparison_data["metric_comparisons"][metric] = {
                        "values": metric_values,
                        "statistics": self._calculate_stats(list(metric_values.values())),
                        "ranking": sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
                    }
            
            logger.info(f"Generated comparison for {len(symbols)} companies")
            return comparison_data
            
        except Exception as e:
            logger.error(f"Failed to compare companies: {e}")
            raise
    
    # === Data Management Methods ===
    
    def save_all_data(
        self,
        stock_data: Optional[List[StockData]] = None,
        financial_data: Optional[List[FinancialData]] = None,
        company_info: Optional[List[CompanyInfo]] = None
    ) -> Dict[str, int]:
        """
        Save data to all repositories in a coordinated manner.
        
        Args:
            stock_data: Stock data to save
            financial_data: Financial data to save
            company_info: Company info to save
            
        Returns:
            Dict[str, int]: Count of records saved by type
        """
        saved_counts = {"stock_data": 0, "financial_data": 0, "company_info": 0}
        
        try:
            if stock_data:
                self.stock_repo.save_stock_data(stock_data)
                saved_counts["stock_data"] = len(stock_data)
            
            if financial_data:
                self.financial_repo.save_financial_data(financial_data)
                saved_counts["financial_data"] = len(financial_data)
            
            if company_info:
                self.company_repo.save_company_info(company_info)
                saved_counts["company_info"] = len(company_info)
            
            logger.info(f"Saved data: {saved_counts}")
            return saved_counts
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache across all repositories.
        
        Args:
            symbol: Specific symbol to clear (clears all if None)
        """
        if symbol:
            self.stock_repo.clear_symbol_cache(symbol)
            self.financial_repo.clear_symbol_cache(symbol)
            self.company_repo.clear_symbol_cache(symbol)
            logger.info(f"Cleared cache for symbol: {symbol}")
        else:
            self.stock_repo._clear_cache()
            self.financial_repo._clear_cache()
            self.company_repo._clear_cache()
            logger.info("Cleared all cache")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics from all repositories.
        
        Returns:
            Dict[str, Any]: System statistics
        """
        try:
            stats = {
                "database_stats": {
                    "stock_data": self.stock_repo.get_collection_stats(),
                    "financial_data": self.financial_repo.get_collection_stats(),
                    "company_info": self.company_repo.get_collection_stats()
                },
                "cache_stats": {
                    "stock_data": self.stock_repo.get_cache_stats(),
                    "financial_data": self.financial_repo.get_cache_stats(),
                    "company_info": self.company_repo.get_cache_stats()
                },
                "query_stats": {
                    "stock_data": self.stock_repo.get_query_stats(),
                    "financial_data": self.financial_repo.get_query_stats(),
                    "company_info": self.company_repo.get_query_stats()
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            raise
    
    # === Utility Methods ===
    
    def _calculate_stats(self, values: List[Union[int, float]]) -> Dict[str, float]:
        """
        Calculate basic statistics for a list of numeric values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dict[str, float]: Statistics (min, max, mean, median, etc.)
        """
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(values)
        
        stats = {
            "count": n,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / n,
            "median": sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        }
        
        # Calculate standard deviation
        if n > 1:
            variance = sum((x - stats["mean"]) ** 2 for x in values) / (n - 1)
            stats["std_dev"] = variance ** 0.5
        else:
            stats["std_dev"] = 0.0
        
        return stats
    
    def get_available_symbols(self) -> Dict[str, List[str]]:
        """
        Get all available symbols from each repository.
        
        Returns:
            Dict[str, List[str]]: Available symbols by data type
        """
        try:
            return {
                "stock_data": self.stock_repo.get_symbols(),
                "financial_data": self.financial_repo.get_symbols(),
                "company_info": self.company_repo.get_all_symbols()
            }
        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on all repositories and database connections.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        health_status = {
            "overall_status": "healthy",
            "database_connection": False,
            "repositories": {
                "stock_data": False,
                "financial_data": False,
                "company_info": False
            },
            "errors": []
        }
        
        try:
            # Check database connection
            self.ensure_connection()
            health_status["database_connection"] = True
            
            # Check each repository
            try:
                self.stock_repo.get_symbols()
                health_status["repositories"]["stock_data"] = True
            except Exception as e:
                health_status["errors"].append(f"Stock data repository error: {e}")
            
            try:
                self.financial_repo.get_symbols()
                health_status["repositories"]["financial_data"] = True
            except Exception as e:
                health_status["errors"].append(f"Financial data repository error: {e}")
            
            try:
                self.company_repo.get_all_symbols()
                health_status["repositories"]["company_info"] = True
            except Exception as e:
                health_status["errors"].append(f"Company info repository error: {e}")
            
            # Determine overall status
            if not health_status["database_connection"]:
                health_status["overall_status"] = "unhealthy"
            elif not all(health_status["repositories"].values()):
                health_status["overall_status"] = "degraded"
            
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["errors"].append(f"Database connection error: {e}")
        
        return health_status