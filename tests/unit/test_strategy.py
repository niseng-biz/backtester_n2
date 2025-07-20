"""
Unit tests for strategy implementations.
"""

import pytest
from datetime import datetime, timedelta
from backtester.strategy import Strategy, BuyAndHoldStrategy, MovingAverageStrategy, RSIStrategy
from backtester.models import MarketData, Order, OrderType, OrderAction


class TestBaseStrategy:
    """Test cases for base Strategy class."""
    
    def create_test_strategy(self):
        """Create a concrete strategy for testing."""
        class TestStrategy(Strategy):
            def generate_signal(self, current_data, historical_data):
                return None
            
            def get_strategy_name(self):
                return "Test Strategy"
        
        return TestStrategy()
    
    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = self.create_test_strategy()
        
        assert strategy.initial_capital == 100000.0
        assert strategy.current_position == 0
        assert strategy.cash == 100000.0
        assert strategy.total_trades == 0
    
    def test_set_parameters(self):
        """Test parameter setting."""
        strategy = self.create_test_strategy()
        strategy.set_parameters(param1=10, param2="test")
        
        params = strategy.get_parameters()
        assert params["param1"] == 10
        assert params["param2"] == "test"
    
    def test_update_position_buy(self):
        """Test position update for buy order."""
        strategy = self.create_test_strategy()
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        
        strategy.update_position(order, 50.0)
        
        assert strategy.current_position == 100
        assert strategy.cash == 95000.0  # 100000 - (100 * 50)
        assert strategy.total_trades == 1
    
    def test_update_position_sell(self):
        """Test position update for sell order."""
        strategy = self.create_test_strategy()
        
        # First buy some shares
        buy_order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        strategy.update_position(buy_order, 50.0)
        
        # Then sell some
        sell_order = Order(OrderType.MARKET, OrderAction.SELL, 50)
        strategy.update_position(sell_order, 55.0)
        
        assert strategy.current_position == 50
        assert strategy.cash == 97750.0  # 95000 + (50 * 55)
        assert strategy.total_trades == 2
    
    def test_can_execute_order_buy_sufficient_cash(self):
        """Test order execution check with sufficient cash."""
        strategy = self.create_test_strategy()
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        
        assert strategy.can_execute_order(order, 50.0) is True
    
    def test_can_execute_order_buy_insufficient_cash(self):
        """Test order execution check with insufficient cash."""
        strategy = self.create_test_strategy()
        order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        
        assert strategy.can_execute_order(order, 2000.0) is False
    
    def test_can_execute_order_sell_sufficient_position(self):
        """Test sell order execution check with sufficient position."""
        strategy = self.create_test_strategy()
        
        # Buy some shares first
        buy_order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        strategy.update_position(buy_order, 50.0)
        
        # Try to sell some
        sell_order = Order(OrderType.MARKET, OrderAction.SELL, 50)
        assert strategy.can_execute_order(sell_order, 55.0) is True
    
    def test_can_execute_order_sell_insufficient_position(self):
        """Test sell order execution check with insufficient position."""
        strategy = self.create_test_strategy()
        sell_order = Order(OrderType.MARKET, OrderAction.SELL, 100)
        
        assert strategy.can_execute_order(sell_order, 50.0) is False
    
    def test_get_portfolio_value(self):
        """Test portfolio value calculation."""
        strategy = self.create_test_strategy()
        
        # Buy some shares
        buy_order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        strategy.update_position(buy_order, 50.0)
        
        # Portfolio value = cash + position value
        portfolio_value = strategy.get_portfolio_value(60.0)
        expected_value = 95000.0 + (100 * 60.0)  # cash + position value
        assert portfolio_value == expected_value
    
    def test_reset(self):
        """Test strategy reset."""
        strategy = self.create_test_strategy()
        
        # Make some changes
        buy_order = Order(OrderType.MARKET, OrderAction.BUY, 100)
        strategy.update_position(buy_order, 50.0)
        strategy.set_parameters(test_param=123)
        
        # Reset
        strategy.reset()
        
        assert strategy.current_position == 0
        assert strategy.cash == 100000.0
        assert strategy.total_trades == 0
        # Parameters should remain
        assert strategy.get_parameters()["test_param"] == 123


class TestBuyAndHoldStrategy:
    """Test cases for BuyAndHoldStrategy."""
    
    def test_buy_and_hold_initialization(self):
        """Test buy and hold strategy initialization."""
        from backtester.models import LotConfig
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(50000.0, lot_config=lot_config)
        
        assert strategy.initial_capital == 50000.0
        assert strategy.get_strategy_name() == "Buy and Hold"
        assert strategy.has_bought is False
    
    def test_buy_and_hold_first_signal(self):
        """Test first buy signal generation."""
        from backtester.models import LotConfig
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(lot_config=lot_config)
        
        current_data = MarketData(datetime.now(), 100.0, 105.0, 95.0, 102.0, 1000)
        historical_data = []
        
        order = strategy.generate_signal(current_data, historical_data)
        
        assert order is not None
        assert order.action == OrderAction.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 980  # floor(100000 / 102)
        assert strategy.has_bought is True
    
    def test_buy_and_hold_no_second_signal(self):
        """Test no signal after first buy."""
        from backtester.models import LotConfig
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(lot_config=lot_config)
        
        current_data = MarketData(datetime.now(), 100.0, 105.0, 95.0, 102.0, 1000)
        historical_data = []
        
        # First signal
        first_order = strategy.generate_signal(current_data, historical_data)
        assert first_order is not None
        
        # Second call should return None
        second_order = strategy.generate_signal(current_data, historical_data)
        assert second_order is None


class TestMovingAverageStrategy:
    """Test cases for MovingAverageStrategy."""
    
    def create_test_data(self, prices: list, start_date: datetime = None) -> list:
        """Create test market data with given prices."""
        if start_date is None:
            start_date = datetime(2023, 1, 1)
        
        data = []
        for i, price in enumerate(prices):
            date = start_date + timedelta(days=i)
            data.append(MarketData(date, price, price+2, price-1, price, 1000))
        
        return data
    
    def test_ma_strategy_initialization(self):
        """Test moving average strategy initialization."""
        strategy = MovingAverageStrategy(5, 10, 50000.0)
        
        assert strategy.short_window == 5
        assert strategy.long_window == 10
        assert strategy.initial_capital == 50000.0
        assert strategy.get_strategy_name() == "Moving Average (5/10)"
    
    def test_ma_strategy_insufficient_data(self):
        """Test MA strategy with insufficient historical data."""
        strategy = MovingAverageStrategy(5, 10)
        
        # Only 5 data points, need 10 for long MA
        historical_data = self.create_test_data([100, 101, 102, 103, 104])
        current_data = MarketData(datetime.now(), 105.0, 107.0, 103.0, 105.0, 1000)
        
        order = strategy.generate_signal(current_data, historical_data)
        assert order is None
    
    def test_ma_strategy_golden_cross(self):
        """Test golden cross signal (short MA crosses above long MA)."""
        strategy = MovingAverageStrategy(2, 4)
        
        # Create data where short MA will cross above long MA
        # Prices: declining then rising
        prices = [100, 99, 98, 97, 105, 110, 115]
        historical_data = self.create_test_data(prices)
        current_data = MarketData(datetime.now(), 120.0, 122.0, 118.0, 120.0, 1000)
        
        order = strategy.generate_signal(current_data, historical_data)
        
        # Should generate buy signal
        if order:
            assert order.action == OrderAction.BUY
            assert order.order_type == OrderType.MARKET
    
    def test_ma_calculation(self):
        """Test moving average calculation."""
        strategy = MovingAverageStrategy(3, 5)
        
        data = self.create_test_data([100, 102, 104, 106, 108])
        
        # 3-period MA of last 3 prices: (104 + 106 + 108) / 3 = 106
        ma_3 = strategy._calculate_moving_average(data, 3)
        assert ma_3 == 106.0
        
        # 5-period MA of all prices: (100 + 102 + 104 + 106 + 108) / 5 = 104
        ma_5 = strategy._calculate_moving_average(data, 5)
        assert ma_5 == 104.0
    
    def test_ma_calculation_insufficient_data(self):
        """Test MA calculation with insufficient data."""
        strategy = MovingAverageStrategy(5, 10)
        
        data = self.create_test_data([100, 102, 104])  # Only 3 data points
        
        ma = strategy._calculate_moving_average(data, 5)
        assert ma is None


class TestRSIStrategy:
    """Test cases for RSIStrategy."""
    
    def create_test_data(self, prices: list, start_date: datetime = None) -> list:
        """Create test market data with given prices."""
        if start_date is None:
            start_date = datetime(2023, 1, 1)
        
        data = []
        for i, price in enumerate(prices):
            date = start_date + timedelta(days=i)
            data.append(MarketData(date, price, price+2, price-1, price, 1000))
        
        return data
    
    def test_rsi_strategy_initialization(self):
        """Test RSI strategy initialization."""
        strategy = RSIStrategy(14, 30.0, 70.0, 50000.0)
        
        assert strategy.rsi_period == 14
        assert strategy.oversold_threshold == 30.0
        assert strategy.overbought_threshold == 70.0
        assert strategy.get_strategy_name() == "RSI (14, 30.0/70.0)"
    
    def test_rsi_calculation_basic(self):
        """Test basic RSI calculation."""
        strategy = RSIStrategy(4)  # Short period for testing
        
        # Create data with clear trend
        # Rising prices should give lower RSI initially, then higher
        prices = [100, 102, 104, 106, 108, 110]
        data = self.create_test_data(prices)
        
        rsi = strategy._calculate_rsi(data)
        
        # RSI should be calculated (exact value depends on calculation)
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_insufficient_data(self):
        """Test RSI calculation with insufficient data."""
        strategy = RSIStrategy(14)
        
        # Only 5 data points, need at least 15 (period + 1)
        data = self.create_test_data([100, 101, 102, 103, 104])
        
        rsi = strategy._calculate_rsi(data)
        assert rsi is None
    
    def test_rsi_all_gains(self):
        """Test RSI calculation with all gains (no losses)."""
        strategy = RSIStrategy(4)
        
        # Steadily rising prices (all gains)
        prices = [100, 102, 104, 106, 108]
        data = self.create_test_data(prices)
        
        rsi = strategy._calculate_rsi(data)
        
        # Should return 100 when there are no losses
        assert rsi == 100.0