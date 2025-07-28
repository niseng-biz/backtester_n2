"""
Stock Database System

A comprehensive stock data management system that fetches data from Yahoo Finance
and stores it in MongoDB for use with backtesting systems.
"""

__version__ = "1.0.0"
__author__ = "Stock Database Team"

from .config import ConfigManager
from .init import get_system_status, initialize_stock_database
from .logger import setup_logger
from .models.company_info import CompanyInfo
from .models.financial_data import FinancialData
# Import models individually to avoid circular imports
from .models.stock_data import StockData
from .models.validation import DataValidator, ValidationResult

__all__ = [
    "ConfigManager", 
    "setup_logger", 
    "initialize_stock_database", 
    "get_system_status",
    "StockData",
    "FinancialData", 
    "CompanyInfo",
    "DataValidator",
    "ValidationResult"
]
