#!/usr/bin/env python3
"""
Command-line interface for NASDAQ symbol fetching operations.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import stock_database
sys.path.append(str(Path(__file__).parent.parent))

from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager
from stock_database.utils.nasdaq_symbol_fetcher import NasdaqSymbolFetcher
from stock_database.utils.symbol_data_source import FilterCriteria

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='NASDAQ Symbol Fetcher CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all NASDAQ symbols
  python nasdaq_symbol_cli.py fetch-all
  
  # Update symbol database
  python nasdaq_symbol_cli.py update
  
  # Search for symbols
  python nasdaq_symbol_cli.py search AAPL
  
  # Get symbols by sector
  python nasdaq_symbol_cli.py filter --sector Technology --limit 10
  
  # Get large-cap symbols
  python nasdaq_symbol_cli.py filter --min-market-cap 10000000000
  
  # Show statistics
  python nasdaq_symbol_cli.py stats
        """
    )
    
    # Global options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch all symbols
    fetch_parser = subparsers.add_parser('fetch-all', help='Fetch all NASDAQ symbols')
    fetch_parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh from data sources'
    )
    fetch_parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of symbols to fetch'
    )
    
    # Update symbols
    update_parser = subparsers.add_parser('update', help='Update symbol database')
    update_parser.add_argument(
        '--full',
        action='store_true',
        help='Perform full update instead of incremental'
    )
    
    # Search symbols
    search_parser = subparsers.add_parser('search', help='Search for symbols')
    search_parser.add_argument('query', help='Search query (symbol or company name)')
    search_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of results (default: 10)'
    )
    
    # Filter symbols
    filter_parser = subparsers.add_parser('filter', help='Filter symbols by criteria')
    filter_parser.add_argument(
        '--sector',
        help='Filter by sector'
    )
    filter_parser.add_argument(
        '--industry',
        help='Filter by industry'
    )
    filter_parser.add_argument(
        '--min-market-cap',
        type=float,
        help='Minimum market capitalization'
    )
    filter_parser.add_argument(
        '--max-market-cap',
        type=float,
        help='Maximum market capitalization'
    )
    filter_parser.add_argument(
        '--include-inactive',
        action='store_true',
        help='Include inactive symbols'
    )
    filter_parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of results'
    )
    
    # Get symbol info
    info_parser = subparsers.add_parser('info', help='Get information for a specific symbol')
    info_parser.add_argument('symbol', help='Stock symbol to get info for')
    
    # Show statistics
    subparsers.add_parser('stats', help='Show database statistics')
    
    # List sectors
    subparsers.add_parser('sectors', help='List all available sectors')
    
    return parser


def format_symbol_info(symbol_info, detailed=False):
    """Format symbol information for display."""
    if detailed:
        lines = [
            f"Symbol: {symbol_info.symbol}",
            f"Company: {symbol_info.company_name}",
            f"Exchange: {symbol_info.exchange}",
            f"Sector: {symbol_info.sector or 'N/A'}",
            f"Industry: {symbol_info.industry or 'N/A'}",
            f"Market Cap: ${symbol_info.market_cap:,.0f}" if symbol_info.market_cap else "Market Cap: N/A",
            f"Active: {'Yes' if symbol_info.is_active else 'No'}",
            f"Market Cap Category: {symbol_info.get_market_cap_category().title()}",
            f"Last Updated: {symbol_info.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        return "\\n".join(lines)
    else:
        market_cap_str = f"${symbol_info.market_cap:,.0f}" if symbol_info.market_cap else "N/A"
        status = "✓" if symbol_info.is_active else "✗"
        return f"{status} {symbol_info.symbol:<8} {symbol_info.company_name:<40} {symbol_info.sector or 'N/A':<20} {market_cap_str:>15}"


def cmd_fetch_all(args, fetcher: NasdaqSymbolFetcher):
    """Handle fetch-all command."""
    logger.info("Fetching all NASDAQ symbols...")
    
    try:
        symbols = fetcher.fetch_all_symbols(force_refresh=args.force_refresh)
        
        if args.limit:
            symbols = symbols[:args.limit]
        
        print(f"\\nFetched {len(symbols)} NASDAQ symbols:")
        print(f"{'Status':<6} {'Symbol':<8} {'Company Name':<40} {'Sector':<20} {'Market Cap':>15}")
        print("-" * 90)
        
        for symbol in symbols:
            print(format_symbol_info(symbol))
        
        print(f"\\nTotal: {len(symbols)} symbols")
        
    except Exception as e:
        logger.error(f"Failed to fetch symbols: {e}")
        sys.exit(1)


def cmd_update(args, fetcher: NasdaqSymbolFetcher):
    """Handle update command."""
    update_type = "full" if args.full else "incremental"
    logger.info(f"Starting {update_type} symbol update...")
    
    try:
        summary = fetcher.update_symbols(incremental=not args.full)
        
        print(f"\\nUpdate Summary:")
        print(f"Duration: {summary.duration:.2f} seconds")
        print(f"Total Fetched: {summary.total_fetched}")
        print(f"New Symbols: {summary.new_symbols}")
        print(f"Updated Symbols: {summary.updated_symbols}")
        print(f"Deactivated Symbols: {summary.deactivated_symbols}")
        print(f"Errors: {summary.errors}")
        
        if summary.data_sources_used:
            print(f"Data Sources Used: {', '.join(summary.data_sources_used)}")
        
        if summary.error_messages:
            print(f"\\nErrors:")
            for error in summary.error_messages[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(summary.error_messages) > 5:
                print(f"  ... and {len(summary.error_messages) - 5} more errors")
        
        if summary.errors == 0:
            print("\\n✓ Update completed successfully!")
        else:
            print(f"\\n⚠ Update completed with {summary.errors} errors")
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        sys.exit(1)


def cmd_search(args, fetcher: NasdaqSymbolFetcher):
    """Handle search command."""
    logger.info(f"Searching for symbols matching '{args.query}'...")
    
    try:
        symbols = fetcher.search_symbols(args.query, limit=args.limit)
        
        if not symbols:
            print(f"No symbols found matching '{args.query}'")
            return
        
        print(f"\\nFound {len(symbols)} symbols matching '{args.query}':")
        print(f"{'Status':<6} {'Symbol':<8} {'Company Name':<40} {'Sector':<20} {'Market Cap':>15}")
        print("-" * 90)
        
        for symbol in symbols:
            print(format_symbol_info(symbol))
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        sys.exit(1)


def cmd_filter(args, fetcher: NasdaqSymbolFetcher):
    """Handle filter command."""
    # Build filter criteria
    criteria = FilterCriteria(
        sector=args.sector,
        industry=args.industry,
        min_market_cap=args.min_market_cap,
        max_market_cap=args.max_market_cap,
        active_only=not args.include_inactive
    )
    
    logger.info(f"Filtering symbols with criteria: {criteria}")
    
    try:
        symbols = fetcher.fetch_symbols_by_criteria(criteria)
        
        if args.limit:
            symbols = symbols[:args.limit]
        
        if not symbols:
            print("No symbols found matching the specified criteria")
            return
        
        print(f"\\nFound {len(symbols)} symbols matching criteria:")
        print(f"{'Status':<6} {'Symbol':<8} {'Company Name':<40} {'Sector':<20} {'Market Cap':>15}")
        print("-" * 90)
        
        for symbol in symbols:
            print(format_symbol_info(symbol))
        
    except Exception as e:
        logger.error(f"Filter failed: {e}")
        sys.exit(1)


def cmd_info(args, fetcher: NasdaqSymbolFetcher):
    """Handle info command."""
    symbol = args.symbol.upper()
    logger.info(f"Getting information for symbol {symbol}...")
    
    try:
        symbol_info = fetcher.get_symbol(symbol)
        
        if not symbol_info:
            print(f"Symbol '{symbol}' not found")
            return
        
        print(f"\\nInformation for {symbol}:")
        print("=" * 50)
        print(format_symbol_info(symbol_info, detailed=True))
        
    except Exception as e:
        logger.error(f"Failed to get symbol info: {e}")
        sys.exit(1)


def cmd_stats(args, fetcher: NasdaqSymbolFetcher):
    """Handle stats command."""
    logger.info("Getting database statistics...")
    
    try:
        stats = fetcher.get_statistics()
        
        print("\\nNASDAQ Symbol Database Statistics:")
        print("=" * 40)
        
        repo_stats = stats.get('repository_stats', {})
        print(f"Total Symbols: {repo_stats.get('total_symbols', 0):,}")
        print(f"Active Symbols: {repo_stats.get('active_symbols', 0):,}")
        print(f"Inactive Symbols: {repo_stats.get('inactive_symbols', 0):,}")
        print(f"Sectors: {repo_stats.get('sectors', 0)}")
        
        # Market cap distribution
        market_cap_dist = repo_stats.get('market_cap_distribution', {})
        if market_cap_dist:
            print("\\nMarket Cap Distribution:")
            print(f"  Large Cap (>$10B): {market_cap_dist.get('large_cap', 0):,}")
            print(f"  Mid Cap ($2B-$10B): {market_cap_dist.get('mid_cap', 0):,}")
            print(f"  Small Cap (<$2B): {market_cap_dist.get('small_cap', 0):,}")
        
        # Data sources
        data_sources = stats.get('data_sources', [])
        if data_sources:
            print("\\nData Sources:")
            for source in data_sources:
                status = "✓" if source.get('available') else "✗"
                rate_limit = source.get('rate_limit', 'N/A')
                print(f"  {status} {source.get('name')} (Rate Limit: {rate_limit}/min)")
        
        # Configuration
        config = stats.get('configuration', {})
        if config:
            print("\\nConfiguration:")
            print(f"  Batch Size: {config.get('batch_size', 'N/A')}")
            print(f"  Max Retries: {config.get('max_retries', 'N/A')}")
            if config.get('min_market_cap'):
                print(f"  Min Market Cap: ${config['min_market_cap']:,.0f}")
            if config.get('exclude_sectors'):
                print(f"  Excluded Sectors: {', '.join(config['exclude_sectors'])}")
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        sys.exit(1)


def cmd_sectors(args, fetcher: NasdaqSymbolFetcher):
    """Handle sectors command."""
    logger.info("Getting available sectors...")
    
    try:
        sectors = fetcher.repository.get_sectors()
        
        if not sectors:
            print("No sectors found in database")
            return
        
        print(f"\\nAvailable Sectors ({len(sectors)}):")
        print("-" * 30)
        
        for sector in sorted(sectors):
            # Get count of symbols in this sector
            sector_symbols = fetcher.repository.get_symbols_by_sector(sector)
            print(f"{sector:<25} ({len(sector_symbols):,} symbols)")
        
    except Exception as e:
        logger.error(f"Failed to get sectors: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Initialize fetcher
        logger.debug("Initializing NASDAQ symbol fetcher...")
        config_manager = get_config_manager()
        db_manager = DatabaseManager(config_manager)
        fetcher = NasdaqSymbolFetcher(config_manager, db_manager)
        
        # Route to appropriate command handler
        command_handlers = {
            'fetch-all': cmd_fetch_all,
            'update': cmd_update,
            'search': cmd_search,
            'filter': cmd_filter,
            'info': cmd_info,
            'stats': cmd_stats,
            'sectors': cmd_sectors
        }
        
        handler = command_handlers.get(args.command)
        if handler:
            handler(args, fetcher)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()