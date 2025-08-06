"""
Main orchestrator for NASDAQ symbol fetching operations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..config import get_config_manager, with_config
from ..database_factory import DatabaseManager
from ..models.symbol_info import SymbolInfo
from ..repositories.symbol_repository import SymbolRepository
from .symbol_data_source import (FilterCriteria, SymbolDataSource,
                                 SymbolDataSourceError)
from .yfinance_symbol_source import YFinanceSymbolSource

logger = logging.getLogger(__name__)


class UpdateSummary:
    """Summary of a symbol update operation."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.total_fetched = 0
        self.new_symbols = 0
        self.updated_symbols = 0
        self.deactivated_symbols = 0
        self.errors = 0
        self.error_messages: List[str] = []
        self.data_sources_used: List[str] = []
    
    def finish(self):
        """Mark the update as finished."""
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> float:
        """Get the duration of the update in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration,
            'total_fetched': self.total_fetched,
            'new_symbols': self.new_symbols,
            'updated_symbols': self.updated_symbols,
            'deactivated_symbols': self.deactivated_symbols,
            'errors': self.errors,
            'error_messages': self.error_messages,
            'data_sources_used': self.data_sources_used
        }
    
    def __str__(self) -> str:
        """String representation of the summary."""
        return (f"UpdateSummary(fetched={self.total_fetched}, new={self.new_symbols}, "
                f"updated={self.updated_symbols}, errors={self.errors}, "
                f"duration={self.duration:.2f}s)")


class NasdaqSymbolFetcher:
    """
    Main orchestrator for NASDAQ symbol fetching operations.
    
    This class manages multiple data sources and provides high-level operations
    for fetching, storing, and updating NASDAQ stock symbols.
    """
    
    def __init__(
        self,
        config_manager=None,
        db_manager=None,
        data_sources: Optional[List[SymbolDataSource]] = None
    ):
        """
        Initialize the NASDAQ symbol fetcher.
        
        Args:
            config_manager: Configuration manager instance
            db_manager: Database manager instance
            data_sources: List of data sources to use
        """
        if config_manager is None:
            config_manager = get_config_manager()
        self.config_manager = config_manager
        self.db_manager = db_manager or DatabaseManager(self.config_manager)
        self.repository = SymbolRepository(self.db_manager)
        
        # Initialize data sources
        self.data_sources = data_sources or self._initialize_default_sources()
        
        # Load configuration
        self._load_config()
        
        logger.info(f"NasdaqSymbolFetcher initialized with {len(self.data_sources)} data sources")
    
    def _load_config(self):
        """Load configuration settings."""
        nasdaq_config = self.config_manager.get("nasdaq_fetcher", {})
        
        self.max_retries = nasdaq_config.get("max_retries", 3)
        self.retry_delay = nasdaq_config.get("retry_delay", 5.0)
        self.batch_size = nasdaq_config.get("batch_size", 100)
        
        # Filtering configuration
        filtering_config = nasdaq_config.get("filtering", {})
        self.min_market_cap = filtering_config.get("min_market_cap")
        self.exclude_sectors = filtering_config.get("exclude_sectors", [])
    
    def _initialize_default_sources(self) -> List[SymbolDataSource]:
        """Initialize default data sources."""
        sources = []
        
        # Add YFinance source
        try:
            yfinance_source = YFinanceSymbolSource()
            sources.append(yfinance_source)
            logger.info("Added YFinance data source")
        except Exception as e:
            logger.warning(f"Failed to initialize YFinance source: {e}")
        
        # TODO: Add other sources (NASDAQ API, etc.) when implemented
        
        return sources
    
    def fetch_all_symbols(self, force_refresh: bool = False) -> List[SymbolInfo]:
        """
        Fetch all NASDAQ symbols from available data sources.
        
        Args:
            force_refresh: Force refresh from data sources even if cached data exists
            
        Returns:
            List[SymbolInfo]: List of all fetched symbols
        """
        logger.info("Starting fetch of all NASDAQ symbols")
        
        try:
            # Check if we should use cached data
            if not force_refresh:
                existing_count = self.repository.get_symbol_count()
                if existing_count > 0:
                    logger.info(f"Using cached symbols ({existing_count} symbols)")
                    return self.repository.get_all_symbols()
            
            # Fetch from data sources
            all_symbols = []
            successful_sources = []
            
            for source in self.data_sources:
                try:
                    logger.info(f"Attempting to fetch symbols from {source.get_source_name()}")
                    
                    # Try to fetch symbols even if availability check fails
                    symbols = source.fetch_symbols()
                    
                    if symbols:
                        all_symbols.extend(symbols)
                        successful_sources.append(source.get_source_name())
                        logger.info(f"Fetched {len(symbols)} symbols from {source.get_source_name()}")
                    else:
                        logger.warning(f"No symbols returned from {source.get_source_name()}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch from {source.get_source_name()}: {e}")
                    continue
            
            if not all_symbols:
                raise SymbolDataSourceError("No symbols could be fetched from any data source")
            
            # Remove duplicates (keep the first occurrence)
            unique_symbols = self._deduplicate_symbols(all_symbols)
            logger.info(f"Deduplicated to {len(unique_symbols)} unique symbols")
            
            # Apply global filters
            filtered_symbols = self._apply_global_filters(unique_symbols)
            logger.info(f"Applied filters, {len(filtered_symbols)} symbols remaining")
            
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch all symbols: {e}")
            raise
    
    def fetch_symbols_by_criteria(self, criteria: FilterCriteria) -> List[SymbolInfo]:
        """
        Fetch symbols matching specific criteria.
        
        Args:
            criteria: Filter criteria to apply
            
        Returns:
            List[SymbolInfo]: List of symbols matching the criteria
        """
        logger.info(f"Fetching symbols with criteria: {criteria}")
        
        try:
            # First try to get from database
            db_symbols = self.repository.get_symbols(criteria=criteria)
            
            if db_symbols:
                logger.info(f"Found {len(db_symbols)} symbols in database matching criteria")
                return db_symbols
            
            # If no database results, fetch from sources and filter
            all_symbols = self.fetch_all_symbols()
            filtered_symbols = [s for s in all_symbols if criteria.matches(s)]
            
            logger.info(f"Filtered {len(all_symbols)} symbols to {len(filtered_symbols)} matching criteria")
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch symbols by criteria: {e}")
            raise
    
    def update_symbols(self, incremental: bool = True) -> UpdateSummary:
        """
        Update symbol database with latest data.
        
        Args:
            incremental: If True, only update changed symbols; if False, full refresh
            
        Returns:
            UpdateSummary: Summary of the update operation
        """
        summary = UpdateSummary()
        logger.info(f"Starting {'incremental' if incremental else 'full'} symbol update")
        
        try:
            # Ensure database connection
            if not self.db_manager.is_connected():
                self.db_manager.connect()
            
            # Fetch latest symbols from sources
            try:
                latest_symbols = self.fetch_all_symbols(force_refresh=True)
                summary.total_fetched = len(latest_symbols)
                
                # Record which sources were used
                for source in self.data_sources:
                    if source.is_available():
                        summary.data_sources_used.append(source.get_source_name())
                
            except Exception as e:
                summary.errors += 1
                summary.error_messages.append(f"Failed to fetch symbols: {e}")
                logger.error(f"Failed to fetch symbols during update: {e}")
                summary.finish()
                return summary
            
            # Get existing symbols if incremental update
            existing_symbols = {}
            if incremental:
                try:
                    existing_list = self.repository.get_all_symbols(active_only=False)
                    existing_symbols = {s.symbol: s for s in existing_list}
                    logger.info(f"Found {len(existing_symbols)} existing symbols")
                except Exception as e:
                    logger.warning(f"Failed to get existing symbols: {e}")
            
            # Process symbols in batches
            for i in range(0, len(latest_symbols), self.batch_size):
                batch = latest_symbols[i:i + self.batch_size]
                
                try:
                    batch_summary = self._process_symbol_batch(batch, existing_symbols, incremental)
                    summary.new_symbols += batch_summary['new']
                    summary.updated_symbols += batch_summary['updated']
                    summary.errors += batch_summary['errors']
                    summary.error_messages.extend(batch_summary['error_messages'])
                    
                    logger.info(f"Processed batch {i//self.batch_size + 1}: "
                              f"{batch_summary['new']} new, {batch_summary['updated']} updated")
                    
                except Exception as e:
                    summary.errors += 1
                    summary.error_messages.append(f"Batch processing failed: {e}")
                    logger.error(f"Failed to process batch {i//self.batch_size + 1}: {e}")
            
            # Mark symbols as inactive if they're no longer in the latest data
            if incremental:
                try:
                    latest_symbol_set = {s.symbol for s in latest_symbols}
                    for existing_symbol in existing_symbols.values():
                        if existing_symbol.is_active and existing_symbol.symbol not in latest_symbol_set:
                            if self.repository.deactivate_symbol(existing_symbol.symbol):
                                summary.deactivated_symbols += 1
                                logger.info(f"Deactivated symbol: {existing_symbol.symbol}")
                except Exception as e:
                    summary.errors += 1
                    summary.error_messages.append(f"Failed to deactivate symbols: {e}")
                    logger.error(f"Failed to deactivate symbols: {e}")
            
            summary.finish()
            logger.info(f"Symbol update completed: {summary}")
            return summary
            
        except Exception as e:
            summary.errors += 1
            summary.error_messages.append(f"Update failed: {e}")
            summary.finish()
            logger.error(f"Symbol update failed: {e}")
            return summary
    
    def _process_symbol_batch(
        self,
        batch: List[SymbolInfo],
        existing_symbols: Dict[str, SymbolInfo],
        incremental: bool
    ) -> Dict[str, Any]:
        """
        Process a batch of symbols for update.
        
        Args:
            batch: Batch of symbols to process
            existing_symbols: Dictionary of existing symbols
            incremental: Whether this is an incremental update
            
        Returns:
            Dict[str, Any]: Summary of batch processing
        """
        summary = {'new': 0, 'updated': 0, 'errors': 0, 'error_messages': []}
        
        for symbol_info in batch:
            try:
                existing = existing_symbols.get(symbol_info.symbol)
                
                if existing is None:
                    # New symbol
                    if self.repository.create_symbol(symbol_info):
                        summary['new'] += 1
                    else:
                        summary['errors'] += 1
                        summary['error_messages'].append(f"Failed to create symbol: {symbol_info.symbol}")
                
                elif incremental and self._symbol_needs_update(existing, symbol_info):
                    # Update existing symbol
                    if self.repository.update_symbol(symbol_info):
                        summary['updated'] += 1
                    else:
                        summary['errors'] += 1
                        summary['error_messages'].append(f"Failed to update symbol: {symbol_info.symbol}")
                
                elif not incremental:
                    # Full update - always update
                    if self.repository.update_symbol(symbol_info):
                        summary['updated'] += 1
                    else:
                        summary['errors'] += 1
                        summary['error_messages'].append(f"Failed to update symbol: {symbol_info.symbol}")
                
            except Exception as e:
                summary['errors'] += 1
                summary['error_messages'].append(f"Error processing {symbol_info.symbol}: {e}")
                logger.error(f"Error processing symbol {symbol_info.symbol}: {e}")
        
        return summary
    
    def _symbol_needs_update(self, existing: SymbolInfo, new: SymbolInfo) -> bool:
        """
        Check if a symbol needs to be updated.
        
        Args:
            existing: Existing symbol information
            new: New symbol information
            
        Returns:
            bool: True if symbol needs update
        """
        # Check key fields that might change
        return (
            existing.company_name != new.company_name or
            existing.market_cap != new.market_cap or
            existing.sector != new.sector or
            existing.industry != new.industry or
            existing.is_active != new.is_active
        )
    
    def _deduplicate_symbols(self, symbols: List[SymbolInfo]) -> List[SymbolInfo]:
        """
        Remove duplicate symbols, keeping the first occurrence.
        
        Args:
            symbols: List of symbols that may contain duplicates
            
        Returns:
            List[SymbolInfo]: List of unique symbols
        """
        seen = set()
        unique_symbols = []
        
        for symbol in symbols:
            if symbol.symbol not in seen:
                seen.add(symbol.symbol)
                unique_symbols.append(symbol)
        
        return unique_symbols
    
    def _apply_global_filters(self, symbols: List[SymbolInfo]) -> List[SymbolInfo]:
        """
        Apply global configuration filters to symbols.
        
        Args:
            symbols: List of symbols to filter
            
        Returns:
            List[SymbolInfo]: Filtered list of symbols
        """
        filtered = symbols
        
        # Apply minimum market cap filter
        if self.min_market_cap:
            filtered = [s for s in filtered 
                       if s.market_cap is not None and s.market_cap >= self.min_market_cap]
        
        # Apply sector exclusions
        if self.exclude_sectors:
            filtered = [s for s in filtered 
                       if s.sector not in self.exclude_sectors]
        
        return filtered
    
    def get_symbol_count(self, active_only: bool = True) -> int:
        """
        Get the total number of symbols in the database.
        
        Args:
            active_only: Only count active symbols
            
        Returns:
            int: Number of symbols
        """
        return self.repository.get_symbol_count(active_only=active_only)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the symbol database.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        try:
            repo_stats = self.repository.get_statistics()
            
            # Add data source information
            source_info = []
            for source in self.data_sources:
                source_info.append({
                    'name': source.get_source_name(),
                    'available': source.is_available(),
                    'rate_limit': source.get_rate_limit(),
                    'supported_filters': source.get_supported_filters()
                })
            
            return {
                'repository_stats': repo_stats,
                'data_sources': source_info,
                'configuration': {
                    'max_retries': self.max_retries,
                    'batch_size': self.batch_size,
                    'min_market_cap': self.min_market_cap,
                    'exclude_sectors': self.exclude_sectors
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def search_symbols(self, query: str, limit: Optional[int] = None) -> List[SymbolInfo]:
        """
        Search for symbols by symbol or company name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[SymbolInfo]: List of matching symbols
        """
        return self.repository.search_symbols(query, limit=limit)
    
    def get_symbol(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get information for a specific symbol.
        
        Args:
            symbol: Stock symbol to retrieve
            
        Returns:
            Optional[SymbolInfo]: Symbol information or None if not found
        """
        return self.repository.get_symbol(symbol)
    
    def add_data_source(self, source: SymbolDataSource):
        """
        Add a new data source.
        
        Args:
            source: Data source to add
        """
        self.data_sources.append(source)
        logger.info(f"Added data source: {source.get_source_name()}")
    
    def remove_data_source(self, source_name: str) -> bool:
        """
        Remove a data source by name.
        
        Args:
            source_name: Name of the data source to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        for i, source in enumerate(self.data_sources):
            if source.get_source_name() == source_name:
                del self.data_sources[i]
                logger.info(f"Removed data source: {source_name}")
                return True
        
        logger.warning(f"Data source not found: {source_name}")
        return False