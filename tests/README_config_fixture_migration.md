# Configuration Manager Fixture Migration Guide

This document explains how to migrate from using `get_config_manager()` directly to using the unified test fixtures.

## Before and After Patterns

### Pattern 1: Basic Config Manager Usage

**Before:**
```python
from stock_database.config import get_config_manager

def test_something():
    config = get_config_manager()
    # Use config...
```

**After:**
```python
def test_something(config_manager):
    # config_manager is automatically provided by fixture
    # Use config_manager...
```

### Pattern 2: Database Manager Creation

**Before:**
```python
from stock_database.config import get_config_manager
from stock_database.database_factory import DatabaseManager

def test_database_operation():
    config = get_config_manager()
    db_manager = DatabaseManager(config)
    db_manager.connect()
    # Use db_manager...
    db_manager.disconnect()
```

**After:**
```python
def test_database_operation(database_manager):
    # database_manager is automatically provided and cleaned up
    database_manager.connect()
    # Use database_manager...
    # No need to disconnect - fixture handles cleanup
```

### Pattern 3: SQLite Manager Creation

**Before:**
```python
from stock_database.config import get_config_manager
from stock_database.sqlite_database import SQLiteManager

def test_sqlite_operation():
    config = get_config_manager()
    db_manager = SQLiteManager(config)
    db_manager.connect()
    # Use db_manager...
    db_manager.disconnect()
```

**After:**
```python
def test_sqlite_operation(sqlite_db_manager):
    # sqlite_db_manager is automatically provided and cleaned up
    sqlite_db_manager.connect()
    # Use sqlite_db_manager...
    # No need to disconnect - fixture handles cleanup
```

## Available Fixtures

The following fixtures are available in `tests/conftest.py`:

### `config_manager`
- Provides a ConfigManager instance
- Equivalent to calling `get_config_manager()`
- No cleanup needed

### `database_manager`
- Provides a DatabaseManager instance with config already injected
- Automatically handles cleanup/disconnection
- Use this instead of creating DatabaseManager manually

### `sqlite_db_manager`
- Provides a SQLiteManager instance with config already injected
- Automatically handles cleanup/disconnection
- Use this instead of creating SQLiteManager manually

## Migration Steps

1. **Remove direct imports**: Remove `from stock_database.config import get_config_manager`
2. **Add fixture parameter**: Add the appropriate fixture as a function parameter
3. **Remove manual creation**: Remove manual config/manager creation code
4. **Remove cleanup code**: Remove manual disconnect/cleanup code (fixtures handle this)
5. **Update variable names**: Use the fixture parameter name instead of local variables

## Example Migration

**Original standalone script:**
```python
def test_company_info_insertion():
    try:
        # Create company info
        company_info = CompanyInfo(...)
        
        # Initialize database manager
        config = get_config_manager()
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Insert company info
        db_manager.upsert_company_info([company_info])
        
        # Test retrieval
        data_api = DataAccessAPI()
        retrieved_info = data_api.get_company_info("AAPL")
        
        assert retrieved_info is not None
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
```

**Migrated pytest test:**
```python
def test_company_info_insertion(database_manager):
    # Create company info
    company_info = CompanyInfo(...)
    
    # Use provided database manager
    database_manager.connect()
    
    # Insert company info
    database_manager.upsert_company_info([company_info])
    
    # Test retrieval
    data_api = DataAccessAPI()
    retrieved_info = data_api.get_company_info("AAPL")
    
    assert retrieved_info is not None
    # No need to disconnect - fixture handles cleanup
```

## Benefits of Using Fixtures

1. **Consistency**: All tests use the same configuration setup pattern
2. **Cleanup**: Automatic resource cleanup prevents test interference
3. **Reusability**: Common setup code is centralized in conftest.py
4. **Maintainability**: Changes to setup logic only need to be made in one place
5. **Reliability**: Proper cleanup ensures tests don't affect each other

## Converting Standalone Scripts

Many of the current test files are standalone scripts rather than proper pytest tests. To convert them:

1. **Change function signatures**: Convert `def test_something():` to `def test_something(fixture_name):`
2. **Remove main() functions**: Remove the `if __name__ == "__main__":` blocks
3. **Use assertions**: Replace manual success/failure tracking with pytest assertions
4. **Remove try/catch blocks**: Let pytest handle exceptions naturally
5. **Use fixtures**: Replace manual setup with fixture parameters

This migration improves test reliability and maintainability while reducing code duplication.