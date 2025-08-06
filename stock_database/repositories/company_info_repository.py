"""
Company information repository for efficient company metadata access and management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..sqlite_database import SQLiteManager
from ..models.company_info import CompanyInfo
from .base_repository import (BaseRepository, with_caching,
                              with_performance_monitoring)

logger = logging.getLogger(__name__)


class CompanyInfoRepository(BaseRepository):
    """
    Repository for company information operations with caching and performance optimization.
    
    Provides efficient access to company metadata with features like:
    - Cached queries for frequently accessed data
    - Sector and industry-based filtering
    - Market cap analysis
    - Performance monitoring
    """
    
    def __init__(self, db_manager: Optional[SQLiteManager] = None, cache_ttl: int = 1800):
        """
        Initialize company info repository.
        
        Args:
            db_manager: MongoDB manager instance
            cache_ttl: Cache time-to-live in seconds (default: 30 minutes for company info)
        """
        super().__init__(db_manager, cache_ttl)
        self.collection_name = self.db_manager.COMPANY_INFO_COLLECTION
    
    def get_collection_name(self) -> str:
        """Get the collection name for this repository."""
        return self.collection_name
    
    @with_performance_monitoring("save_company_info")
    def save_company_info(self, data: List[CompanyInfo]) -> None:
        """
        Save company information to the database using upsert operations.
        
        Args:
            data: List of CompanyInfo instances to save
            
        Raises:
            ValueError: If data validation fails
        """
        if not data:
            logger.warning("No company info provided to save")
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
            logger.warning(f"Found {len(invalid_data)} invalid company info records")
            for item in invalid_data:
                logger.debug(f"Invalid data: {item.symbol}")
        
        if not valid_data:
            raise ValueError("No valid company info to save")
        
        # Use upsert to handle duplicates gracefully
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            operations = []
            for item in valid_data:
                doc = item.to_dict()
                # Convert datetime objects for MongoDB
                doc["created_at"] = item.created_at
                doc["updated_at"] = item.updated_at
                
                operations.append({
                    "replaceOne": {
                        "filter": {"symbol": item.symbol},
                        "replacement": doc,
                        "upsert": True
                    }
                })
            
            if operations:
                # Use SQLite bulk operations for efficiency
                for op in operations:
                    filter_data = op["replaceOne"]["filter"]
                    replacement_data = op["replaceOne"]["replacement"]
                    
                    # Use upsert operation for SQLite
                    self.db_manager.upsert_company_info([
                        CompanyInfo(**replacement_data)
                    ])
                
                # Clear cache for affected symbols
                symbols = {item.symbol for item in valid_data}
                for symbol in symbols:
                    self._clear_cache(symbol)
                
                logger.info(f"Saved {len(valid_data)} company info records")
                
        except Exception as e:
            logger.error(f"Failed to save company info: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_company_info")
    def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """
        Retrieve company information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[CompanyInfo]: Company information or None if not found
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            doc = collection.find_one({"symbol": symbol})
            
            if doc:
                # Remove MongoDB _id field and SQLite id field
                doc.pop("_id", None)
                doc.pop("id", None)
                return CompanyInfo.from_dict(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company info for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_companies_by_sector")
    def get_companies_by_sector(self, sector: str) -> List[CompanyInfo]:
        """
        Get all companies in a specific sector.
        
        Args:
            sector: Business sector name
            
        Returns:
            List[CompanyInfo]: List of companies in the sector
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            cursor = collection.find({"sector": sector}).sort("symbol", 1)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                company_info = CompanyInfo.from_dict(doc)
                results.append(company_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get companies by sector {sector}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_companies_by_industry")
    def get_companies_by_industry(self, industry: str) -> List[CompanyInfo]:
        """
        Get all companies in a specific industry.
        
        Args:
            industry: Industry classification
            
        Returns:
            List[CompanyInfo]: List of companies in the industry
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            cursor = collection.find({"industry": industry}).sort("symbol", 1)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                company_info = CompanyInfo.from_dict(doc)
                results.append(company_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get companies by industry {industry}: {e}")
            raise
    
    @with_performance_monitoring("get_all_sectors")
    def get_all_sectors(self) -> List[str]:
        """
        Get all unique sectors in the database.
        
        Returns:
            List[str]: List of unique sectors
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            sectors = collection.distinct("sector")
            # Filter out None values and sort
            sectors = [s for s in sectors if s is not None]
            return sorted(sectors)
        except Exception as e:
            logger.error(f"Failed to get sectors: {e}")
            raise
    
    @with_performance_monitoring("get_all_industries")
    def get_all_industries(self) -> List[str]:
        """
        Get all unique industries in the database.
        
        Returns:
            List[str]: List of unique industries
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            industries = collection.distinct("industry")
            # Filter out None values and sort
            industries = [i for i in industries if i is not None]
            return sorted(industries)
        except Exception as e:
            logger.error(f"Failed to get industries: {e}")
            raise
    
    @with_performance_monitoring("get_all_symbols")
    def get_all_symbols(self) -> List[str]:
        """
        Get all symbols in the database.
        
        Returns:
            List[str]: List of all stock symbols
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
    @with_performance_monitoring("get_companies_by_market_cap")
    def get_companies_by_market_cap(
        self,
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[CompanyInfo]:
        """
        Get companies filtered by market capitalization range.
        
        Args:
            min_market_cap: Minimum market cap (optional)
            max_market_cap: Maximum market cap (optional)
            limit: Maximum number of results (optional)
            
        Returns:
            List[CompanyInfo]: List of companies matching criteria
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            query = {"market_cap": {"$ne": None}}
            
            if min_market_cap is not None:
                query["market_cap"]["$gte"] = min_market_cap
            
            if max_market_cap is not None:
                query["market_cap"]["$lte"] = max_market_cap
            
            cursor = collection.find(query).sort("market_cap", -1)  # Largest first
            
            if limit:
                cursor = cursor.limit(limit)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                company_info = CompanyInfo.from_dict(doc)
                results.append(company_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get companies by market cap: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("search_companies")
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
            search_fields: Fields to search in (default: ['symbol', 'company_name'])
            limit: Maximum number of results (optional)
            
        Returns:
            List[CompanyInfo]: List of companies matching the search
        """
        if search_fields is None:
            search_fields = ['symbol', 'company_name']
        
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Create regex pattern for case-insensitive search
            regex_pattern = {"$regex": query, "$options": "i"}
            
            # Build OR query for multiple fields
            or_conditions = []
            for field in search_fields:
                or_conditions.append({field: regex_pattern})
            
            mongo_query = {"$or": or_conditions}
            
            cursor = collection.find(mongo_query).sort("symbol", 1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                company_info = CompanyInfo.from_dict(doc)
                results.append(company_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search companies with query '{query}': {e}")
            raise
    
    @with_performance_monitoring("update_company_info")
    def update_company_info(self, symbol: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields of company information.
        
        Args:
            symbol: Stock symbol
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if document was updated, False if not found
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now()
            
            result = collection.update_one(
                {"symbol": symbol},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                # Clear cache for this symbol
                self._clear_cache(symbol)
                logger.debug(f"Updated company info for {symbol}")
                return True
            else:
                logger.debug(f"No company info found to update for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update company info for {symbol}: {e}")
            raise
    
    @with_performance_monitoring("delete_company_info")
    def delete_company_info(self, symbol: str) -> bool:
        """
        Delete company information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            bool: True if document was deleted, False if not found
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            result = collection.delete_one({"symbol": symbol})
            
            if result.deleted_count > 0:
                # Clear cache for this symbol
                self._clear_cache(symbol)
                logger.info(f"Deleted company info for {symbol}")
                return True
            else:
                logger.debug(f"No company info found to delete for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete company info for {symbol}: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_sector_summary")
    def get_sector_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics for each sector.
        
        Returns:
            Dict[str, Dict[str, Any]]: Sector statistics including company count, avg market cap, etc.
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Use aggregation pipeline for efficient calculation
            pipeline = [
                {"$match": {"sector": {"$ne": None}}},
                {"$group": {
                    "_id": "$sector",
                    "company_count": {"$sum": 1},
                    "avg_market_cap": {"$avg": "$market_cap"},
                    "total_market_cap": {"$sum": "$market_cap"},
                    "max_market_cap": {"$max": "$market_cap"},
                    "min_market_cap": {"$min": "$market_cap"}
                }},
                {"$sort": {"company_count": -1}}
            ]
            
            results = {}
            for doc in collection.aggregate(pipeline):
                sector = doc["_id"]
                results[sector] = {
                    "company_count": doc["company_count"],
                    "avg_market_cap": doc["avg_market_cap"],
                    "total_market_cap": doc["total_market_cap"],
                    "max_market_cap": doc["max_market_cap"],
                    "min_market_cap": doc["min_market_cap"]
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get sector summary: {e}")
            raise
    
    @with_caching()
    @with_performance_monitoring("get_industry_summary")
    def get_industry_summary(self, sector: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics for each industry, optionally filtered by sector.
        
        Args:
            sector: Optional sector filter
            
        Returns:
            Dict[str, Dict[str, Any]]: Industry statistics
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            # Build match stage
            match_stage = {"industry": {"$ne": None}}
            if sector:
                match_stage["sector"] = sector
            
            pipeline = [
                {"$match": match_stage},
                {"$group": {
                    "_id": "$industry",
                    "company_count": {"$sum": 1},
                    "avg_market_cap": {"$avg": "$market_cap"},
                    "total_market_cap": {"$sum": "$market_cap"},
                    "sectors": {"$addToSet": "$sector"}
                }},
                {"$sort": {"company_count": -1}}
            ]
            
            results = {}
            for doc in collection.aggregate(pipeline):
                industry = doc["_id"]
                results[industry] = {
                    "company_count": doc["company_count"],
                    "avg_market_cap": doc["avg_market_cap"],
                    "total_market_cap": doc["total_market_cap"],
                    "sectors": doc["sectors"]
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get industry summary: {e}")
            raise
    
    @with_performance_monitoring("bulk_get_company_info")
    def bulk_get_company_info(self, symbols: List[str]) -> Dict[str, Optional[CompanyInfo]]:
        """
        Get company information for multiple symbols efficiently.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict[str, Optional[CompanyInfo]]: Mapping of symbol to company info
        """
        self.ensure_connection()
        collection = self.db_manager.get_collection(self.collection_name)
        
        try:
            cursor = collection.find({"symbol": {"$in": symbols}})
            
            results = {}
            for doc in cursor:
                doc.pop("_id", None)
                company_info = CompanyInfo.from_dict(doc)
                results[company_info.symbol] = company_info
            
            # Ensure all symbols are in the result (with None for missing ones)
            for symbol in symbols:
                if symbol not in results:
                    results[symbol] = None
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to bulk get company info: {e}")
            raise
    
    def clear_symbol_cache(self, symbol: str) -> None:
        """
        Clear cache entries for a specific symbol.
        
        Args:
            symbol: Stock symbol to clear cache for
        """
        self._clear_cache(symbol)
        logger.debug(f"Cleared company info cache for symbol: {symbol}")