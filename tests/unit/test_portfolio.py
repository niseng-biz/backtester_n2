"""
Unit tests for portfolio management system.
"""

import pytest
from datetime import datetime, timedelta
from backtester.portfolio import Position, PortfolioManager
from backtester.models import Order, Trade, MarketData, OrderType, OrderAction


class TestPosition:
    """Test cases for Position class."""
    
    def test_position_initialization(self):
        """Test position initialization."""
        position = Position("AAPL", 100, 150.0)
        
        assert position.symbol == "AAPL"
        assert position.quantity == 100
        assert position.avg_price == 150.0
        assert position.realized_pnl == 0.0
        assert len(position.trades) == 0
    
    def test_add_buy_trade_to_empty_position(self):
        """Test adding buy trade to empty position."""
        position = Position("AAPL")
        trade = Trade(
            entry_price=100.0, exit_price=100.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        
        position.add_trade(trade, 100.0)
        
        assert position.quantity == 100
        assert position.avg_price == 100.0
        assert len(position.trades) == 1
    
    def test_add_multiple_buy_trades(self):
        """Test adding multiple buy trades (averaging up)."""
        position = Position("AAPL")
        
        # First trade: 100 shares at $100
        trade1 = Trade(
            entry_price=100.0, exit_price=100.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        position.add_trade(trade1, 100.0)
        
        # Second trade: 100 shares at $120
        trade2 = Trade(
            entry_price=120.0, exit_price=120.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        position.add_trade(trade2, 120.0)
        
        assert position.quantity == 200
        assert position.avg_price == 110.0  # (100*100 + 100*120) / 200
    
    def test_partial_sell_from_long_position(self):
        """Test partial sell from long position."""
        position = Position("AAPL", 200, 100.0)
        
        # Sell 100 shares at $110
        sell_trade = Trade(
            entry_price=110.0, exit_price=110.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.SELL, order_type=OrderType.MARKET
        )
        position.add_trade(sell_trade, 110.0)
        
        assert position.quantity == 100  # 200 - 100
        assert position.avg_price == 100.0  # Unchanged for remaining shares
        assert position.realized_pnl == 1000.0  # 100 * (110 - 100)
    
    def test_complete_sell_from_long_position(self):
        """Test complete sell from long position."""
        position = Position("AAPL", 100, 100.0)
        
        # Sell all 100 shares at $110
        sell_trade = Trade(
            entry_price=110.0, exit_price=110.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.SELL, order_type=OrderType.MARKET
        )
        position.add_trade(sell_trade, 110.0)
        
        assert position.quantity == 0
        assert position.realized_pnl == 1000.0  # 100 * (110 - 100)
        assert position.is_flat() is True
    
    def test_unrealized_pnl_long_position(self):
        """Test unrealized P&L calculation for long position."""
        position = Position("AAPL", 100, 100.0)
        
        # Current price is $110
        unrealized_pnl = position.get_unrealized_pnl(110.0)
        assert unrealized_pnl == 1000.0  # 100 * (110 - 100)
        
        # Current price is $90
        unrealized_pnl = position.get_unrealized_pnl(90.0)
        assert unrealized_pnl == -1000.0  # 100 * (90 - 100)
    
    def test_market_value(self):
        """Test market value calculation."""
        position = Position("AAPL", 100, 100.0)
        
        market_value = position.get_market_value(110.0)
        assert market_value == 11000.0  # 100 * 110
    
    def test_is_flat(self):
        """Test flat position detection."""
        position = Position("AAPL")
        assert position.is_flat() is True
        
        position.quantity = 100
        assert position.is_flat() is False
        
        position.quantity = 0
        assert position.is_flat() is True


class TestPortfolioManager:
    """Test cases for PortfolioManager class."""
    
    def test_portfolio_manager_initialization(self):
        """Test portfolio manager initialization."""
        portfolio = PortfolioManager(50000.0)
        
        assert portfolio.initial_capital == 50000.0
        assert portfolio.cash == 50000.0
        assert len(portfolio.positions) == 0
        assert len(portfolio.portfolio_history) == 0
        assert len(portfolio.trade_history) == 0
    
    def test_process_buy_order(self):
        """Test processing buy order."""
        portfolio = PortfolioManager(100000.0)
        
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        
        trade = portfolio.process_order(order, market_data)
        
        assert trade is not None
        assert trade.action == OrderAction.BUY
        assert trade.quantity == 100
        
        # Check portfolio state
        assert len(portfolio.positions) == 1
        assert portfolio.cash < 100000.0  # Cash should decrease
        assert len(portfolio.trade_history) == 1
    
    def test_process_sell_order_insufficient_position(self):
        """Test processing sell order with insufficient position."""
        portfolio = PortfolioManager(100000.0)
        
        # Try to sell without having any position
        order = Order(OrderType.MARKET, OrderAction.SELL, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        
        trade = portfolio.process_order(order, market_data)
        
        # Order should not execute due to insufficient position
        assert trade is None
        assert len(portfolio.positions) == 0
        assert portfolio.cash == 100000.0  # Cash unchanged
    
    def test_get_total_value(self):
        """Test total portfolio value calculation."""
        portfolio = PortfolioManager(100000.0)
        
        # Initially, total value equals cash
        assert portfolio.get_total_value() == 100000.0
        
        # After buying shares, total value includes position value
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        
        portfolio.process_order(order, market_data)
        
        # Total value should be approximately the same (cash + position value)
        current_prices = {"DEFAULT": 100.0}
        total_value = portfolio.get_total_value(current_prices)
        assert abs(total_value - 100000.0) < 1000.0  # Allow for slippage and commission
    
    def test_get_unrealized_pnl(self):
        """Test unrealized P&L calculation."""
        portfolio = PortfolioManager(100000.0)
        
        # Buy shares
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        
        portfolio.process_order(order, market_data)
        
        # Calculate unrealized P&L with higher current price
        current_prices = {"DEFAULT": 110.0}
        unrealized_pnl = portfolio.get_unrealized_pnl(current_prices)
        
        # Should be positive since price increased
        assert unrealized_pnl > 0
    
    def test_record_portfolio_snapshot(self):
        """Test portfolio snapshot recording."""
        portfolio = PortfolioManager(100000.0)
        
        timestamp = datetime.now()
        portfolio.record_portfolio_snapshot(timestamp)
        
        assert len(portfolio.portfolio_history) == 1
        snapshot = portfolio.portfolio_history[0]
        
        assert snapshot['timestamp'] == timestamp
        assert snapshot['total_value'] == 100000.0
        assert snapshot['cash'] == 100000.0
        assert snapshot['num_positions'] == 0
    
    def test_get_performance_metrics(self):
        """Test performance metrics calculation."""
        portfolio = PortfolioManager(100000.0)
        
        # Record initial snapshot
        portfolio.record_portfolio_snapshot(datetime.now())
        
        # Simulate some trading and price changes
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        portfolio.process_order(order, market_data)
        
        # Record another snapshot with higher prices
        current_prices = {"DEFAULT": 110.0}
        portfolio.record_portfolio_snapshot(datetime.now() + timedelta(days=1), current_prices)
        
        metrics = portfolio.get_performance_metrics()
        
        assert 'total_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert 'total_trades' in metrics
        assert metrics['total_trades'] == 1
    
    def test_set_risk_limits(self):
        """Test setting risk limits."""
        portfolio = PortfolioManager()
        
        portfolio.set_risk_limits(max_position_size=0.05, max_total_exposure=0.8)
        
        assert portfolio.max_position_size == 0.05
        assert portfolio.max_total_exposure == 0.8
        
        # Test invalid limits
        with pytest.raises(ValueError, match="Max position size must be between 0 and 1"):
            portfolio.set_risk_limits(max_position_size=1.5)
        
        with pytest.raises(ValueError, match="Max total exposure must be between 0 and 2"):
            portfolio.set_risk_limits(max_total_exposure=3.0)
    
    def test_reset(self):
        """Test portfolio reset."""
        portfolio = PortfolioManager(100000.0)
        
        # Make some trades
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        portfolio.process_order(order, market_data)
        portfolio.record_portfolio_snapshot(datetime.now())
        
        # Verify state before reset
        assert len(portfolio.positions) > 0
        assert len(portfolio.trade_history) > 0
        assert len(portfolio.portfolio_history) > 0
        assert portfolio.cash != portfolio.initial_capital
        
        # Reset
        portfolio.reset()
        
        # Verify state after reset
        assert len(portfolio.positions) == 0
        assert len(portfolio.trade_history) == 0
        assert len(portfolio.portfolio_history) == 0
        assert portfolio.cash == portfolio.initial_capital
    
    def test_get_positions_summary(self):
        """Test positions summary."""
        portfolio = PortfolioManager(100000.0)
        
        # Initially no positions
        summary = portfolio.get_positions_summary()
        assert len(summary) == 0
        
        # After buying shares
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        market_data = MarketData(
            timestamp=datetime.now(),
            open=100.0, high=105.0, low=95.0, close=100.0, volume=1000
        )
        portfolio.process_order(order, market_data)
        
        current_prices = {"DEFAULT": 110.0}
        summary = portfolio.get_positions_summary(current_prices)
        
        assert len(summary) == 1
        position_summary = summary[0]
        
        assert position_summary['symbol'] == "DEFAULT"
        assert position_summary['quantity'] == 100
        assert position_summary['current_price'] == 110.0
        assert 'market_value' in position_summary
        assert 'unrealized_pnl' in position_summary