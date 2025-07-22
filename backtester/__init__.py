"""
Stock Trading Backtester Package

A comprehensive backtesting framework for stock trading strategies
with parameter optimization.
"""

__version__ = "1.1.0"
__author__ = "Nishina"

# Optimization and Analytics
from .analytics import AnalyticsEngine
# Main components
from .backtester import Backtester
# Configuration
from .config import ConfigFactory
from .crypto_data_reader import CryptoDataReader
from .data_reader import DataReader
# Core models
from .models import (LotConfig, LotSizeMode, MarketData, Order, OrderAction,
                     OrderType, Trade)
from .optimizer import Optimizer
# Strategies
from .strategy import (BuyAndHoldStrategy, MovingAverageStrategy,
                       RSIAveragingStrategy, RSIStrategy, Strategy)
from .visualization import VisualizationEngine

__all__ = [
    # Core models
    "MarketData",
    "Order",
    "Trade",
    "OrderType",
    "OrderAction",
    "LotConfig",
    "LotSizeMode",
    # Main components
    "Backtester",
    "DataReader",
    "CryptoDataReader",
    # Strategies
    "Strategy",
    "BuyAndHoldStrategy",
    "MovingAverageStrategy",
    "RSIStrategy",
    "RSIAveragingStrategy",
    # Optimization and Analytics
    "Optimizer",
    "AnalyticsEngine",
    "VisualizationEngine",
    # Configuration
    "ConfigFactory",
]