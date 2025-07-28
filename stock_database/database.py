"""
MongoDB database manager for stock data storage and retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pymongo
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (ConnectionFailure, DuplicateKeyError,
                            OperationFailure, ServerSelectionTimeoutError)

from .config import get_config_manager
from .models.financial_data import FinancialData
from .models.stock_data import StockData

logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    MongoDB connection and database management for stock data.
    
    Handles connection management, index creation, and basic CRUD operations
    for stock data, financial data, and company information collections.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize MongoDB manager.
        
        Args:
            config_manager: Configuration manager instance. If None, uses global instance.
        """
        self.config = config_manager or get_config_manager()
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._connected = False
        
        # Collection names
        self.STOCK_DATA_COLLECTION = "stock_data"
        self.FINANCIAL_DATA_COLLECTION = "financial_data"
        self.COMPANY_INFO_COLLECTION = "company_info"
    
    def connect(self) -> None:
        """
        Establish connection to MongoDB.
        
        Raises:
            ConnectionFailure: If connection cannot be established
        """
        try:
            db_config = self.config.get_database_config().get("mongodb", {})
            database_name = db_config.get("database", "stock_data")
            
            # Connection options
            connection_timeout = db_config.get("connection_timeout", 30) * 1000  # Convert to ms
            max_pool_size = db_config.get("max_pool_size", 100)
            
            # Check if using MongoDB Atlas
            if db_config.get("is_atlas", False):
                # MongoDB Atlas connection
                connection_string = db_config.get("connection_string", "")
                username = db_config.get("username", "")
                password = db_config.get("password", "")
                
                if not connection_string or not username or not password:
                    raise ValueError("MongoDB Atlas requires connection_string, username, and password")
                
                # Build Atlas URI with credentials and database
                if connection_string.endswith('/'):
                    uri = f"mongodb+srv://{username}:{password}@{connection_string[14:]}{database_name}?retryWrites=true&w=majority"
                else:
                    uri = f"mongodb+srv://{username}:{password}@{connection_string[14:]}/{database_name}?retryWrites=true&w=majority"
                
                logger.info(f"Connecting to MongoDB Atlas: {connection_string}")
                
            else:
                # Local MongoDB connection
                host = db_config.get("host", "localhost")
                port = db_config.get("port", 27017)
                username = db_config.get("username", "")
                password = db_config.get("password", "")
                
                # Build local connection URI
                if username and password:
                    uri = f"mongodb://{username}:{password}@{host}:{port}/{database_name}"
                else:
                    uri = f"mongodb://{host}:{port}/{database_name}"
                
                logger.info(f"Connecting to local MongoDB: {host}:{port}")
            
            # Create client with options
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=connection_timeout,
                maxPoolSize=max_pool_size,
                retryWrites=True,
                retryReads=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[database_name]
            self._connected = True
            
            if db_config.get("is_atlas", False):
                logger.info(f"Successfully connected to MongoDB Atlas, database: {database_name}")
            else:
                host = db_config.get("host", "localhost")
                port = db_config.get("port", 27017)
                logger.info(f"Successfully connected to MongoDB at {host}:{port}, database: {database_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            raise ConnectionFailure(f"Cannot connect to MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self._connected = False
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    def is_connected(self) -> bool:
        """
        Check if connected to MongoDB.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self._connected or not self.client:
            return False
        
        try:
            # Test connection with a simple command
            self.client.admin.command('ping')
            return True
        except Exception:
            self._connected = False
            return False
    
    def ensure_connection(self) -> None:
        """Ensure connection is established, reconnect if necessary."""
        if not self.is_connected():
            logger.info("Reconnecting to MongoDB...")
            self.connect()
    
    def create_indexes(self) -> None:
        """
        Create indexes for all collections to optimize query performance.
        
        Raises:
            OperationFailure: If index creation fails
        """
        self.ensure_connection()
        
        try:
            # Stock data collection indexes
            stock_collection = self.database[self.STOCK_DATA_COLLECTION]
            
            # Unique compound index on symbol and date
            stock_collection.create_index(
                [("symbol", ASCENDING), ("date", ASCENDING)],
                unique=True,
                name="symbol_date_unique"
            )
            
            # Index for date-based queries (descending for recent data first)
            stock_collection.create_index(
                [("symbol", ASCENDING), ("date", DESCENDING)],
                name="symbol_date_desc"
            )
            
            # Index for date range queries
            stock_collection.create_index(
                [("date", DESCENDING)],
                name="date_desc"
            )
            
            logger.info("Created indexes for stock_data collection")
            
            # Financial data collection indexes
            financial_collection = self.database[self.FINANCIAL_DATA_COLLECTION]
            
            # Unique compound index on symbol, fiscal_year, and fiscal_quarter
            financial_collection.create_index(
                [("symbol", ASCENDING), ("fiscal_year", ASCENDING), ("fiscal_quarter", ASCENDING)],
                unique=True,
                name="symbol_fiscal_unique"
            )
            
            # Index for fiscal year queries (descending for recent data first)
            financial_collection.create_index(
                [("symbol", ASCENDING), ("fiscal_year", DESCENDING)],
                name="symbol_fiscal_year_desc"
            )
            
            logger.info("Created indexes for financial_data collection")
            
            # Company info collection indexes
            company_collection = self.database[self.COMPANY_INFO_COLLECTION]
            
            # Unique index on symbol
            company_collection.create_index(
                [("symbol", ASCENDING)],
                unique=True,
                name="symbol_unique"
            )
            
            # Index for sector-based queries
            company_collection.create_index(
                [("sector", ASCENDING)],
                name="sector_index"
            )
            
            # Index for industry-based queries
            company_collection.create_index(
                [("industry", ASCENDING)],
                name="industry_index"
            )
            
            logger.info("Created indexes for company_info collection")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating indexes: {e}")
            raise
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection: MongoDB collection object
            
        Raises:
            ConnectionFailure: If not connected to database
        """
        self.ensure_connection()
        
        if self.database is None:
            raise ConnectionFailure("Not connected to database")
        
        return self.database[collection_name]
    
    # Stock Data Operations
    
    def insert_stock_data(self, data: Union[StockData, List[StockData]]) -> None:
        """
        Insert stock data into the database.
        
        Args:
            data: Single StockData instance or list of StockData instances
            
        Raises:
            OperationFailure: If insertion fails
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            if isinstance(data, StockData):
                # Single document
                doc = self._stock_data_to_doc(data)
                collection.insert_one(doc)
                logger.debug(f"Inserted stock data for {data.symbol} on {data.date}")
            else:
                # Multiple documents
                docs = [self._stock_data_to_doc(item) for item in data]
                if docs:
                    collection.insert_many(docs, ordered=False)
                    logger.info(f"Inserted {len(docs)} stock data records")
                    
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate stock data detected: {e}")
            # Continue execution for batch operations
        except OperationFailure as e:
            logger.error(f"Failed to insert stock data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting stock data: {e}")
            raise
    
    def update_stock_data(self, symbol: str, date: datetime, updates: Dict[str, Any]) -> bool:
        """
        Update stock data for a specific symbol and date.
        
        Args:
            symbol: Stock symbol
            date: Trading date
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if document was updated, False if not found
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now()
            
            result = collection.update_one(
                {"symbol": symbol, "date": date},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.debug(f"Updated stock data for {symbol} on {date}")
                return True
            else:
                logger.debug(f"No stock data found to update for {symbol} on {date}")
                return False
                
        except OperationFailure as e:
            logger.error(f"Failed to update stock data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating stock data: {e}")
            raise
    
    def upsert_stock_data(self, data: Union[StockData, List[StockData]]) -> None:
        """
        Insert or update stock data (upsert operation).
        
        Args:
            data: Single StockData instance or list of StockData instances
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            if isinstance(data, StockData):
                # Single document
                doc = self._stock_data_to_doc(data)
                collection.replace_one(
                    {"symbol": data.symbol, "date": data.date},
                    doc,
                    upsert=True
                )
                logger.debug(f"Upserted stock data for {data.symbol} on {data.date}")
            else:
                # Multiple documents - use bulk operations for efficiency
                operations = []
                for item in data:
                    doc = self._stock_data_to_doc(item)
                    operations.append(
                        pymongo.ReplaceOne(
                            {"symbol": item.symbol, "date": item.date},
                            doc,
                            upsert=True
                        )
                    )
                
                if operations:
                    collection.bulk_write(operations, ordered=False)
                    logger.info(f"Upserted {len(operations)} stock data records")
                    
        except OperationFailure as e:
            logger.error(f"Failed to upsert stock data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error upserting stock data: {e}")
            raise
    
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
            start_date: Start date (inclusive). If None, no start limit
            end_date: End date (inclusive). If None, no end limit
            limit: Maximum number of records to return
            
        Returns:
            List[StockData]: List of stock data records
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            # Build query
            query = {"symbol": symbol}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["date"] = date_query
            
            # Execute query with sorting (most recent first)
            cursor = collection.find(query).sort("date", DESCENDING)
            
            if limit:
                cursor = cursor.limit(limit)
            
            # Convert documents to StockData objects
            results = []
            for doc in cursor:
                stock_data = self._doc_to_stock_data(doc)
                results.append(stock_data)
            
            logger.debug(f"Retrieved {len(results)} stock data records for {symbol}")
            return results
            
        except OperationFailure as e:
            logger.error(f"Failed to retrieve stock data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving stock data: {e}")
            raise
    
    def get_latest_stock_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the latest date for which stock data exists for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[datetime]: Latest date or None if no data exists
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            doc = collection.find_one(
                {"symbol": symbol},
                sort=[("date", DESCENDING)]
            )
            
            if doc:
                return doc["date"]
            return None
            
        except OperationFailure as e:
            logger.error(f"Failed to get latest stock date: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting latest stock date: {e}")
            raise
    
    def delete_stock_data(self, symbol: str, date: Optional[datetime] = None) -> int:
        """
        Delete stock data for a symbol.
        
        Args:
            symbol: Stock symbol
            date: Specific date to delete. If None, deletes all data for symbol
            
        Returns:
            int: Number of documents deleted
        """
        self.ensure_connection()
        collection = self.get_collection(self.STOCK_DATA_COLLECTION)
        
        try:
            query = {"symbol": symbol}
            if date:
                query["date"] = date
            
            result = collection.delete_many(query)
            
            logger.info(f"Deleted {result.deleted_count} stock data records for {symbol}")
            return result.deleted_count
            
        except OperationFailure as e:
            logger.error(f"Failed to delete stock data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting stock data: {e}")
            raise
    
    # Financial Data Operations
    
    def insert_financial_data(self, data: Union[FinancialData, List[FinancialData]]) -> None:
        """
        Insert financial data into the database.
        
        Args:
            data: Single FinancialData instance or list of FinancialData instances
        """
        self.ensure_connection()
        collection = self.get_collection(self.FINANCIAL_DATA_COLLECTION)
        
        try:
            if isinstance(data, FinancialData):
                # Single document
                doc = self._financial_data_to_doc(data)
                collection.insert_one(doc)
                logger.debug(f"Inserted financial data for {data.symbol} FY{data.fiscal_year}")
            else:
                # Multiple documents
                docs = [self._financial_data_to_doc(item) for item in data]
                if docs:
                    collection.insert_many(docs, ordered=False)
                    logger.info(f"Inserted {len(docs)} financial data records")
                    
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate financial data detected: {e}")
        except OperationFailure as e:
            logger.error(f"Failed to insert financial data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting financial data: {e}")
            raise
    
    def upsert_financial_data(self, data: Union[FinancialData, List[FinancialData]]) -> None:
        """
        Insert or update financial data (upsert operation).
        
        Args:
            data: Single FinancialData instance or list of FinancialData instances
        """
        self.ensure_connection()
        collection = self.get_collection(self.FINANCIAL_DATA_COLLECTION)
        
        try:
            if isinstance(data, FinancialData):
                # Single document
                doc = self._financial_data_to_doc(data)
                collection.replace_one(
                    {
                        "symbol": data.symbol,
                        "fiscal_year": data.fiscal_year,
                        "fiscal_quarter": data.fiscal_quarter
                    },
                    doc,
                    upsert=True
                )
                logger.debug(f"Upserted financial data for {data.symbol} FY{data.fiscal_year}")
            else:
                # Multiple documents
                operations = []
                for item in data:
                    doc = self._financial_data_to_doc(item)
                    operations.append(
                        pymongo.ReplaceOne(
                            {
                                "symbol": item.symbol,
                                "fiscal_year": item.fiscal_year,
                                "fiscal_quarter": item.fiscal_quarter
                            },
                            doc,
                            upsert=True
                        )
                    )
                
                if operations:
                    collection.bulk_write(operations, ordered=False)
                    logger.info(f"Upserted {len(operations)} financial data records")
                    
        except OperationFailure as e:
            logger.error(f"Failed to upsert financial data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error upserting financial data: {e}")
            raise
    
    def get_financial_data(
        self,
        symbol: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None
    ) -> List[FinancialData]:
        """
        Retrieve financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            fiscal_year: Specific fiscal year. If None, returns all years
            fiscal_quarter: Specific fiscal quarter. If None, returns all quarters
            
        Returns:
            List[FinancialData]: List of financial data records
        """
        self.ensure_connection()
        collection = self.get_collection(self.FINANCIAL_DATA_COLLECTION)
        
        try:
            # Build query
            query = {"symbol": symbol}
            
            if fiscal_year is not None:
                query["fiscal_year"] = fiscal_year
            
            if fiscal_quarter is not None:
                query["fiscal_quarter"] = fiscal_quarter
            
            # Execute query with sorting (most recent first)
            cursor = collection.find(query).sort([
                ("fiscal_year", DESCENDING),
                ("fiscal_quarter", DESCENDING)
            ])
            
            # Convert documents to FinancialData objects
            results = []
            for doc in cursor:
                financial_data = self._doc_to_financial_data(doc)
                results.append(financial_data)
            
            logger.debug(f"Retrieved {len(results)} financial data records for {symbol}")
            return results
            
        except OperationFailure as e:
            logger.error(f"Failed to retrieve financial data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving financial data: {e}")
            raise
    
    # Helper methods for document conversion
    
    def _stock_data_to_doc(self, stock_data: StockData) -> Dict[str, Any]:
        """Convert StockData to MongoDB document."""
        doc = stock_data.to_dict()
        # Convert date strings back to datetime for MongoDB
        doc["date"] = stock_data.date
        doc["created_at"] = stock_data.created_at
        doc["updated_at"] = stock_data.updated_at
        return doc
    
    def _doc_to_stock_data(self, doc: Dict[str, Any]) -> StockData:
        """Convert MongoDB document to StockData."""
        # Remove MongoDB _id field
        doc.pop("_id", None)
        return StockData(**doc)
    
    def _financial_data_to_doc(self, financial_data: FinancialData) -> Dict[str, Any]:
        """Convert FinancialData to MongoDB document."""
        doc = financial_data.to_dict()
        # Convert date strings back to datetime for MongoDB
        doc["created_at"] = financial_data.created_at
        doc["updated_at"] = financial_data.updated_at
        return doc
    
    def _doc_to_financial_data(self, doc: Dict[str, Any]) -> FinancialData:
        """Convert MongoDB document to FinancialData."""
        # Remove MongoDB _id field
        doc.pop("_id", None)
        return FinancialData(**doc)
    
    # Database management operations
    
    def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection from the database.
        
        Args:
            collection_name: Name of the collection to drop
        """
        self.ensure_connection()
        
        try:
            self.database[collection_name].drop()
            logger.info(f"Dropped collection: {collection_name}")
        except OperationFailure as e:
            logger.error(f"Failed to drop collection {collection_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error dropping collection {collection_name}: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict[str, Any]: Collection statistics
        """
        self.ensure_connection()
        
        try:
            stats = self.database.command("collStats", collection_name)
            return {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avgObjSize": stats.get("avgObjSize", 0),
                "storageSize": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0),
                "totalIndexSize": stats.get("totalIndexSize", 0)
            }
        except OperationFailure as e:
            logger.error(f"Failed to get collection stats for {collection_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting collection stats for {collection_name}: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dict[str, Any]: Database information
        """
        self.ensure_connection()
        
        try:
            # Get database stats
            db_stats = self.database.command("dbStats")
            
            # Get collection names
            collections = self.database.list_collection_names()
            
            # Get collection stats for each collection
            collection_stats = {}
            for collection_name in collections:
                try:
                    collection_stats[collection_name] = self.get_collection_stats(collection_name)
                except Exception as e:
                    logger.warning(f"Could not get stats for collection {collection_name}: {e}")
                    collection_stats[collection_name] = {"error": str(e)}
            
            return {
                "database_name": self.database.name,
                "collections": collections,
                "collection_count": len(collections),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
                "index_size": db_stats.get("indexSize", 0),
                "collection_stats": collection_stats
            }
            
        except OperationFailure as e:
            logger.error(f"Failed to get database info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting database info: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()