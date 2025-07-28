"""
Repository for NASDAQ symbol data operations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.symbol_info import SymbolInfo
from ..utils.symbol_data_source import FilterCriteria
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SymbolRepository(BaseRepository):
    """
    Repository for managing NASDAQ symbol data in the database.
    
    This repository provides high-level operations for storing, retrieving,
    and managing stock symbol information.
    """
    
    def __init__(self, db_manager):
        """
        Initialize the symbol repository.
        
        Args:
            db_manager: Database manager instance
        """
        super().__init__(db_manager)
        self.table_name = db_manager.NASDAQ_SYMBOLS_TABLE
    
    def get_collection_name(self) -> str:
        """Get the collection/table name for this repository."""
        return self.table_name
    
    def create_symbol(self, symbol_info: SymbolInfo) -> bool:
        """
        Create a new symbol record.
        
        Args:
            symbol_info: Symbol information to create
            
        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            if not symbol_info.validate():
                logger.error(f"Invalid symbol data: {symbol_info}")
                return False
            
            self.db_manager.upsert_nasdaq_symbols([symbol_info])
            logger.info(f"Created symbol: {symbol_info.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create symbol {symbol_info.symbol}: {e}")
            return False
    
    def bulk_create_symbols(self, symbols: List[SymbolInfo]) -> Dict[str, Any]:
        """
        Create multiple symbol records in bulk.
        
        Args:
            symbols: List of symbol information to create
            
        Returns:
            Dict[str, Any]: Summary of the bulk operation
        """
        try:
            # Validate all symbols first
            valid_symbols = []
            invalid_symbols = []
            
            for symbol_info in symbols:
                if symbol_info.validate():
                    valid_symbols.append(symbol_info)
                else:
                    invalid_symbols.append(symbol_info.symbol)
                    logger.warning(f"Invalid symbol data: {symbol_info.symbol}")
            
            # Insert valid symbols
            if valid_symbols:
                self.db_manager.upsert_nasdaq_symbols(valid_symbols)
            
            summary = {
                'total_requested': len(symbols),
                'created': len(valid_symbols),
                'invalid': len(invalid_symbols),
                'invalid_symbols': invalid_symbols
            }
            
            logger.info(f"Bulk create completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to bulk create symbols: {e}")
            raise
    
    def get_symbol(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Retrieve a specific symbol.
        
        Args:
            symbol: Stock symbol to retrieve
            
        Returns:
            Optional[SymbolInfo]: Symbol information or None if not found
        """
        try:
            return self.db_manager.get_nasdaq_symbol(symbol)
        except Exception as e:
            logger.error(f"Failed to get symbol {symbol}: {e}")
            return None
    
    def get_symbols(
        self,
        criteria: Optional[FilterCriteria] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SymbolInfo]:
        """
        Retrieve symbols with optional filtering.
        
        Args:
            criteria: Filter criteria
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[SymbolInfo]: List of symbol information
        """
        try:
            # Convert criteria to database parameters
            kwargs = {}
            if criteria:
                kwargs['active_only'] = criteria.active_only
                kwargs['sector'] = criteria.sector
                kwargs['min_market_cap'] = criteria.min_market_cap
                kwargs['max_market_cap'] = criteria.max_market_cap
            
            if limit:
                kwargs['limit'] = limit
            
            symbols = self.db_manager.get_nasdaq_symbols(**kwargs)
            
            # Apply offset if specified (database doesn't support it directly)
            if offset and offset > 0:
                symbols = symbols[offset:]
            
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    def get_all_symbols(self, active_only: bool = True) -> List[SymbolInfo]:
        """
        Retrieve all symbols.
        
        Args:
            active_only: Only return active symbols
            
        Returns:
            List[SymbolInfo]: List of all symbol information
        """
        try:
            return self.db_manager.get_nasdaq_symbols(active_only=active_only)
        except Exception as e:
            logger.error(f"Failed to get all symbols: {e}")
            return []
    
    def update_symbol(self, symbol_info: SymbolInfo) -> bool:
        """
        Update an existing symbol record.
        
        Args:
            symbol_info: Updated symbol information
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if not symbol_info.validate():
                logger.error(f"Invalid symbol data: {symbol_info}")
                return False
            
            # Update the last_updated timestamp
            symbol_info.last_updated = datetime.now()
            
            self.db_manager.upsert_nasdaq_symbols([symbol_info])
            logger.info(f"Updated symbol: {symbol_info.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update symbol {symbol_info.symbol}: {e}")
            return False
    
    def deactivate_symbol(self, symbol: str) -> bool:
        """
        Mark a symbol as inactive (delisted).
        
        Args:
            symbol: Stock symbol to deactivate
            
        Returns:
            bool: True if deactivated successfully, False otherwise
        """
        try:
            return self.db_manager.deactivate_nasdaq_symbol(symbol)
        except Exception as e:
            logger.error(f"Failed to deactivate symbol {symbol}: {e}")
            return False
    
    def delete_symbol(self, symbol: str) -> bool:
        """
        Delete a symbol record completely.
        
        Args:
            symbol: Stock symbol to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            self.db_manager.ensure_connection()
            cursor = self.db_manager.connection.cursor()
            
            cursor.execute(f"""
                DELETE FROM {self.table_name} WHERE symbol = ?
            """, (symbol,))
            
            self.db_manager.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted symbol: {symbol}")
                return True
            else:
                logger.warning(f"Symbol not found for deletion: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete symbol {symbol}: {e}")
            return False
    
    def get_symbol_count(self, active_only: bool = True) -> int:
        """
        Get the total number of symbols.
        
        Args:
            active_only: Only count active symbols
            
        Returns:
            int: Number of symbols
        """
        try:
            return self.db_manager.get_nasdaq_symbol_count(active_only=active_only)
        except Exception as e:
            logger.error(f"Failed to get symbol count: {e}")
            return 0
    
    def get_sectors(self) -> List[str]:
        """
        Get list of all sectors.
        
        Returns:
            List[str]: List of unique sectors
        """
        try:
            return self.db_manager.get_nasdaq_sectors()
        except Exception as e:
            logger.error(f"Failed to get sectors: {e}")
            return []
    
    def get_symbols_by_sector(self, sector: str, active_only: bool = True) -> List[SymbolInfo]:
        """
        Get symbols filtered by sector.
        
        Args:
            sector: Sector to filter by
            active_only: Only return active symbols
            
        Returns:
            List[SymbolInfo]: List of symbols in the sector
        """
        try:
            return self.db_manager.get_nasdaq_symbols(
                active_only=active_only,
                sector=sector
            )
        except Exception as e:
            logger.error(f"Failed to get symbols for sector {sector}: {e}")
            return []
    
    def get_symbols_by_market_cap(
        self,
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        active_only: bool = True
    ) -> List[SymbolInfo]:
        """
        Get symbols filtered by market capitalization.
        
        Args:
            min_market_cap: Minimum market cap
            max_market_cap: Maximum market cap
            active_only: Only return active symbols
            
        Returns:
            List[SymbolInfo]: List of symbols matching market cap criteria
        """
        try:
            return self.db_manager.get_nasdaq_symbols(
                active_only=active_only,
                min_market_cap=min_market_cap,
                max_market_cap=max_market_cap
            )
        except Exception as e:
            logger.error(f"Failed to get symbols by market cap: {e}")
            return []
    
    def get_large_cap_symbols(self, threshold: float = 10_000_000_000) -> List[SymbolInfo]:
        """
        Get large-cap symbols.
        
        Args:
            threshold: Market cap threshold for large-cap (default: $10B)
            
        Returns:
            List[SymbolInfo]: List of large-cap symbols
        """
        return self.get_symbols_by_market_cap(min_market_cap=threshold)
    
    def get_mid_cap_symbols(
        self,
        min_threshold: float = 2_000_000_000,
        max_threshold: float = 10_000_000_000
    ) -> List[SymbolInfo]:
        """
        Get mid-cap symbols.
        
        Args:
            min_threshold: Minimum market cap for mid-cap (default: $2B)
            max_threshold: Maximum market cap for mid-cap (default: $10B)
            
        Returns:
            List[SymbolInfo]: List of mid-cap symbols
        """
        return self.get_symbols_by_market_cap(
            min_market_cap=min_threshold,
            max_market_cap=max_threshold
        )
    
    def get_small_cap_symbols(self, threshold: float = 2_000_000_000) -> List[SymbolInfo]:
        """
        Get small-cap symbols.
        
        Args:
            threshold: Market cap threshold for small-cap (default: $2B)
            
        Returns:
            List[SymbolInfo]: List of small-cap symbols
        """
        return self.get_symbols_by_market_cap(max_market_cap=threshold)
    
    def search_symbols(self, query: str, limit: Optional[int] = None) -> List[SymbolInfo]:
        """
        Search symbols by symbol or company name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[SymbolInfo]: List of matching symbols
        """
        try:
            self.db_manager.ensure_connection()
            cursor = self.db_manager.connection.cursor()
            
            # Search in both symbol and company name
            sql_query = f"""
                SELECT * FROM {self.table_name}
                WHERE (symbol LIKE ? OR company_name LIKE ?) AND is_active = 1
                ORDER BY 
                    CASE WHEN symbol = ? THEN 1 ELSE 2 END,
                    symbol
            """
            params = [f"%{query}%", f"%{query}%", query.upper()]
            
            if limit:
                sql_query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            # Convert to SymbolInfo objects
            symbols = []
            for row in rows:
                symbol_info = SymbolInfo(
                    symbol=row['symbol'],
                    company_name=row['company_name'],
                    exchange=row['exchange'],
                    market_cap=row['market_cap'],
                    sector=row['sector'],
                    industry=row['industry'],
                    is_active=bool(row['is_active']),
                    first_listed=datetime.fromisoformat(row['first_listed']).date() if row['first_listed'] else None,
                    last_updated=datetime.fromisoformat(row['last_updated']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                symbols.append(symbol_info)
            
            logger.debug(f"Search for '{query}' returned {len(symbols)} results")
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to search symbols with query '{query}': {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the symbol repository
        """
        try:
            total_symbols = self.get_symbol_count(active_only=False)
            active_symbols = self.get_symbol_count(active_only=True)
            sectors = self.get_sectors()
            
            # Get market cap distribution
            large_cap_count = len(self.get_large_cap_symbols())
            mid_cap_count = len(self.get_mid_cap_symbols())
            small_cap_count = len(self.get_small_cap_symbols())
            
            return {
                'total_symbols': total_symbols,
                'active_symbols': active_symbols,
                'inactive_symbols': total_symbols - active_symbols,
                'sectors': len(sectors),
                'sector_list': sectors,
                'market_cap_distribution': {
                    'large_cap': large_cap_count,
                    'mid_cap': mid_cap_count,
                    'small_cap': small_cap_count
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository statistics: {e}")
            return {}