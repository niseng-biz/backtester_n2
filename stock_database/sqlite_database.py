"""
SQLite database manager for stock data storage and retrieval.
"""

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .config import get_config_manager
from .models.company_info import CompanyInfo
from .models.financial_data import FinancialData
from .models.stock_data import StockData
from .models.symbol_info import SymbolInfo

logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    SQLite connection and database management for stock data.
    
    Handles connection management, table creation, and basic CRUD operations
    for stock data, financial data, and company information.
    """
    
    def __init__(self, config_manager=None, db_path: Optional[str] = None):
        """
        Initialize SQLite manager.
        
        Args:
            config_manager: Configuration manager instance. If None, uses global instance.
            db_path: Path to SQLite database file. If None, uses default.
        """
        self.config = config_manager or get_config_manager()
        self.db_path = db_path or self._get_default_db_path()
        self.connection: Optional[sqlite3.Connection] = None
        self._connected = False
        
        # Table names
        self.STOCK_DATA_TABLE = "stock_data"
        self.FINANCIAL_DATA_TABLE = "financial_data"
        self.COMPANY_INFO_TABLE = "company_info"
        self.NASDAQ_SYMBOLS_TABLE = "nasdaq_symbols"
    
    def _get_default_db_path(self) -> str:
        """Get default database path."""
        db_config = self.config.get_database_config().get("sqlite", {})
        default_path = db_config.get("path", "data/stock_data.db")
        
        # Ensure directory exists
        db_path = Path(default_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(db_path)
    
    def connect(self) -> None:
        """
        Establish connection to SQLite database.
        
        Raises:
            Exception: If connection cannot be established
        """
        try:
            # Use check_same_thread=False to allow multi-threading
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Enable WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            
            self._connected = True
            
            # Create tables if they don't exist
            self.create_tables()
            
            logger.info(f"Connected to SQLite database at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            self._connected = False
            raise
    
    def disconnect(self) -> None:
        """Close SQLite connection."""
        if self.connection:
            self.connection.close()
            self._connected = False
            logger.info("Disconnected from SQLite database")
    
    def is_connected(self) -> bool:
        """
        Check if connected to SQLite database.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected and self.connection is not None
    
    def ensure_connection(self) -> None:
        """Ensure connection is established, reconnect if necessary."""
        if not self.is_connected():
            logger.info("Reconnecting to SQLite database...")
            self.connect()
    
    def create_tables(self) -> None:
        """
        Create tables for all data types.
        
        Raises:
            Exception: If table creation fails
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            # Stock data table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.STOCK_DATA_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    adjusted_close REAL NOT NULL,
                    dividend REAL,
                    stock_split REAL,
                    sma_20 REAL,
                    sma_50 REAL,
                    rsi REAL,
                    bb_upper REAL,
                    bb_middle REAL,
                    bb_lower REAL,
                    macd REAL,
                    macd_signal REAL,
                    macd_histogram REAL,
                    stoch_k REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(symbol, date)
                )
            """)
            
            # Create indexes for stock data
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_stock_symbol ON {self.STOCK_DATA_TABLE}(symbol)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_stock_date ON {self.STOCK_DATA_TABLE}(date)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_stock_symbol_date ON {self.STOCK_DATA_TABLE}(symbol, date)")
            
            # Financial data table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.FINANCIAL_DATA_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    fiscal_quarter INTEGER,
                    total_revenue REAL,
                    cost_of_revenue REAL,
                    gross_profit REAL,
                    operating_expense REAL,
                    operating_income REAL,
                    pretax_income REAL,
                    tax_provision REAL,
                    net_income REAL,
                    basic_eps REAL,
                    diluted_eps REAL,
                    total_assets REAL,
                    total_liabilities_net_minority_interest REAL,
                    stockholders_equity REAL,
                    cash_and_cash_equivalents REAL,
                    total_debt REAL,
                    operating_cash_flow REAL,
                    free_cash_flow REAL,
                    capital_expenditure REAL,
                    trailing_pe REAL,
                    forward_pe REAL,
                    price_to_book REAL,
                    return_on_equity REAL,
                    return_on_assets REAL,
                    debt_to_equity REAL,
                    current_ratio REAL,
                    quick_ratio REAL,
                    gross_margins REAL,
                    operating_margins REAL,
                    profit_margins REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(symbol, fiscal_year, fiscal_quarter)
                )
            """)
            
            # Create indexes for financial data
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_financial_symbol ON {self.FINANCIAL_DATA_TABLE}(symbol)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_financial_year ON {self.FINANCIAL_DATA_TABLE}(fiscal_year)")
            
            # Company info table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.COMPANY_INFO_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    long_name TEXT NOT NULL,
                    short_name TEXT,
                    sector TEXT,
                    industry TEXT,
                    market_cap REAL,
                    country TEXT,
                    currency TEXT,
                    exchange TEXT,
                    website TEXT,
                    business_summary TEXT,
                    full_time_employees INTEGER,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    phone TEXT,
                    address1 TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for company info
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_company_symbol ON {self.COMPANY_INFO_TABLE}(symbol)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_company_sector ON {self.COMPANY_INFO_TABLE}(sector)")
            
            # NASDAQ symbols table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.NASDAQ_SYMBOLS_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    company_name TEXT NOT NULL,
                    exchange TEXT DEFAULT 'NASDAQ',
                    market_cap REAL,
                    sector TEXT,
                    industry TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    first_listed DATE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for NASDAQ symbols
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_nasdaq_symbol ON {self.NASDAQ_SYMBOLS_TABLE}(symbol)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_nasdaq_sector ON {self.NASDAQ_SYMBOLS_TABLE}(sector)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_nasdaq_active ON {self.NASDAQ_SYMBOLS_TABLE}(is_active)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_nasdaq_market_cap ON {self.NASDAQ_SYMBOLS_TABLE}(market_cap)")
            
            self.connection.commit()
            logger.info("Created SQLite tables and indexes")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    # Stock Data Operations
    
    def insert_stock_data(self, data: Union[StockData, List[StockData]]) -> None:
        """
        Insert stock data into the database.
        
        Args:
            data: Single StockData instance or list of StockData instances
            
        Raises:
            Exception: If insertion fails
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if isinstance(data, StockData):
                data = [data]
            
            for stock_item in data:
                cursor.execute(f"""
                    INSERT OR IGNORE INTO {self.STOCK_DATA_TABLE} (
                        symbol, date, open, high, low, close, volume, adjusted_close,
                        dividend, stock_split, sma_20, sma_50, rsi, bb_upper, bb_middle,
                        bb_lower, macd, macd_signal, macd_histogram, stoch_k,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_item.symbol,
                    stock_item.date.isoformat(),
                    stock_item.open,
                    stock_item.high,
                    stock_item.low,
                    stock_item.close,
                    stock_item.volume,
                    stock_item.adjusted_close,
                    stock_item.dividend,
                    stock_item.stock_split,
                    stock_item.sma_20,
                    stock_item.sma_50,
                    stock_item.rsi,
                    stock_item.bb_upper,
                    stock_item.bb_middle,
                    stock_item.bb_lower,
                    stock_item.macd,
                    stock_item.macd_signal,
                    stock_item.macd_histogram,
                    stock_item.stoch_k,
                    stock_item.created_at.isoformat(),
                    stock_item.updated_at.isoformat()
                ))
            
            self.connection.commit()
            logger.debug(f"Inserted {len(data)} stock data records")
            
        except Exception as e:
            logger.error(f"Failed to insert stock data: {e}")
            raise
    
    def upsert_stock_data(self, data: Union[StockData, List[StockData]]) -> None:
        """
        Insert or update stock data (upsert operation).
        
        Args:
            data: Single StockData instance or list of StockData instances
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if isinstance(data, StockData):
                data = [data]
            
            for stock_item in data:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {self.STOCK_DATA_TABLE} (
                        symbol, date, open, high, low, close, volume, adjusted_close,
                        dividend, stock_split, sma_20, sma_50, rsi, bb_upper, bb_middle,
                        bb_lower, macd, macd_signal, macd_histogram, stoch_k,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_item.symbol,
                    stock_item.date.isoformat(),
                    stock_item.open,
                    stock_item.high,
                    stock_item.low,
                    stock_item.close,
                    stock_item.volume,
                    stock_item.adjusted_close,
                    stock_item.dividend,
                    stock_item.stock_split,
                    stock_item.sma_20,
                    stock_item.sma_50,
                    stock_item.rsi,
                    stock_item.bb_upper,
                    stock_item.bb_middle,
                    stock_item.bb_lower,
                    stock_item.macd,
                    stock_item.macd_signal,
                    stock_item.macd_histogram,
                    stock_item.stoch_k,
                    stock_item.created_at.isoformat(),
                    stock_item.updated_at.isoformat()
                ))
            
            self.connection.commit()
            logger.info(f"Upserted {len(data)} stock data records")
            
        except Exception as e:
            logger.error(f"Failed to upsert stock data: {e}")
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
        
        try:
            cursor = self.connection.cursor()
            
            # Build query
            query = f"SELECT * FROM {self.STOCK_DATA_TABLE} WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY date DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to StockData objects
            results = []
            for row in rows:
                stock_data = StockData(
                    symbol=row['symbol'],
                    date=datetime.fromisoformat(row['date']),
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    adjusted_close=row['adjusted_close'],
                    dividend=row['dividend'],
                    stock_split=row['stock_split'],
                    sma_20=row['sma_20'],
                    sma_50=row['sma_50'],
                    rsi=row['rsi'],
                    bb_upper=row['bb_upper'],
                    bb_middle=row['bb_middle'],
                    bb_lower=row['bb_lower'],
                    macd=row['macd'],
                    macd_signal=row['macd_signal'],
                    macd_histogram=row['macd_histogram'],
                    stoch_k=row['stoch_k'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                results.append(stock_data)
            
            logger.debug(f"Retrieved {len(results)} stock data records for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve stock data: {e}")
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
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT MAX(date) as latest_date FROM {self.STOCK_DATA_TABLE} WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row and row['latest_date']:
                return datetime.fromisoformat(row['latest_date'])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest stock date: {e}")
            raise
    
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
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            # Build update query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            query = f"UPDATE {self.STOCK_DATA_TABLE} SET {set_clause} WHERE symbol = ? AND date = ?"
            
            params = list(updates.values()) + [symbol, date.isoformat()]
            cursor.execute(query, params)
            
            self.connection.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Updated stock data for {symbol} on {date}")
                return True
            else:
                logger.debug(f"No stock data found to update for {symbol} on {date}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update stock data: {e}")
            raise
    
    # Financial Data Operations
    
    def insert_financial_data(self, data: Union[FinancialData, List[FinancialData]]) -> None:
        """
        Insert financial data into the database.
        
        Args:
            data: Single FinancialData instance or list of FinancialData instances
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if isinstance(data, FinancialData):
                data = [data]
            
            for financial_item in data:
                cursor.execute(f"""
                    INSERT OR IGNORE INTO {self.FINANCIAL_DATA_TABLE} (
                        symbol, fiscal_year, fiscal_quarter, total_revenue, cost_of_revenue,
                        gross_profit, operating_expense, operating_income, pretax_income,
                        tax_provision, net_income, basic_eps, diluted_eps, total_assets,
                        total_liabilities_net_minority_interest, stockholders_equity,
                        cash_and_cash_equivalents, total_debt, operating_cash_flow,
                        free_cash_flow, capital_expenditure, trailing_pe, forward_pe,
                        price_to_book, return_on_equity, return_on_assets, debt_to_equity,
                        current_ratio, quick_ratio, gross_margins, operating_margins,
                        profit_margins, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    financial_item.symbol,
                    financial_item.fiscal_year,
                    financial_item.fiscal_quarter,
                    financial_item.total_revenue,
                    financial_item.cost_of_revenue,
                    financial_item.gross_profit,
                    financial_item.operating_expense,
                    financial_item.operating_income,
                    financial_item.pretax_income,
                    financial_item.tax_provision,
                    financial_item.net_income,
                    financial_item.basic_eps,
                    financial_item.diluted_eps,
                    financial_item.total_assets,
                    financial_item.total_liabilities_net_minority_interest,
                    financial_item.stockholders_equity,
                    financial_item.cash_and_cash_equivalents,
                    financial_item.total_debt,
                    financial_item.operating_cash_flow,
                    financial_item.free_cash_flow,
                    financial_item.capital_expenditure,
                    financial_item.trailing_pe,
                    financial_item.forward_pe,
                    financial_item.price_to_book,
                    financial_item.return_on_equity,
                    financial_item.return_on_assets,
                    financial_item.debt_to_equity,
                    financial_item.current_ratio,
                    financial_item.quick_ratio,
                    financial_item.gross_margins,
                    financial_item.operating_margins,
                    financial_item.profit_margins,
                    financial_item.created_at.isoformat(),
                    financial_item.updated_at.isoformat()
                ))
            
            self.connection.commit()
            logger.debug(f"Inserted {len(data)} financial data records")
            
        except Exception as e:
            logger.error(f"Failed to insert financial data: {e}")
            raise
    
    def upsert_financial_data(self, data: Union[FinancialData, List[FinancialData]]) -> None:
        """
        Insert or update financial data (upsert operation).
        
        Args:
            data: Single FinancialData instance or list of FinancialData instances
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if isinstance(data, FinancialData):
                data = [data]
            
            for financial_item in data:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {self.FINANCIAL_DATA_TABLE} (
                        symbol, fiscal_year, fiscal_quarter, total_revenue, cost_of_revenue,
                        gross_profit, operating_expense, operating_income, pretax_income,
                        tax_provision, net_income, basic_eps, diluted_eps, total_assets,
                        total_liabilities_net_minority_interest, stockholders_equity,
                        cash_and_cash_equivalents, total_debt, operating_cash_flow,
                        free_cash_flow, capital_expenditure, trailing_pe, forward_pe,
                        price_to_book, return_on_equity, return_on_assets, debt_to_equity,
                        current_ratio, quick_ratio, gross_margins, operating_margins,
                        profit_margins, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    financial_item.symbol,
                    financial_item.fiscal_year,
                    financial_item.fiscal_quarter,
                    financial_item.total_revenue,
                    financial_item.cost_of_revenue,
                    financial_item.gross_profit,
                    financial_item.operating_expense,
                    financial_item.operating_income,
                    financial_item.pretax_income,
                    financial_item.tax_provision,
                    financial_item.net_income,
                    financial_item.basic_eps,
                    financial_item.diluted_eps,
                    financial_item.total_assets,
                    financial_item.total_liabilities_net_minority_interest,
                    financial_item.stockholders_equity,
                    financial_item.cash_and_cash_equivalents,
                    financial_item.total_debt,
                    financial_item.operating_cash_flow,
                    financial_item.free_cash_flow,
                    financial_item.capital_expenditure,
                    financial_item.trailing_pe,
                    financial_item.forward_pe,
                    financial_item.price_to_book,
                    financial_item.return_on_equity,
                    financial_item.return_on_assets,
                    financial_item.debt_to_equity,
                    financial_item.current_ratio,
                    financial_item.quick_ratio,
                    financial_item.gross_margins,
                    financial_item.operating_margins,
                    financial_item.profit_margins,
                    financial_item.created_at.isoformat(),
                    financial_item.updated_at.isoformat()
                ))
            
            self.connection.commit()
            logger.info(f"Upserted {len(data)} financial data records")
            
        except Exception as e:
            logger.error(f"Failed to upsert financial data: {e}")
            raise
    
    def upsert_company_info(self, data: Union['CompanyInfo', List['CompanyInfo']]) -> None:
        """
        Insert or update company info (upsert operation).
        
        Args:
            data: Single CompanyInfo instance or list of CompanyInfo instances
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if not isinstance(data, list):
                data = [data]
            
            for company_item in data:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {self.COMPANY_INFO_TABLE} (
                        symbol, long_name, short_name, sector, industry, market_cap,
                        country, currency, exchange, website, business_summary,
                        full_time_employees, city, state, zip_code, phone, address1,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_item.symbol,
                    company_item.long_name,
                    company_item.short_name,
                    company_item.sector,
                    company_item.industry,
                    company_item.market_cap,
                    company_item.country,
                    company_item.currency,
                    company_item.exchange,
                    company_item.website,
                    company_item.business_summary,
                    company_item.full_time_employees,
                    company_item.city,
                    company_item.state,
                    company_item.zip_code,
                    company_item.phone,
                    company_item.address1,
                    company_item.created_at.isoformat(),
                    company_item.updated_at.isoformat()
                ))
            
            self.connection.commit()
            logger.info(f"Upserted {len(data)} company info records")
            
        except Exception as e:
            logger.error(f"Failed to upsert company info: {e}")
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
        
        try:
            cursor = self.connection.cursor()
            
            # Build query
            query = f"SELECT * FROM {self.FINANCIAL_DATA_TABLE} WHERE symbol = ?"
            params = [symbol]
            
            if fiscal_year is not None:
                query += " AND fiscal_year = ?"
                params.append(fiscal_year)
            
            if fiscal_quarter is not None:
                query += " AND fiscal_quarter = ?"
                params.append(fiscal_quarter)
            
            query += " ORDER BY fiscal_year DESC, fiscal_quarter DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to FinancialData objects
            results = []
            for row in rows:
                financial_data = FinancialData(
                    symbol=row['symbol'],
                    fiscal_year=row['fiscal_year'],
                    fiscal_quarter=row['fiscal_quarter'],
                    total_revenue=row['total_revenue'],
                    cost_of_revenue=row['cost_of_revenue'],
                    gross_profit=row['gross_profit'],
                    operating_expense=row['operating_expense'],
                    operating_income=row['operating_income'],
                    pretax_income=row['pretax_income'],
                    tax_provision=row['tax_provision'],
                    net_income=row['net_income'],
                    basic_eps=row['basic_eps'],
                    diluted_eps=row['diluted_eps'],
                    total_assets=row['total_assets'],
                    total_liabilities_net_minority_interest=row['total_liabilities_net_minority_interest'],
                    stockholders_equity=row['stockholders_equity'],
                    cash_and_cash_equivalents=row['cash_and_cash_equivalents'],
                    total_debt=row['total_debt'],
                    operating_cash_flow=row['operating_cash_flow'],
                    free_cash_flow=row['free_cash_flow'],
                    capital_expenditure=row['capital_expenditure'],
                    trailing_pe=row['trailing_pe'],
                    forward_pe=row['forward_pe'],
                    price_to_book=row['price_to_book'],
                    return_on_equity=row['return_on_equity'],
                    return_on_assets=row['return_on_assets'],
                    debt_to_equity=row['debt_to_equity'],
                    current_ratio=row['current_ratio'],
                    quick_ratio=row['quick_ratio'],
                    gross_margins=row['gross_margins'],
                    operating_margins=row['operating_margins'],
                    profit_margins=row['profit_margins'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                results.append(financial_data)
            
            logger.debug(f"Retrieved {len(results)} financial data records for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve financial data: {e}")
            raise
    
    def get_data_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get a summary of available data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Any]: Summary including date range, record count, etc.
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            # Get basic stats
            cursor.execute(f"SELECT COUNT(*) as count FROM {self.STOCK_DATA_TABLE} WHERE symbol = ?", (symbol,))
            total_count = cursor.fetchone()['count']
            
            if total_count == 0:
                return {
                    "symbol": symbol,
                    "total_records": 0,
                    "date_range": None,
                    "latest_date": None,
                    "data_completeness": 0.0
                }
            
            # Get date range
            cursor.execute(f"""
                SELECT MIN(date) as min_date, MAX(date) as max_date 
                FROM {self.STOCK_DATA_TABLE} 
                WHERE symbol = ?
            """, (symbol,))
            date_row = cursor.fetchone()
            
            date_range = None
            if date_row['min_date'] and date_row['max_date']:
                min_date_str = date_row['min_date']
                max_date_str = date_row['max_date']
                # Handle both string and datetime objects
                if isinstance(min_date_str, str):
                    min_date = datetime.fromisoformat(min_date_str)
                else:
                    min_date = min_date_str
                if isinstance(max_date_str, str):
                    max_date = datetime.fromisoformat(max_date_str)
                else:
                    max_date = max_date_str
                date_range = (min_date, max_date)
            
            latest_date = max_date if date_range else None
            
            # Simple completeness calculation (assume 100% for existing data)
            completeness = 1.0 if total_count > 0 else 0.0
            
            return {
                "symbol": symbol,
                "total_records": total_count,
                "date_range": date_range,
                "latest_date": latest_date,
                "data_completeness": completeness
            }
            
        except Exception as e:
            logger.error(f"Failed to get data summary for {symbol}: {e}")
            raise
    
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
    
    # Database management operations
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dict[str, Any]: Database information
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            # Get table statistics
            table_stats = {}
            for table_name in [self.STOCK_DATA_TABLE, self.FINANCIAL_DATA_TABLE, self.COMPANY_INFO_TABLE, self.NASDAQ_SYMBOLS_TABLE]:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                table_stats[table_name] = {"count": count}
            
            # Get database file size
            db_path = Path(self.db_path)
            file_size = db_path.stat().st_size if db_path.exists() else 0
            
            return {
                "database_path": self.db_path,
                "database_size": file_size,
                "table_stats": table_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def get_collection(self, table_name: str):
        """
        Get a table reference (for compatibility with MongoDB interface).
        
        Args:
            table_name: Name of the table
            
        Returns:
            SQLiteTableWrapper: Wrapper object for table operations
        """
        return SQLiteTableWrapper(self, table_name)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    # NASDAQ Symbols Operations
    
    def upsert_nasdaq_symbols(self, symbols: Union[SymbolInfo, List[SymbolInfo]]) -> None:
        """
        Insert or update NASDAQ symbol information (upsert operation).
        
        Args:
            symbols: Single SymbolInfo instance or list of SymbolInfo instances
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if not isinstance(symbols, list):
                symbols = [symbols]
            
            for symbol_info in symbols:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO {self.NASDAQ_SYMBOLS_TABLE} (
                        symbol, company_name, exchange, market_cap, sector, industry,
                        is_active, first_listed, last_updated, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_info.symbol,
                    symbol_info.company_name,
                    symbol_info.exchange,
                    symbol_info.market_cap,
                    symbol_info.sector,
                    symbol_info.industry,
                    symbol_info.is_active,
                    symbol_info.first_listed.isoformat() if symbol_info.first_listed else None,
                    symbol_info.last_updated.isoformat(),
                    symbol_info.created_at.isoformat()
                ))
            
            self.connection.commit()
            logger.info(f"Upserted {len(symbols)} NASDAQ symbol records")
            
        except Exception as e:
            logger.error(f"Failed to upsert NASDAQ symbols: {e}")
            raise
    
    def get_nasdaq_symbols(
        self,
        active_only: bool = True,
        sector: Optional[str] = None,
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[SymbolInfo]:
        """
        Retrieve NASDAQ symbols with optional filtering.
        
        Args:
            active_only: Only return active symbols
            sector: Filter by sector
            min_market_cap: Minimum market cap filter
            max_market_cap: Maximum market cap filter
            limit: Maximum number of results
            
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            # Build query with filters
            query = f"SELECT * FROM {self.NASDAQ_SYMBOLS_TABLE} WHERE 1=1"
            params = []
            
            if active_only:
                query += " AND is_active = ?"
                params.append(True)
            
            if sector:
                query += " AND sector = ?"
                params.append(sector)
            
            if min_market_cap is not None:
                query += " AND market_cap >= ?"
                params.append(min_market_cap)
            
            if max_market_cap is not None:
                query += " AND market_cap <= ?"
                params.append(max_market_cap)
            
            query += " ORDER BY symbol"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to SymbolInfo objects
            results = []
            for row in rows:
                symbol_info = SymbolInfo(
                    symbol=row['symbol'],
                    company_name=row['company_name'],
                    exchange=row['exchange'],
                    market_cap=row['market_cap'],
                    sector=row['sector'],
                    industry=row['industry'],
                    is_active=bool(row['is_active']),
                    first_listed=date.fromisoformat(row['first_listed']) if row['first_listed'] else None,
                    last_updated=datetime.fromisoformat(row['last_updated']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                results.append(symbol_info)
            
            logger.debug(f"Retrieved {len(results)} NASDAQ symbol records")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve NASDAQ symbols: {e}")
            raise
    
    def get_nasdaq_symbol(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Retrieve a specific NASDAQ symbol.
        
        Args:
            symbol: Stock symbol to retrieve
            
        Returns:
            Optional[SymbolInfo]: Symbol information or None if not found
        """
        results = self.get_nasdaq_symbols(active_only=False, limit=1)
        return results[0] if results else None
    
    def get_nasdaq_sectors(self) -> List[str]:
        """
        Get list of all sectors in NASDAQ symbols.
        
        Returns:
            List[str]: List of unique sectors
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT DISTINCT sector 
                FROM {self.NASDAQ_SYMBOLS_TABLE} 
                WHERE sector IS NOT NULL AND is_active = 1
                ORDER BY sector
            """)
            rows = cursor.fetchall()
            return [row['sector'] for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get NASDAQ sectors: {e}")
            raise
    
    def get_nasdaq_symbol_count(self, active_only: bool = True) -> int:
        """
        Get count of NASDAQ symbols.
        
        Args:
            active_only: Only count active symbols
            
        Returns:
            int: Number of symbols
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            query = f"SELECT COUNT(*) as count FROM {self.NASDAQ_SYMBOLS_TABLE}"
            params = []
            
            if active_only:
                query += " WHERE is_active = ?"
                params.append(True)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count']
            
        except Exception as e:
            logger.error(f"Failed to get NASDAQ symbol count: {e}")
            raise
    
    def get_company_info(self, symbol: str) -> Optional['CompanyInfo']:
        """
        Get company information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[CompanyInfo]: Company information or None if not found
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT * FROM {self.COMPANY_INFO_TABLE} WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                from .models.company_info import CompanyInfo
                return CompanyInfo(
                    symbol=row['symbol'],
                    long_name=row['long_name'],
                    short_name=row['short_name'],
                    sector=row['sector'],
                    industry=row['industry'],
                    market_cap=row['market_cap'],
                    country=row['country'],
                    currency=row['currency'],
                    exchange=row['exchange'],
                    website=row['website'],
                    business_summary=row['business_summary'],
                    full_time_employees=row['full_time_employees'],
                    city=row['city'],
                    state=row['state'],
                    zip_code=row['zip_code'],
                    phone=row['phone'],
                    address1=row['address1'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company info: {e}")
            raise
    
    def deactivate_nasdaq_symbol(self, symbol: str) -> bool:
        """
        Mark a NASDAQ symbol as inactive (delisted).
        
        Args:
            symbol: Stock symbol to deactivate
            
        Returns:
            bool: True if symbol was found and deactivated
        """
        self.ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                UPDATE {self.NASDAQ_SYMBOLS_TABLE} 
                SET is_active = 0, last_updated = ? 
                WHERE symbol = ?
            """, (datetime.now().isoformat(), symbol))
            
            self.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deactivated NASDAQ symbol: {symbol}")
                return True
            else:
                logger.warning(f"NASDAQ symbol not found: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deactivate NASDAQ symbol {symbol}: {e}")
            raise


class SQLiteTableWrapper:
    """
    Wrapper class to provide MongoDB-like interface for SQLite tables.
    """
    
    def __init__(self, db_manager: SQLiteManager, table_name: str):
        """Initialize table wrapper."""
        self.db_manager = db_manager
        self.table_name = table_name
    
    def find_one(self, query: Dict[str, Any], sort: Optional[List[Tuple[str, int]]] = None) -> Optional[Dict[str, Any]]:
        """
        Find one document matching the query.
        
        Args:
            query: Query dictionary
            sort: Sort specification (list of (field, direction) tuples)
            
        Returns:
            Optional[Dict[str, Any]]: Matching document or None
        """
        self.db_manager.ensure_connection()
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Build WHERE clause
            where_clause, params = self._build_where_clause(query)
            sql = f"SELECT * FROM {self.table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            
            # Add ORDER BY clause
            if sort:
                order_parts = []
                for field, direction in sort:
                    order_direction = "DESC" if direction == -1 else "ASC"
                    order_parts.append(f"{field} {order_direction}")
                sql += f" ORDER BY {', '.join(order_parts)}"
            
            sql += " LIMIT 1"
            
            cursor.execute(sql, params)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find document in {self.table_name}: {e}")
            raise
    
    def count_documents(self, query: Dict[str, Any]) -> int:
        """
        Count documents matching the query.
        
        Args:
            query: Query dictionary
            
        Returns:
            int: Number of matching documents
        """
        self.db_manager.ensure_connection()
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Build WHERE clause
            where_clause, params = self._build_where_clause(query)
            sql = f"SELECT COUNT(*) as count FROM {self.table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            
            cursor.execute(sql, params)
            row = cursor.fetchone()
            
            return row['count'] if row else 0
            
        except Exception as e:
            logger.error(f"Failed to count documents in {self.table_name}: {e}")
            raise
    
    def find(self, query: Dict[str, Any]):
        """
        Find documents matching the query (returns a cursor-like object).
        
        Args:
            query: Query dictionary
            
        Returns:
            SQLiteCursor: Cursor-like object for chaining operations
        """
        return SQLiteCursor(self.db_manager, self.table_name, query)
    
    def _build_where_clause(self, query: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause from query dictionary.
        
        Args:
            query: Query dictionary
            
        Returns:
            Tuple[str, List[Any]]: WHERE clause and parameters
        """
        if not query:
            return "", []
        
        conditions = []
        params = []
        
        for key, value in query.items():
            conditions.append(f"{key} = ?")
            params.append(value)
        
        return " AND ".join(conditions), params


class SQLiteCursor:
    """
    Cursor-like object for SQLite queries to provide MongoDB-like interface.
    """
    
    def __init__(self, db_manager: SQLiteManager, table_name: str, query: Dict[str, Any]):
        """Initialize cursor."""
        self.db_manager = db_manager
        self.table_name = table_name
        self.query = query
        self.sort_fields = []
        self.limit_count = None
    
    def sort(self, field: str, direction: int = 1):
        """
        Add sort criteria.
        
        Args:
            field: Field name to sort by
            direction: 1 for ascending, -1 for descending
            
        Returns:
            SQLiteCursor: Self for chaining
        """
        self.sort_fields.append((field, direction))
        return self
    
    def limit(self, count: int):
        """
        Limit the number of results.
        
        Args:
            count: Maximum number of results
            
        Returns:
            SQLiteCursor: Self for chaining
        """
        self.limit_count = count
        return self
    
    def __iter__(self):
        """Execute the query and return results."""
        self.db_manager.ensure_connection()
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Build WHERE clause
            where_clause, params = self._build_where_clause(self.query)
            sql = f"SELECT * FROM {self.table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            
            # Add ORDER BY clause
            if self.sort_fields:
                order_parts = []
                for field, direction in self.sort_fields:
                    order_direction = "DESC" if direction == -1 else "ASC"
                    order_parts.append(f"{field} {order_direction}")
                sql += f" ORDER BY {', '.join(order_parts)}"
            
            # Add LIMIT clause
            if self.limit_count:
                sql += f" LIMIT {self.limit_count}"
            
            cursor.execute(sql, params)
            
            for row in cursor.fetchall():
                yield dict(row)
                
        except Exception as e:
            logger.error(f"Failed to execute cursor query on {self.table_name}: {e}")
            raise
    
    def _build_where_clause(self, query: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build WHERE clause from query dictionary."""
        if not query:
            return "", []
        
        conditions = []
        params = []
        
        for key, value in query.items():
            conditions.append(f"{key} = ?")
            params.append(value)
        
        return " AND ".join(conditions), params