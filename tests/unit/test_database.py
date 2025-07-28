"""
Unit tests for MongoDB database manager.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from pymongo.errors import (ConnectionFailure, DuplicateKeyError,
                            OperationFailure)

from stock_database.database import MongoDBManager
from stock_database.models.financial_data import FinancialData
from stock_database.models.stock_data import StockData


class TestMongoDBManager:
    """Test cases for MongoDBManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration manager."""
        config = Mock()
        config.get_database_config.return_value = {
            "mongodb": {
                "host": "localhost",
                "port": 27017,
                "database": "test_stock_data",
                "username": "",
                "password": "",
                "connection_timeout": 30,
                "max_pool_size": 100
            }
        }
        return config
    
    @pytest.fixture
    def db_manager(self, mock_config):
        """Create MongoDBManager instance with mock config."""
        return MongoDBManager(config_manager=mock_config)
    
    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data for testing."""
        return StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 15),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
    
    @pytest.fixture
    def sample_financial_data(self):
        """Create sample financial data for testing."""
        return FinancialData(
            symbol="AAPL",
            fiscal_year=2024,
            fiscal_quarter=1,
            revenue=100000000000,
            net_income=25000000000,
            eps=6.15,
            per=25.0,
            pbr=3.5,
            roe=0.167
        )
    
    def test_init(self, mock_config):
        """Test MongoDBManager initialization."""
        manager = MongoDBManager(config_manager=mock_config)
        
        assert manager.config == mock_config
        assert manager.client is None
        assert manager.database is None
        assert not manager._connected
        assert manager.STOCK_DATA_COLLECTION == "stock_data"
        assert manager.FINANCIAL_DATA_COLLECTION == "financial_data"
        assert manager.COMPANY_INFO_COLLECTION == "company_info"
    
    @patch('stock_database.database.MongoClient')
    def test_connect_success(self, mock_mongo_client, db_manager):
        """Test successful MongoDB connection."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_database = MagicMock()
        mock_client.__getitem__.return_value = mock_database
        mock_mongo_client.return_value = mock_client
        
        # Test connection
        db_manager.connect()
        
        # Verify connection was established
        assert db_manager.client == mock_client
        assert db_manager.database == mock_database
        assert db_manager._connected is True
        
        # Verify client was created with correct parameters
        mock_mongo_client.assert_called_once()
        call_args = mock_mongo_client.call_args
        assert "mongodb://localhost:27017/test_stock_data" in call_args[0][0]
        assert call_args[1]["serverSelectionTimeoutMS"] == 30000
        assert call_args[1]["maxPoolSize"] == 100
        assert call_args[1]["retryWrites"] is True
        assert call_args[1]["retryReads"] is True
    
    @patch('stock_database.database.MongoClient')
    def test_connect_failure(self, mock_mongo_client, db_manager):
        """Test MongoDB connection failure."""
        # Setup mock to raise ConnectionFailure
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        # Test connection failure
        with pytest.raises(ConnectionFailure):
            db_manager.connect()
        
        # Verify connection state
        assert not db_manager._connected
    
    def test_disconnect(self, db_manager):
        """Test MongoDB disconnection."""
        # Setup mock client
        mock_client = Mock()
        db_manager.client = mock_client
        db_manager._connected = True
        
        # Test disconnection
        db_manager.disconnect()
        
        # Verify disconnection
        mock_client.close.assert_called_once()
        assert not db_manager._connected
    
    def test_is_connected_true(self, db_manager):
        """Test is_connected when connected."""
        # Setup mock client
        mock_client = Mock()
        mock_client.admin.command.return_value = {"ok": 1}
        db_manager.client = mock_client
        db_manager._connected = True
        
        # Test connection check
        assert db_manager.is_connected() is True
        mock_client.admin.command.assert_called_with('ping')
    
    def test_is_connected_false(self, db_manager):
        """Test is_connected when not connected."""
        # Test when not connected
        assert db_manager.is_connected() is False
        
        # Test when client exists but ping fails
        mock_client = Mock()
        mock_client.admin.command.side_effect = Exception("Ping failed")
        db_manager.client = mock_client
        db_manager._connected = True
        
        assert db_manager.is_connected() is False
        assert not db_manager._connected
    
    @patch.object(MongoDBManager, 'connect')
    def test_ensure_connection_reconnects(self, mock_connect, db_manager):
        """Test ensure_connection reconnects when not connected."""
        # Setup not connected state
        db_manager._connected = False
        
        # Test ensure connection
        db_manager.ensure_connection()
        
        # Verify reconnection attempt
        mock_connect.assert_called_once()
    
    @patch.object(MongoDBManager, 'ensure_connection')
    def test_create_indexes(self, mock_ensure_connection, db_manager):
        """Test index creation."""
        # Setup mock database and collections
        mock_stock_collection = Mock()
        mock_financial_collection = Mock()
        mock_company_collection = Mock()
        
        mock_database = MagicMock()
        mock_database.__getitem__.side_effect = lambda name: {
            "stock_data": mock_stock_collection,
            "financial_data": mock_financial_collection,
            "company_info": mock_company_collection
        }[name]
        
        db_manager.database = mock_database
        
        # Test index creation
        db_manager.create_indexes()
        
        # Verify stock data indexes
        assert mock_stock_collection.create_index.call_count == 3
        
        # Verify financial data indexes
        assert mock_financial_collection.create_index.call_count == 2
        
        # Verify company info indexes
        assert mock_company_collection.create_index.call_count == 3
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_insert_stock_data_single(self, mock_get_collection, mock_ensure_connection, 
                                    db_manager, sample_stock_data):
        """Test inserting single stock data record."""
        # Setup mock collection
        mock_collection = Mock()
        mock_get_collection.return_value = mock_collection
        
        # Test insertion
        db_manager.insert_stock_data(sample_stock_data)
        
        # Verify insertion
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["symbol"] == "AAPL"
        assert call_args["date"] == datetime(2024, 1, 15)
        assert call_args["close"] == 154.0
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_insert_stock_data_multiple(self, mock_get_collection, mock_ensure_connection, 
                                      db_manager, sample_stock_data):
        """Test inserting multiple stock data records."""
        # Setup mock collection
        mock_collection = Mock()
        mock_get_collection.return_value = mock_collection
        
        # Create multiple stock data records
        stock_data_list = [sample_stock_data, sample_stock_data]
        
        # Test insertion
        db_manager.insert_stock_data(stock_data_list)
        
        # Verify insertion
        mock_collection.insert_many.assert_called_once()
        call_args = mock_collection.insert_many.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["symbol"] == "AAPL"
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_insert_stock_data_duplicate_key_error(self, mock_get_collection, 
                                                  mock_ensure_connection, db_manager, 
                                                  sample_stock_data):
        """Test handling duplicate key error during insertion."""
        # Setup mock collection to raise DuplicateKeyError
        mock_collection = Mock()
        mock_collection.insert_one.side_effect = DuplicateKeyError("Duplicate key")
        mock_get_collection.return_value = mock_collection
        
        # Test insertion (should not raise exception)
        db_manager.insert_stock_data(sample_stock_data)
        
        # Verify insertion was attempted
        mock_collection.insert_one.assert_called_once()
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_update_stock_data(self, mock_get_collection, mock_ensure_connection, db_manager):
        """Test updating stock data."""
        # Setup mock collection
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collection = Mock()
        mock_collection.update_one.return_value = mock_result
        mock_get_collection.return_value = mock_collection
        
        # Test update
        symbol = "AAPL"
        date = datetime(2024, 1, 15)
        updates = {"close": 155.0}
        
        result = db_manager.update_stock_data(symbol, date, updates)
        
        # Verify update
        assert result is True
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"symbol": symbol, "date": date}
        assert "close" in call_args[0][1]["$set"]
        assert "updated_at" in call_args[0][1]["$set"]
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_upsert_stock_data_single(self, mock_get_collection, mock_ensure_connection, 
                                    db_manager, sample_stock_data):
        """Test upserting single stock data record."""
        # Setup mock collection
        mock_collection = Mock()
        mock_get_collection.return_value = mock_collection
        
        # Test upsert
        db_manager.upsert_stock_data(sample_stock_data)
        
        # Verify upsert
        mock_collection.replace_one.assert_called_once()
        call_args = mock_collection.replace_one.call_args
        assert call_args[0][0] == {"symbol": "AAPL", "date": datetime(2024, 1, 15)}
        assert call_args[1]["upsert"] is True
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_get_stock_data(self, mock_get_collection, mock_ensure_connection, db_manager):
        """Test retrieving stock data."""
        # Setup mock collection and cursor
        mock_doc = {
            "symbol": "AAPL",
            "date": datetime(2024, 1, 15),
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "volume": 1000000,
            "adjusted_close": 154.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = [mock_doc]
        mock_cursor.sort.return_value = mock_cursor
        
        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mock_get_collection.return_value = mock_collection
        
        # Test retrieval
        symbol = "AAPL"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        results = db_manager.get_stock_data(symbol, start_date, end_date)
        
        # Verify retrieval
        assert len(results) == 1
        assert isinstance(results[0], StockData)
        assert results[0].symbol == "AAPL"
        assert results[0].close == 154.0
        
        # Verify query parameters
        mock_collection.find.assert_called_once()
        query = mock_collection.find.call_args[0][0]
        assert query["symbol"] == symbol
        assert "$gte" in query["date"]
        assert "$lte" in query["date"]
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_get_latest_stock_date(self, mock_get_collection, mock_ensure_connection, db_manager):
        """Test getting latest stock date."""
        # Setup mock collection
        latest_date = datetime(2024, 1, 15)
        mock_doc = {"date": latest_date}
        mock_collection = Mock()
        mock_collection.find_one.return_value = mock_doc
        mock_get_collection.return_value = mock_collection
        
        # Test retrieval
        result = db_manager.get_latest_stock_date("AAPL")
        
        # Verify result
        assert result == latest_date
        mock_collection.find_one.assert_called_once()
        call_args = mock_collection.find_one.call_args
        assert call_args[0][0] == {"symbol": "AAPL"}
        assert call_args[1]["sort"] == [("date", -1)]
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_delete_stock_data(self, mock_get_collection, mock_ensure_connection, db_manager):
        """Test deleting stock data."""
        # Setup mock collection
        mock_result = Mock()
        mock_result.deleted_count = 5
        mock_collection = Mock()
        mock_collection.delete_many.return_value = mock_result
        mock_get_collection.return_value = mock_collection
        
        # Test deletion
        result = db_manager.delete_stock_data("AAPL")
        
        # Verify deletion
        assert result == 5
        mock_collection.delete_many.assert_called_once()
        call_args = mock_collection.delete_many.call_args[0][0]
        assert call_args == {"symbol": "AAPL"}
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_insert_financial_data(self, mock_get_collection, mock_ensure_connection, 
                                 db_manager, sample_financial_data):
        """Test inserting financial data."""
        # Setup mock collection
        mock_collection = Mock()
        mock_get_collection.return_value = mock_collection
        
        # Test insertion
        db_manager.insert_financial_data(sample_financial_data)
        
        # Verify insertion
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["symbol"] == "AAPL"
        assert call_args["fiscal_year"] == 2024
        assert call_args["eps"] == 6.15
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_upsert_financial_data(self, mock_get_collection, mock_ensure_connection, 
                                 db_manager, sample_financial_data):
        """Test upserting financial data."""
        # Setup mock collection
        mock_collection = Mock()
        mock_get_collection.return_value = mock_collection
        
        # Test upsert
        db_manager.upsert_financial_data(sample_financial_data)
        
        # Verify upsert
        mock_collection.replace_one.assert_called_once()
        call_args = mock_collection.replace_one.call_args
        expected_filter = {
            "symbol": "AAPL",
            "fiscal_year": 2024,
            "fiscal_quarter": 1
        }
        assert call_args[0][0] == expected_filter
        assert call_args[1]["upsert"] is True
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection')
    def test_get_financial_data(self, mock_get_collection, mock_ensure_connection, db_manager):
        """Test retrieving financial data."""
        # Setup mock collection and cursor
        mock_doc = {
            "symbol": "AAPL",
            "fiscal_year": 2024,
            "fiscal_quarter": 1,
            "revenue": 100000000000,
            "net_income": 25000000000,
            "eps": 6.15,
            "per": 25.0,
            "pbr": 3.5,
            "roe": 0.167,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = [mock_doc]
        mock_cursor.sort.return_value = mock_cursor
        
        mock_collection = Mock()
        mock_collection.find.return_value = mock_cursor
        mock_get_collection.return_value = mock_collection
        
        # Test retrieval
        results = db_manager.get_financial_data("AAPL", 2024, 1)
        
        # Verify retrieval
        assert len(results) == 1
        assert isinstance(results[0], FinancialData)
        assert results[0].symbol == "AAPL"
        assert results[0].eps == 6.15
        
        # Verify query parameters
        mock_collection.find.assert_called_once()
        query = mock_collection.find.call_args[0][0]
        assert query["symbol"] == "AAPL"
        assert query["fiscal_year"] == 2024
        assert query["fiscal_quarter"] == 1
    
    @patch.object(MongoDBManager, 'ensure_connection')
    def test_get_collection(self, mock_ensure_connection, db_manager):
        """Test getting a collection."""
        # Setup mock database
        mock_collection = Mock()
        mock_database = MagicMock()
        mock_database.__getitem__.return_value = mock_collection
        db_manager.database = mock_database
        
        # Test getting collection
        result = db_manager.get_collection("test_collection")
        
        # Verify result
        assert result == mock_collection
        mock_database.__getitem__.assert_called_once_with("test_collection")
    
    def test_get_collection_not_connected(self, db_manager):
        """Test getting collection when not connected."""
        # Test without connection
        with pytest.raises(ConnectionFailure):
            db_manager.get_collection("test_collection")
    
    @patch.object(MongoDBManager, 'ensure_connection')
    def test_drop_collection(self, mock_ensure_connection, db_manager):
        """Test dropping a collection."""
        # Setup mock database
        mock_collection = Mock()
        mock_database = MagicMock()
        mock_database.__getitem__.return_value = mock_collection
        db_manager.database = mock_database
        
        # Test dropping collection
        db_manager.drop_collection("test_collection")
        
        # Verify drop was called
        mock_collection.drop.assert_called_once()
    
    @patch.object(MongoDBManager, 'ensure_connection')
    def test_get_collection_stats(self, mock_ensure_connection, db_manager):
        """Test getting collection statistics."""
        # Setup mock database
        mock_stats = {
            "count": 1000,
            "size": 50000,
            "avgObjSize": 50,
            "storageSize": 60000,
            "nindexes": 3,
            "totalIndexSize": 10000
        }
        mock_database = Mock()
        mock_database.command.return_value = mock_stats
        db_manager.database = mock_database
        
        # Test getting stats
        result = db_manager.get_collection_stats("test_collection")
        
        # Verify result
        assert result["count"] == 1000
        assert result["size"] == 50000
        assert result["indexes"] == 3
        mock_database.command.assert_called_once_with("collStats", "test_collection")
    
    @patch.object(MongoDBManager, 'ensure_connection')
    @patch.object(MongoDBManager, 'get_collection_stats')
    def test_get_database_info(self, mock_get_collection_stats, mock_ensure_connection, db_manager):
        """Test getting database information."""
        # Setup mock database
        mock_db_stats = {
            "dataSize": 1000000,
            "storageSize": 1200000,
            "indexSize": 100000
        }
        mock_database = Mock()
        mock_database.command.return_value = mock_db_stats
        mock_database.list_collection_names.return_value = ["stock_data", "financial_data"]
        mock_database.name = "test_stock_data"
        db_manager.database = mock_database
        
        mock_get_collection_stats.return_value = {"count": 100}
        
        # Test getting database info
        result = db_manager.get_database_info()
        
        # Verify result
        assert result["database_name"] == "test_stock_data"
        assert result["collections"] == ["stock_data", "financial_data"]
        assert result["collection_count"] == 2
        assert result["data_size"] == 1000000
        assert "collection_stats" in result
    
    def test_context_manager(self, db_manager):
        """Test context manager functionality."""
        with patch.object(db_manager, 'connect') as mock_connect, \
             patch.object(db_manager, 'disconnect') as mock_disconnect:
            
            with db_manager:
                pass
            
            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()
    
    def test_stock_data_to_doc_conversion(self, db_manager, sample_stock_data):
        """Test conversion from StockData to MongoDB document."""
        doc = db_manager._stock_data_to_doc(sample_stock_data)
        
        assert doc["symbol"] == "AAPL"
        assert doc["date"] == datetime(2024, 1, 15)
        assert doc["close"] == 154.0
        assert "created_at" in doc
        assert "updated_at" in doc
    
    def test_doc_to_stock_data_conversion(self, db_manager):
        """Test conversion from MongoDB document to StockData."""
        doc = {
            "_id": "some_id",
            "symbol": "AAPL",
            "date": datetime(2024, 1, 15),
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "volume": 1000000,
            "adjusted_close": 154.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        stock_data = db_manager._doc_to_stock_data(doc)
        
        assert isinstance(stock_data, StockData)
        assert stock_data.symbol == "AAPL"
        assert stock_data.close == 154.0
        assert "_id" not in stock_data.__dict__
    
    def test_financial_data_to_doc_conversion(self, db_manager, sample_financial_data):
        """Test conversion from FinancialData to MongoDB document."""
        doc = db_manager._financial_data_to_doc(sample_financial_data)
        
        assert doc["symbol"] == "AAPL"
        assert doc["fiscal_year"] == 2024
        assert doc["eps"] == 6.15
        assert "created_at" in doc
        assert "updated_at" in doc
    
    def test_doc_to_financial_data_conversion(self, db_manager):
        """Test conversion from MongoDB document to FinancialData."""
        doc = {
            "_id": "some_id",
            "symbol": "AAPL",
            "fiscal_year": 2024,
            "fiscal_quarter": 1,
            "revenue": 100000000000,
            "net_income": 25000000000,
            "eps": 6.15,
            "per": 25.0,
            "pbr": 3.5,
            "roe": 0.167,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        financial_data = db_manager._doc_to_financial_data(doc)
        
        assert isinstance(financial_data, FinancialData)
        assert financial_data.symbol == "AAPL"
        assert financial_data.eps == 6.15
        assert "_id" not in financial_data.__dict__