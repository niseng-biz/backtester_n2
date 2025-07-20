"""
Stock Trading Backtester Package

A comprehensive backtesting framework for stock trading strategies.
"""

__version__ = "1.0.0"
__author__ = "Trading Strategy Team"

from .models import MarketData, Order, OrderAction, OrderType, Trade

__all__ = ["MarketData", "Order", "Trade", "OrderType", "OrderAction"]
