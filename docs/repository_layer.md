# Repository Layer Documentation

## Overview

The repository layer provides a high-level data access interface for the stock database system. It implements the Repository pattern with advanced features like caching, performance monitoring, and optimized query patterns.

## Architecture

The repository layer consists of four main components:

1. **BaseRepository** - Abstract base class with common functionality
2. **StockDataRepository** - Stock price data access
3. **FinancialDataRepository** - Financial metrics data access  
4. **CompanyInfoRepository** - Company information data access
5. **DataAccessAPI** - Unified interface combining all repositories

## Features

### Caching System
- **Intelligent Caching**: Automatic caching with configurable TTL
- **Cache Invalidation**: Smart cache clearing on data updates
- **Performance Monitoring**: Cache hit/miss statistics

### Query Optimization
- **Bulk Operations**: Efficient multi-symbol queries
- **Index Utilization**: Optimized MongoDB queries
- **Result Pagination**: Memory-efficient large result handling

### Performance Monitoring
- **Query Statistics**: Execution time tracking
- **Operation Metrics**: Success/failure rates
- **Resource Usage**: Memory and connection monitoring

## Repository Classes

### BaseRepository

Abstract base class providing common functionality:

```python
from stock_database.repositories.base_repository import BaseRepository

class MyRepository(BaseRepository):
    def get_collection_name(self) -> str:
        return "my_collection"
```

**Features:**
- Caching with configurable TTL
- Performance monitoring decorators
- Database connection management
- Query statistics collection

### StockDataRepository

Handles stock price data operations:

```python
from stock_database.repositories import StockDataRepository

# Initialize repository
stock_repo = StockDataRepository(cache_ttl=300)  # 5 minutes cache

# Save stock data
stock_repo.save_stock_data(stock_data_list)

# Get stock data with date range
data = stock_repo.get_stock_data(
    symbol="AAPL",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Get recent data
recent = stock_repo.get_recent_data("AAPL", days=30)

# Get latest date
latest_date = stock_repo.get_latest_date("AAPL")

# Bulk operations
latest_dates = stock_repo.bulk_get_latest_dates(["AAPL", "GOOGL", "MSFT"])
```

**Key Methods:**
- `save_stock_data()` - Save/update stock data
- `get_stock_data()` - Retrieve with date filtering
- `get_recent_data()` - Get recent trading days
- `get_latest_date()` - Latest available date
- `get_missing_dates()` - Find data gaps
- `bulk_get_latest_dates()` - Efficient multi-symbol queries

### FinancialDataRepository

Handles financial metrics and ratios:

```python
from stock_database.repositories import FinancialDataRepository

# Initialize repository
financial_repo = FinancialDataRepository(cache_ttl=600)  # 10 minutes cache

# Save financial data
financial_repo.save_financial_data(financial_data_list)

# Get financial data
data = financial_repo.get_financial_data("AAPL", fiscal_year=2023)

# Get latest financial data
latest = financial_repo.get_latest_financial_data("AAPL", annual_only=True)

# Get annual data
annual = financial_repo.get_annual_data("AAPL", years=5)

# Calculate growth rates
growth = financial_repo.calculate_growth_rates("AAPL", "revenue", periods=5)

# Get financial ratios
ratios = financial_repo.get_financial_ratios("AAPL")

# Compare metrics across companies
comparison = financial_repo.compare_metrics(["AAPL", "GOOGL"], "revenue")
```

**Key Methods:**
- `save_financial_data()` - Save/update financial data
- `get_financial_data()` - Retrieve with fiscal year/quarter filtering
- `get_annual_data()` - Annual reports only
- `get_quarterly_data()` - Quarterly reports only
- `calculate_growth_rates()` - Growth rate analysis
- `get_financial_ratios()` - Financial ratio calculations
- `compare_metrics()` - Cross-company comparisons

### CompanyInfoRepository

Handles company metadata and information:

```python
from stock_database.repositories import CompanyInfoRepository

# Initialize repository
company_repo = CompanyInfoRepository(cache_ttl=1800)  # 30 minutes cache

# Save company info
company_repo.save_company_info(company_info_list)

# Get company info
info = company_repo.get_company_info("AAPL")

# Get companies by sector
tech_companies = company_repo.get_companies_by_sector("Technology")

# Get companies by industry
software_companies = company_repo.get_companies_by_industry("Software")

# Search companies
results = company_repo.search_companies("Apple", limit=10)

# Get companies by market cap
large_cap = company_repo.get_companies_by_market_cap(min_market_cap=1e12)

# Get sector summary
sector_stats = company_repo.get_sector_summary()

# Bulk operations
bulk_info = company_repo.bulk_get_company_info(["AAPL", "GOOGL", "MSFT"])
```

**Key Methods:**
- `save_company_info()` - Save/update company information
- `get_company_info()` - Retrieve company details
- `get_companies_by_sector()` - Filter by business sector
- `get_companies_by_industry()` - Filter by industry
- `search_companies()` - Text search functionality
- `get_companies_by_market_cap()` - Market cap filtering
- `get_sector_summary()` - Sector-level statistics
- `bulk_get_company_info()` - Efficient multi-symbol queries

## DataAccessAPI

Unified interface combining all repositories with advanced features:

```python
from stock_database.repositories import DataAccessAPI

# Initialize API
api = DataAccessAPI(
    stock_cache_ttl=300,      # 5 minutes
    financial_cache_ttl=600,  # 10 minutes  
    company_cache_ttl=1800    # 30 minutes
)

# Basic data access (delegates to individual repositories)
stock_data = api.get_stock_data("AAPL")
financial_data = api.get_financial_data("AAPL")
company_info = api.get_company_info("AAPL")

# Advanced cross-repository operations
complete_data = api.get_complete_company_data("AAPL")
bulk_data = api.bulk_get_latest_data(["AAPL", "GOOGL", "MSFT"])
sector_analysis = api.get_sector_analysis("Technology")
comparison = api.compare_companies(["AAPL", "GOOGL"], ["market_cap", "per"])

# Data management
api.save_all_data(
    stock_data=stock_data_list,
    financial_data=financial_data_list,
    company_info=company_info_list
)

# System monitoring
health = api.health_check()
stats = api.get_system_stats()
symbols = api.get_available_symbols()

# Cache management
api.clear_cache("AAPL")  # Clear specific symbol
api.clear_cache()        # Clear all cache
```

**Advanced Features:**
- `get_complete_company_data()` - All data for a company
- `bulk_get_latest_data()` - Efficient multi-symbol latest data
- `get_sector_analysis()` - Comprehensive sector analysis
- `compare_companies()` - Multi-metric company comparison
- `save_all_data()` - Coordinated multi-repository saves
- `health_check()` - System health monitoring
- `get_system_stats()` - Performance and usage statistics

## Caching Strategy

### Cache Levels
1. **Stock Data**: 5 minutes (frequent updates)
2. **Financial Data**: 10 minutes (less frequent updates)
3. **Company Info**: 30 minutes (rarely changes)

### Cache Keys
Cache keys are automatically generated based on method parameters:
```python
# Example cache keys
"get_stock_data:AAPL|2024-01-01T00:00:00|2024-01-31T00:00:00"
"get_financial_ratios:AAPL|fiscal_year=2023"
"get_company_info:AAPL"
```

### Cache Invalidation
- **Automatic**: Cache entries expire based on TTL
- **Manual**: Cache cleared on data updates
- **Selective**: Symbol-specific cache clearing

## Performance Monitoring

### Query Statistics
Each repository tracks:
- Query execution times
- Result counts
- Success/failure rates
- Average response times

### Accessing Statistics
```python
# Get query performance stats
stats = repo.get_query_stats()
print(f"Average query time: {stats['get_stock_data']['avg_duration']:.3f}s")

# Get cache performance
cache_stats = repo.get_cache_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")

# Clear statistics
repo.clear_query_stats()
```

## Error Handling

### Repository-Level Errors
- **Connection Errors**: Automatic retry with exponential backoff
- **Validation Errors**: Data validation before database operations
- **Query Errors**: Graceful degradation and error logging

### API-Level Errors
- **Partial Failures**: Continue processing other operations
- **Fallback Strategies**: Use cached data when possible
- **Error Aggregation**: Collect and report multiple errors

## Best Practices

### Repository Usage
1. **Reuse Instances**: Create repository instances once and reuse
2. **Shared Database Manager**: Use same database manager across repositories
3. **Appropriate Cache TTL**: Set cache TTL based on data update frequency
4. **Bulk Operations**: Use bulk methods for multiple symbols

### DataAccessAPI Usage
1. **Single Entry Point**: Use DataAccessAPI for most operations
2. **Health Monitoring**: Regular health checks in production
3. **Cache Management**: Monitor and manage cache usage
4. **Error Handling**: Implement proper error handling and logging

### Performance Optimization
1. **Index Usage**: Ensure proper database indexes
2. **Query Patterns**: Use efficient query patterns
3. **Batch Processing**: Process data in appropriate batch sizes
4. **Connection Pooling**: Use connection pooling for high-load scenarios

## Configuration

### Repository Configuration
```python
# Individual repository configuration
stock_repo = StockDataRepository(
    db_manager=db_manager,
    cache_ttl=300  # 5 minutes
)

# DataAccessAPI configuration
api = DataAccessAPI(
    db_manager=db_manager,
    stock_cache_ttl=300,
    financial_cache_ttl=600,
    company_cache_ttl=1800
)
```

### Database Configuration
```yaml
database:
  mongodb:
    host: "localhost"
    port: 27017
    database: "stock_data"
    connection_timeout: 30
    max_pool_size: 100
```

## Testing

### Unit Tests
All repositories include comprehensive unit tests:
```bash
# Run repository tests
python -m pytest tests/unit/test_repositories.py -v

# Run DataAccessAPI tests  
python -m pytest tests/unit/test_data_access_api.py -v

# Run all repository tests
python -m pytest tests/unit/test_repositories.py tests/unit/test_data_access_api.py -v
```

### Integration Tests
Integration tests verify database connectivity and operations:
```bash
# Run integration tests (requires MongoDB)
python -m pytest tests/integration/test_repository_integration.py -v
```

## Examples

### Basic Usage Example
```python
from stock_database.repositories import DataAccessAPI

# Setup
api = DataAccessAPI()

# Get complete company data
data = api.get_complete_company_data("AAPL")
print(f"Company: {data['company_info']['company_name']}")
print(f"Latest stock price: ${data['latest_stock_data']['close']}")
print(f"P/E Ratio: {data['financial_ratios']['per']}")
```

### Sector Analysis Example
```python
# Analyze technology sector
sector_data = api.get_sector_analysis("Technology", limit=20)

print(f"Technology sector has {sector_data['company_count']} companies")
print(f"Average market cap: ${sector_data['market_cap_stats']['mean']:,.0f}")

# Show top companies by market cap
for company in sector_data['companies'][:5]:
    print(f"{company['symbol']}: {company['company_name']}")
```

### Performance Monitoring Example
```python
# Monitor system performance
stats = api.get_system_stats()

# Database statistics
for collection, db_stats in stats['database_stats'].items():
    print(f"{collection}: {db_stats['count']} documents")

# Cache performance
for repo, cache_stats in stats['cache_stats'].items():
    print(f"{repo} cache: {cache_stats['active_entries']} entries")

# Query performance
for repo, query_stats in stats['query_stats'].items():
    total_queries = sum(stat['count'] for stat in query_stats.values())
    print(f"{repo}: {total_queries} total queries")
```

## Troubleshooting

### Common Issues

1. **Cache Not Working**
   - Check TTL configuration
   - Verify cache key generation
   - Monitor cache statistics

2. **Slow Queries**
   - Check database indexes
   - Review query patterns
   - Monitor query statistics

3. **Memory Usage**
   - Adjust cache TTL
   - Use pagination for large results
   - Monitor system statistics

4. **Connection Issues**
   - Check database connectivity
   - Verify connection pool settings
   - Use health check functionality

### Debugging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Repository operations will now log detailed information
api = DataAccessAPI()
data = api.get_stock_data("AAPL")
```

## Migration Guide

### From Direct Database Access
```python
# Old way - direct database access
db_manager = SQLiteManager()
collection = db_manager.get_collection("stock_data")
docs = collection.find({"symbol": "AAPL"})

# New way - repository pattern
stock_repo = StockDataRepository()
data = stock_repo.get_stock_data("AAPL")
```

### From Individual Repositories
```python
# Old way - individual repositories
stock_repo = StockDataRepository()
financial_repo = FinancialDataRepository()
company_repo = CompanyInfoRepository()

stock_data = stock_repo.get_stock_data("AAPL")
financial_data = financial_repo.get_financial_data("AAPL")
company_info = company_repo.get_company_info("AAPL")

# New way - unified API
api = DataAccessAPI()
complete_data = api.get_complete_company_data("AAPL")
```