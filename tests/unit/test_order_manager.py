"""
Unit tests for order management system.
"""

import pytest
from datetime import datetime, timedelta
from backtester.order_manager import OrderManager, AdvancedOrderManager
from backtester.models import Order, Trade, MarketData, OrderType, OrderAction


class TestOrderManager:
    """Test cases for OrderManager class."""
    
    def test_order_manager_initialization(self):
        """Test order manager initialization."""
        manager = OrderManager()
        
        assert len(manager.pending_orders) == 0
        assert len(manager.executed_trades) == 0
        assert len(manager.order_history) == 0
        assert manager.slippage_factor == 0.001
        assert manager.commission_rate == 0.001
    
    def test_add_market_order(self):
        """Test adding market order."""
        manager = OrderManager()
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        
        manager.add_order(order)
        
        assert len(manager.pending_orders) == 1
        assert len(manager.order_history) == 1
        assert manager.pending_orders[0] == order
    
    def test_add_limit_order(self):
        """Test adding limit order."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=50.0)
        
        manager.add_order(order)
        
        assert len(manager.pending_orders) == 1
        assert len(manager.order_history) == 1
        assert manager.pending_orders[0] == order
    
    def test_execute_market_order_buy(self):
        """Test market buy order execution."""
        manager = OrderManager()
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        manager.add_order(order)
        
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=102.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 1
        assert len(manager.pending_orders) == 0
        assert len(manager.executed_trades) == 1
        
        trade = trades[0]
        assert trade.action == OrderAction.BUY
        assert trade.quantity == 100
        assert trade.order_type == OrderType.MARKET
        # Price should include slippage (102.0 * 1.001)
        expected_price = 102.0 * (1 + manager.slippage_factor)
        assert abs(trade.entry_price - expected_price) < 0.01
    
    def test_execute_market_order_sell(self):
        """Test market sell order execution."""
        manager = OrderManager()
        order = Order(OrderType.MARKET, OrderAction.SELL, 100)
        manager.add_order(order)
        
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=102.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 1
        trade = trades[0]
        assert trade.action == OrderAction.SELL
        # Price should include slippage (102.0 * 0.999)
        expected_price = 102.0 * (1 - manager.slippage_factor)
        assert abs(trade.entry_price - expected_price) < 0.01
    
    def test_execute_limit_order_buy_triggered(self):
        """Test limit buy order execution when triggered."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=100.0)
        manager.add_order(order)
        
        # Market data with low price touching limit price
        market_data = MarketData(
            timestamp=datetime.now(),
            open=102.0, high=105.0, low=99.0, close=101.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 1
        assert len(manager.pending_orders) == 0
        
        trade = trades[0]
        assert trade.action == OrderAction.BUY
        assert trade.order_type == OrderType.LIMIT
        # Should execute at limit price or better
        assert trade.entry_price <= 100.0
    
    def test_execute_limit_order_buy_not_triggered(self):
        """Test limit buy order not executed when not triggered."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=95.0)
        manager.add_order(order)
        
        # Market data with low price above limit price
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=98.0, close=102.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 0
        assert len(manager.pending_orders) == 1  # Order still pending
    
    def test_execute_limit_order_sell_triggered(self):
        """Test limit sell order execution when triggered."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.SELL, 100, price=105.0)
        manager.add_order(order)
        
        # Market data with high price reaching limit price
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=106.0, low=98.0, close=102.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 1
        assert len(manager.pending_orders) == 0
        
        trade = trades[0]
        assert trade.action == OrderAction.SELL
        assert trade.order_type == OrderType.LIMIT
        # Should execute at limit price or better
        assert trade.entry_price >= 105.0
    
    def test_execute_limit_order_sell_not_triggered(self):
        """Test limit sell order not executed when not triggered."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.SELL, 100, price=110.0)
        manager.add_order(order)
        
        # Market data with high price below limit price
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=98.0, close=102.0, volume=1000
        )
        
        trades = manager.process_orders(market_data)
        
        assert len(trades) == 0
        assert len(manager.pending_orders) == 1  # Order still pending
    
    def test_set_slippage(self):
        """Test setting slippage factor."""
        manager = OrderManager()
        
        manager.set_slippage(0.002)
        assert manager.slippage_factor == 0.002
        
        # Test invalid slippage
        with pytest.raises(ValueError, match="Slippage factor cannot be negative"):
            manager.set_slippage(-0.001)
    
    def test_set_commission(self):
        """Test setting commission rate."""
        manager = OrderManager()
        
        manager.set_commission(0.005)
        assert manager.commission_rate == 0.005
        
        # Test invalid commission
        with pytest.raises(ValueError, match="Commission rate cannot be negative"):
            manager.set_commission(-0.001)
    
    def test_cancel_order(self):
        """Test order cancellation."""
        manager = OrderManager()
        order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=95.0)
        manager.add_order(order)
        
        assert len(manager.pending_orders) == 1
        
        # Cancel the order
        result = manager.cancel_order(order)
        assert result is True
        assert len(manager.pending_orders) == 0
        
        # Try to cancel non-existent order
        result = manager.cancel_order(order)
        assert result is False
    
    def test_cancel_all_orders(self):
        """Test cancelling all orders."""
        manager = OrderManager()
        
        # Add multiple orders
        for i in range(3):
            order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=95.0 + i)
            manager.add_order(order)
        
        assert len(manager.pending_orders) == 3
        
        # Cancel all orders
        count = manager.cancel_all_orders()
        assert count == 3
        assert len(manager.pending_orders) == 0
    
    def test_get_statistics(self):
        """Test order statistics."""
        manager = OrderManager()
        
        # Add and execute some orders
        buy_order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        sell_order = Order(OrderType.MARKET, OrderAction.SELL, 50)
        limit_order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=95.0)
        
        manager.add_order(buy_order)
        manager.add_order(sell_order)
        manager.add_order(limit_order)  # This will remain pending
        
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=98.0, close=102.0, volume=1000
        )
        
        manager.process_orders(market_data)
        
        stats = manager.get_statistics()
        
        assert stats['total_orders'] == 3
        assert stats['executed_orders'] == 2  # 2 market orders executed
        assert stats['pending_orders'] == 1   # 1 limit order pending
        assert stats['buy_orders'] == 1
        assert stats['sell_orders'] == 1
        assert stats['market_orders'] == 2
        assert stats['limit_orders'] == 0
        assert stats['execution_rate'] == 2/3
    
    def test_reset(self):
        """Test order manager reset."""
        manager = OrderManager()
        
        # Add some orders and execute them
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        manager.add_order(order)
        
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=102.0, volume=1000
        )
        
        manager.process_orders(market_data)
        
        assert len(manager.executed_trades) > 0
        assert len(manager.order_history) > 0
        
        # Reset
        manager.reset()
        
        assert len(manager.pending_orders) == 0
        assert len(manager.executed_trades) == 0
        assert len(manager.order_history) == 0


class TestAdvancedOrderManager:
    """Test cases for AdvancedOrderManager class."""
    
    def test_advanced_order_manager_initialization(self):
        """Test advanced order manager initialization."""
        manager = AdvancedOrderManager()
        
        assert len(manager.stop_loss_orders) == 0
        assert len(manager.take_profit_orders) == 0
        assert len(manager.order_timeout) == 0
    
    def test_add_stop_loss(self):
        """Test adding stop-loss order."""
        manager = AdvancedOrderManager()
        
        manager.add_stop_loss("position_1", 95.0)
        
        assert "position_1" in manager.stop_loss_orders
        assert manager.stop_loss_orders["position_1"] == 95.0
    
    def test_add_take_profit(self):
        """Test adding take-profit order."""
        manager = AdvancedOrderManager()
        
        manager.add_take_profit("position_1", 110.0)
        
        assert "position_1" in manager.take_profit_orders
        assert manager.take_profit_orders["position_1"] == 110.0
    
    def test_add_order_with_timeout(self):
        """Test adding order with timeout."""
        manager = AdvancedOrderManager()
        order = Order(OrderType.LIMIT, OrderAction.BUY, 100, price=95.0)
        
        manager.add_order_with_timeout(order, 60)  # 60 minutes timeout
        
        assert order in manager.order_timeout
        assert len(manager.pending_orders) == 1
        
        # Check that expiry time is set correctly (approximately)
        expiry_time = manager.order_timeout[order]
        expected_expiry = datetime.now() + timedelta(minutes=60)
        time_diff = abs((expiry_time - expected_expiry).total_seconds())
        assert time_diff < 5  # Within 5 seconds tolerance