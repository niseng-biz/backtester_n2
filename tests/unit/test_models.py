"""
Unit tests for core data models.
"""

from datetime import datetime

import pytest

from backtester.models import MarketData, Order, OrderAction, OrderType, Trade


class TestMarketData:
    """Test cases for MarketData class."""
    
    def test_valid_market_data(self):
        """Test creation of valid market data."""
        data = MarketData(
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000
        )
        assert data.open == 100.0
        assert data.high == 105.0
        assert data.low == 95.0
        assert data.close == 102.0
        assert data.volume == 1000
    
    def test_invalid_high_price(self):
        """Test validation of high price."""
        with pytest.raises(ValueError, match="High price .* cannot be lower"):
            MarketData(
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=95.0,  # Invalid: high < open
                low=90.0,
                close=98.0,
                volume=1000
            )
    
    def test_invalid_low_price(self):
        """Test validation of low price."""
        with pytest.raises(ValueError, match="Low price .* cannot be higher"):
            MarketData(
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=102.0,  # Invalid: low > close
                close=98.0,
                volume=1000
            )
    
    def test_negative_prices(self):
        """Test validation of negative prices."""
        with pytest.raises(ValueError, match="Prices cannot be negative"):
            MarketData(
                timestamp=datetime(2023, 1, 1),
                open=-100.0,  # Invalid: negative price
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000
            )
    
    def test_negative_volume(self):
        """Test validation of negative volume."""
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            MarketData(
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=-1000  # Invalid: negative volume
            )


class TestOrder:
    """Test cases for Order class."""
    
    def test_valid_market_order(self):
        """Test creation of valid market order."""
        order = Order(
            order_type=OrderType.MARKET,
            action=OrderAction.BUY,
            quantity=100
        )
        assert order.order_type == OrderType.MARKET
        assert order.action == OrderAction.BUY
        assert order.quantity == 100
        assert order.price is None
    
    def test_valid_limit_order(self):
        """Test creation of valid limit order."""
        order = Order(
            order_type=OrderType.LIMIT,
            action=OrderAction.SELL,
            quantity=50,
            price=105.0
        )
        assert order.order_type == OrderType.LIMIT
        assert order.action == OrderAction.SELL
        assert order.quantity == 50
        assert order.price == 105.0
    
    def test_invalid_quantity(self):
        """Test validation of order quantity."""
        with pytest.raises(ValueError, match="Order quantity must be positive"):
            Order(
                order_type=OrderType.MARKET,
                action=OrderAction.BUY,
                quantity=0  # Invalid: zero quantity
            )
    
    def test_limit_order_without_price(self):
        """Test validation of limit order without price."""
        with pytest.raises(ValueError, match="Limit orders must specify a price"):
            Order(
                order_type=OrderType.LIMIT,
                action=OrderAction.BUY,
                quantity=100
                # Missing price for limit order
            )
    
    def test_market_order_with_price(self):
        """Test validation of market order with price."""
        with pytest.raises(ValueError, match="Market orders should not specify a price"):
            Order(
                order_type=OrderType.MARKET,
                action=OrderAction.BUY,
                quantity=100,
                price=100.0  # Invalid: market order with price
            )


class TestTrade:
    """Test cases for Trade class."""
    
    def test_profitable_long_trade(self):
        """Test profitable long trade calculation."""
        trade = Trade(
            entry_price=100.0,
            exit_price=110.0,
            quantity=100,
            entry_time=datetime(2023, 1, 1),
            exit_time=datetime(2023, 1, 2),
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        assert trade.pnl == 1000.0  # (110 - 100) * 100
        assert trade.return_percentage == 10.0
        assert trade.is_profitable is True
    
    def test_losing_long_trade(self):
        """Test losing long trade calculation."""
        trade = Trade(
            entry_price=100.0,
            exit_price=90.0,
            quantity=100,
            entry_time=datetime(2023, 1, 1),
            exit_time=datetime(2023, 1, 2),
            action=OrderAction.BUY,
            order_type=OrderType.MARKET
        )
        assert trade.pnl == -1000.0  # (90 - 100) * 100
        assert trade.return_percentage == -10.0
        assert trade.is_profitable is False
    
    def test_profitable_short_trade(self):
        """Test profitable short trade calculation."""
        trade = Trade(
            entry_price=100.0,
            exit_price=90.0,
            quantity=100,
            entry_time=datetime(2023, 1, 1),
            exit_time=datetime(2023, 1, 2),
            action=OrderAction.SELL,
            order_type=OrderType.MARKET
        )
        assert trade.pnl == 1000.0  # (100 - 90) * 100
        assert trade.return_percentage == 10.0
        assert trade.is_profitable is True