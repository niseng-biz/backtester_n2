"""
Base strategy framework for implementing trading strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

import numpy as np

try:
    import talib

    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ Warning: TA-Lib not available. Using fallback RSI calculation.")

from .models import MarketData, Order, OrderType, OrderAction, LotConfig


class Strategy(ABC):
    """Abstract base class for trading strategies with LOT support."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        name: str = "BaseStrategy",
        lot_config: Optional[LotConfig] = None,
    ):
        """
        Initialize strategy with capital and configuration.

        Args:
            initial_capital: Starting capital for the strategy
            name: Name identifier for the strategy
            lot_config: LOT configuration for position sizing
        """
        self.initial_capital = initial_capital
        self.name = name
        self.current_position = 0.0  # Current position size (supports fractional)
        self.cash = initial_capital
        self.total_value = initial_capital
        self.trade_history = []
        self.parameters = {}

        # LOT configuration
        self.lot_config = lot_config or LotConfig()

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    @abstractmethod
    def generate_signal(
        self, current_data: MarketData, historical_data: List[MarketData]
    ) -> Optional[Order]:
        """
        Generate trading signal based on current and historical market data.

        Args:
            current_data: Current market data point
            historical_data: List of historical market data (chronologically ordered)

        Returns:
            Order object if signal is generated, None otherwise
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        pass

    def set_parameters(self, **kwargs) -> None:
        """
        Set strategy parameters.

        Args:
            **kwargs: Strategy-specific parameters
        """
        self.parameters.update(kwargs)

    def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters."""
        return self.parameters.copy()

    def update_position(self, order: Order, execution_price: float) -> None:
        """
        Update position and cash after order execution.

        Args:
            order: Executed order
            execution_price: Price at which order was executed
        """
        if order.action == OrderAction.BUY:
            # Buying increases position, decreases cash
            cost = order.quantity * execution_price
            if cost <= self.cash:
                self.current_position += order.quantity
                self.cash -= cost
                self.total_trades += 1
        else:
            # Selling decreases position, increases cash
            if order.quantity <= self.current_position:
                proceeds = order.quantity * execution_price
                self.current_position -= order.quantity
                self.cash += proceeds
                self.total_trades += 1

    def can_execute_order(self, order: Order, current_price: float) -> bool:
        """
        Check if order can be executed given current position and cash.

        Args:
            order: Order to check
            current_price: Current market price

        Returns:
            True if order can be executed, False otherwise
        """
        if order.action == OrderAction.BUY:
            # Check if we have enough cash
            required_cash = order.quantity * current_price
            return required_cash <= self.cash
        else:
            # Check if we have enough position to sell
            return order.quantity <= self.current_position

    def get_portfolio_value(self, current_price: float) -> float:
        """
        Calculate total portfolio value.

        Args:
            current_price: Current market price

        Returns:
            Total portfolio value (cash + position value)
        """
        position_value = self.current_position * current_price
        return self.cash + position_value

    def get_position_info(self) -> Dict[str, Any]:
        """
        Get current position information.

        Returns:
            Dictionary with position details
        """
        return {
            "position_size": self.current_position,
            "cash": self.cash,
            "total_value": self.total_value,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
        }

    def calculate_lot_size(
        self, available_cash: float, current_price: float, target_lots: float = 1.0
    ) -> float:
        """
        Calculate actual lot size based on available cash and target lots.
        Uses LotConfig's calculate_lot_size method which supports both FIXED and VARIABLE modes.

        Args:
            available_cash: Available cash for the trade
            current_price: Current market price
            target_lots: Target number of lots to trade (used in FIXED mode)

        Returns:
            Actual lot size that can be traded
        """
        # Calculate total portfolio value (cash + current position value)
        total_portfolio_value = self.get_portfolio_value(current_price)

        return self.lot_config.calculate_lot_size(
            available_cash, current_price, target_lots, total_portfolio_value
        )

    def create_lot_order(
        self,
        action: OrderAction,
        lots: float,
        current_price: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        position_id: Optional[str] = None,
    ) -> Optional[Order]:
        """
        Create an order using LOT-based sizing.

        Args:
            action: Buy or sell action
            lots: Number of lots to trade
            current_price: Current market price
            order_type: Market or limit order
            limit_price: Price for limit orders
            position_id: Position identifier

        Returns:
            Order object or None if invalid
        """
        if lots <= 0:
            return None

        # Validate lot size
        if not self.lot_config.validate_lot_size(lots):
            lots = self.lot_config.round_lot_size(lots)

        return Order.create_lot_order(
            order_type=order_type,
            action=action,
            lots=lots,
            lot_size=self.lot_config.base_lot_size,
            price=limit_price,
            position_id=position_id,
        )

    def reset(self) -> None:
        """Reset strategy to initial state."""
        self.current_position = 0
        self.cash = self.initial_capital
        self.total_value = self.initial_capital
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0


class BuyAndHoldStrategy(Strategy):
    """Simple buy-and-hold strategy for benchmarking."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        lot_config: Optional[LotConfig] = None,
        position_lots: float = 1.0,
    ):
        """
        Initialize buy-and-hold strategy.

        Args:
            initial_capital: Starting capital
            lot_config: LOT configuration for position sizing
            position_lots: Number of lots to trade (used in FIXED mode)
        """
        super().__init__(initial_capital, "BuyAndHold", lot_config)
        self.has_bought = False
        self.position_lots = position_lots
        self.set_parameters(position_lots=position_lots)

    def generate_signal(
        self, current_data: MarketData, historical_data: List[MarketData]
    ) -> Optional[Order]:
        """
        Generate buy signal on first data point only.

        Args:
            current_data: Current market data
            historical_data: Historical market data

        Returns:
            Buy order on first call, None afterwards
        """
        if not self.has_bought and self.cash > 0:
            # Calculate lot size based on available cash and target lots
            actual_lots = self.calculate_lot_size(
                self.cash, current_data.close, self.position_lots
            )

            if actual_lots > 0:
                self.has_bought = True
                return self.create_lot_order(
                    action=OrderAction.BUY,
                    lots=actual_lots,
                    current_price=current_data.close,
                )
        return None

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "Buy and Hold"

    def reset(self) -> None:
        """Reset strategy state."""
        super().reset()
        self.has_bought = False


class MovingAverageStrategy(Strategy):
    """Moving average crossover strategy."""

    def __init__(
        self,
        short_window: int = 10,
        long_window: int = 30,
        initial_capital: float = 100000.0,
        lot_config: Optional[LotConfig] = None,
        position_lots: float = 1.0,
    ):
        """
        Initialize moving average strategy.

        Args:
            short_window: Period for short moving average
            long_window: Period for long moving average
            initial_capital: Starting capital
            lot_config: LOT configuration for position sizing
            position_lots: Number of lots to trade per signal
        """
        super().__init__(initial_capital, "MovingAverage", lot_config)
        self.short_window = short_window
        self.long_window = long_window
        self.position_lots = position_lots
        self.set_parameters(
            short_window=short_window,
            long_window=long_window,
            position_lots=position_lots,
        )

        # Track previous signals to avoid repeated signals
        self.last_signal = None

    def generate_signal(
        self, current_data: MarketData, historical_data: List[MarketData]
    ) -> Optional[Order]:
        """
        Generate signal based on moving average crossover.

        Args:
            current_data: Current market data
            historical_data: Historical market data

        Returns:
            Order if crossover detected, None otherwise
        """
        # Need enough historical data for long MA
        if len(historical_data) < self.long_window - 1:
            return None

        # Include current data for MA calculation
        all_data = historical_data + [current_data]

        # Calculate moving averages
        short_ma = self._calculate_moving_average(all_data, self.short_window)
        long_ma = self._calculate_moving_average(all_data, self.long_window)

        if short_ma is None or long_ma is None:
            return None

        # Simple strategy: buy when short MA > long MA and we have no position
        # Sell when short MA < long MA and we have a position
        current_signal = None

        if short_ma > long_ma and self.current_position == 0:
            current_signal = OrderAction.BUY
        elif short_ma < long_ma and self.current_position > 0:
            current_signal = OrderAction.SELL

        # Generate order if signal detected and different from last signal
        if current_signal and current_signal != self.last_signal:
            self.last_signal = current_signal

            if current_signal == OrderAction.BUY and self.cash > 0:
                # Calculate lot size based on available cash and target lots
                actual_lots = self.calculate_lot_size(
                    self.cash, current_data.close, self.position_lots
                )

                if actual_lots > 0:
                    return self.create_lot_order(
                        action=OrderAction.BUY,
                        lots=actual_lots,
                        current_price=current_data.close,
                    )

            elif current_signal == OrderAction.SELL and self.current_position > 0:
                # Convert current position to lots for selling
                current_lots = self.lot_config.units_to_lots(self.current_position)

                if current_lots > 0:
                    return self.create_lot_order(
                        action=OrderAction.SELL,
                        lots=current_lots,
                        current_price=current_data.close,
                    )

        return None

    def get_strategy_name(self) -> str:
        """Return strategy name with parameters."""
        return f"Moving Average ({self.short_window}/{self.long_window})"

    def _calculate_moving_average(
        self, data: List[MarketData], window: int
    ) -> Optional[float]:
        """
        Calculate simple moving average.

        Args:
            data: Market data list
            window: Moving average window

        Returns:
            Moving average value or None if insufficient data
        """
        if len(data) < window:
            return None

        # Use closing prices for MA calculation
        prices = [d.close for d in data[-window:]]
        return sum(prices) / len(prices)

    def reset(self) -> None:
        """Reset strategy state."""
        super().reset()
        self.last_signal = None


class RSIStrategy(Strategy):
    """RSI-based trading strategy."""

    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
        initial_capital: float = 100000.0,
    ):
        """
        Initialize RSI strategy.

        Args:
            rsi_period: Period for RSI calculation
            oversold_threshold: RSI level considered oversold (buy signal)
            overbought_threshold: RSI level considered overbought (sell signal)
            initial_capital: Starting capital
        """
        super().__init__(initial_capital, "RSI")
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.set_parameters(
            rsi_period=rsi_period,
            oversold_threshold=oversold_threshold,
            overbought_threshold=overbought_threshold,
        )

        self.last_signal = None

    def generate_signal(
        self, current_data: MarketData, historical_data: List[MarketData]
    ) -> Optional[Order]:
        """
        Generate signal based on RSI levels.

        Args:
            current_data: Current market data
            historical_data: Historical market data

        Returns:
            Order if RSI signal detected, None otherwise
        """
        # Need enough data for RSI calculation
        if len(historical_data) < self.rsi_period + 1:
            return None

        rsi = self._calculate_rsi(historical_data)
        if rsi is None:
            return None

        current_signal = None

        # Oversold condition - buy signal
        if rsi < self.oversold_threshold:
            current_signal = OrderAction.BUY

        # Overbought condition - sell signal
        elif rsi > self.overbought_threshold:
            current_signal = OrderAction.SELL

        # Generate order if signal changed
        if current_signal and current_signal != self.last_signal:
            self.last_signal = current_signal

            if current_signal == OrderAction.BUY and self.cash > 0:
                max_shares = int(self.cash / current_data.close)
                if max_shares > 0:
                    return Order(
                        order_type=OrderType.MARKET,
                        action=OrderAction.BUY,
                        quantity=max_shares,
                        timestamp=current_data.timestamp,
                    )

            elif current_signal == OrderAction.SELL and self.current_position > 0:
                return Order(
                    order_type=OrderType.MARKET,
                    action=OrderAction.SELL,
                    quantity=self.current_position,
                    timestamp=current_data.timestamp,
                )

        return None

    def get_strategy_name(self) -> str:
        """Return strategy name with parameters."""
        return f"RSI ({self.rsi_period}, {self.oversold_threshold}/{self.overbought_threshold})"

    def _calculate_rsi(self, data: List[MarketData]) -> Optional[float]:
        """
        Calculate RSI using TA-Lib for accuracy.

        Args:
            data: Market data list

        Returns:
            RSI value or None if insufficient data
        """
        if len(data) < self.rsi_period + 1:
            return None

        if TALIB_AVAILABLE:
            # Use TA-Lib for accurate RSI calculation
            close_prices = np.array([d.close for d in data], dtype=np.float64)
            rsi_values = talib.RSI(close_prices, timeperiod=self.rsi_period)

            # Return the most recent RSI value
            if len(rsi_values) > 0 and not np.isnan(rsi_values[-1]):
                return float(rsi_values[-1])
            else:
                return None
        else:
            # Fallback to custom implementation
            return self._calculate_rsi_fallback(data)

    def _calculate_rsi_fallback(self, data: List[MarketData]) -> Optional[float]:
        """
        Fallback RSI calculation when TA-Lib is not available.

        Args:
            data: Market data list

        Returns:
            RSI value or None if insufficient data
        """
        if len(data) < self.rsi_period + 1:
            return None

        # Calculate price changes
        price_changes = []
        for i in range(1, len(data)):
            change = data[i].close - data[i - 1].close
            price_changes.append(change)

        # Need at least rsi_period changes
        if len(price_changes) < self.rsi_period:
            return None

        # Calculate average gains and losses
        recent_changes = price_changes[-self.rsi_period :]
        gains = [change for change in recent_changes if change > 0]
        losses = [abs(change) for change in recent_changes if change < 0]

        avg_gain = sum(gains) / self.rsi_period if gains else 0
        avg_loss = sum(losses) / self.rsi_period if losses else 0

        if avg_loss == 0:
            return 100.0  # No losses, RSI = 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def reset(self) -> None:
        """Reset strategy state."""
        super().reset()
        self.last_signal = None


class RSIAveragingStrategy(Strategy):
    """RSI-based dollar-cost averaging strategy with multiple positions using crossover signals."""

    def __init__(
        self,
        rsi_period: int = 14,
        entry_levels: List[float] = None,
        exit_level: float = 70.0,
        position_size_pct: float = 0.2,
        max_positions: int = 5,
        initial_capital: float = 100000.0,
        lot_config: Optional[LotConfig] = None,
        position_lots: float = 0.2,
    ):
        """
        Initialize RSI averaging strategy with crossover logic and LOT support.

        Args:
            rsi_period: Period for RSI calculation
            entry_levels: RSI levels for opening positions (default: [20, 25, 30, 35, 40])
            exit_level: RSI level for closing all positions (default: 70)
            position_size_pct: Percentage of capital per position (deprecated, use position_lots)
            max_positions: Maximum number of positions
            initial_capital: Starting capital
            lot_config: LOT configuration for position sizing
            position_lots: Number of lots per position (replaces position_size_pct)
        """
        super().__init__(initial_capital, "RSIAveraging", lot_config)
        self.rsi_period = rsi_period
        self.entry_levels = entry_levels or [20, 25, 30, 35, 40]
        self.exit_level = exit_level
        self.position_size_pct = position_size_pct  # Keep for backward compatibility
        self.position_lots = position_lots
        self.max_positions = max_positions

        # Track RSI values for crossover detection
        self.current_rsi = None
        self.previous_rsi = None

        # Track positions and entry levels
        self.open_positions = (
            {}
        )  # position_id -> {'quantity': int, 'entry_level': float}
        self.used_entry_levels = set()  # Track which entry levels have been used

        self.set_parameters(
            rsi_period=rsi_period,
            entry_levels=self.entry_levels,
            exit_level=exit_level,
            position_size_pct=position_size_pct,
            max_positions=max_positions,
        )

    def generate_signal(
        self, current_data: MarketData, historical_data: List[MarketData]
    ) -> Optional[Order]:
        """
        Generate signal based on RSI crossover levels for dollar-cost averaging.

        Entry: Previous RSI >= threshold AND Current RSI < threshold (crossover down)
        Exit: Previous RSI >= 70 AND Current RSI < 70 (crossover down)

        Args:
            current_data: Current market data
            historical_data: Historical market data

        Returns:
            Order if RSI crossover signal detected, None otherwise
        """
        # Need enough data for RSI calculation
        if (
            len(historical_data) < self.rsi_period + 2
        ):  # Need extra data for previous RSI
            return None

        # Calculate current RSI
        all_data = historical_data + [current_data]
        current_rsi = self._calculate_rsi(all_data)
        if current_rsi is None:
            return None

        # Calculate previous RSI
        previous_data = historical_data
        previous_rsi = self._calculate_rsi(previous_data)
        if previous_rsi is None:
            return None

        # Update RSI tracking
        self.current_rsi = current_rsi
        self.previous_rsi = previous_rsi

        # Check for exit signal (crossover down from 70)
        if (
            previous_rsi >= self.exit_level
            and current_rsi < self.exit_level
            and len(self.open_positions) > 0
        ):

            # Get the first open position to close
            position_id = next(iter(self.open_positions))
            position_info = self.open_positions[position_id]
            quantity = position_info["quantity"]

            # Remove this position from tracking
            del self.open_positions[position_id]

            # Remove the used entry level so it can be used again
            if "entry_level" in position_info:
                self.used_entry_levels.discard(position_info["entry_level"])

            # Create sell order for this specific position
            return Order(
                order_type=OrderType.MARKET,
                action=OrderAction.SELL,
                quantity=quantity,
                timestamp=current_data.timestamp,
                position_id=position_id,
            )

        # Check for entry signals (crossover down from entry levels)
        for entry_level in self.entry_levels:
            # Check crossover condition: previous >= level AND current < level
            if (
                previous_rsi >= entry_level
                and current_rsi < entry_level
                and entry_level not in self.used_entry_levels
                and len(self.open_positions) < self.max_positions
            ):

                # Calculate lot size based on available cash and target lots
                actual_lots = self.calculate_lot_size(
                    self.cash, current_data.close, self.position_lots
                )

                if actual_lots > 0:
                    # Create unique position ID
                    position_id = f"rsi_pos_{len(self.open_positions) + 1}_{current_data.timestamp.strftime('%Y%m%d_%H%M%S')}"

                    # Convert lots to actual quantity for tracking
                    actual_quantity = self.lot_config.lot_to_units(actual_lots)

                    # Track this position
                    self.open_positions[position_id] = {
                        "quantity": actual_quantity,
                        "lots": actual_lots,
                        "entry_level": entry_level,
                    }
                    self.used_entry_levels.add(entry_level)

                    # Create LOT-based order
                    return self.create_lot_order(
                        action=OrderAction.BUY,
                        lots=actual_lots,
                        current_price=current_data.close,
                        position_id=position_id,
                    )

        return None

    def get_strategy_name(self) -> str:
        """Return strategy name with parameters."""
        levels_str = "/".join(map(str, self.entry_levels))
        return f"RSI Averaging ({self.rsi_period}, {levels_str}, {self.exit_level})"

    def _calculate_rsi(self, data: List[MarketData]) -> Optional[float]:
        """
        Calculate RSI using TA-Lib for accuracy.

        Args:
            data: Market data list

        Returns:
            RSI value or None if insufficient data
        """
        if len(data) < self.rsi_period + 1:
            return None

        if TALIB_AVAILABLE:
            # Use TA-Lib for accurate RSI calculation
            close_prices = np.array([d.close for d in data], dtype=np.float64)
            rsi_values = talib.RSI(close_prices, timeperiod=self.rsi_period)

            # Return the most recent RSI value
            if len(rsi_values) > 0 and not np.isnan(rsi_values[-1]):
                return float(rsi_values[-1])
            else:
                return None
        else:
            # Fallback to Wilder's smoothing method
            return self._calculate_rsi_fallback(data)

    def _calculate_rsi_fallback(self, data: List[MarketData]) -> Optional[float]:
        """
        Fallback RSI calculation using Wilder's smoothing method when TA-Lib is not available.

        Args:
            data: Market data list

        Returns:
            RSI value or None if insufficient data
        """
        if len(data) < self.rsi_period + 1:
            return None

        # Calculate price changes
        price_changes = []
        for i in range(1, len(data)):
            change = data[i].close - data[i - 1].close
            price_changes.append(change)

        if len(price_changes) < self.rsi_period:
            return None

        # Calculate initial average gain and loss
        initial_changes = price_changes[-self.rsi_period :]
        gains = [max(0, change) for change in initial_changes]
        losses = [abs(min(0, change)) for change in initial_changes]

        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period

        # For more data points, use Wilder's smoothing
        if len(price_changes) > self.rsi_period:
            for change in price_changes[self.rsi_period :]:
                gain = max(0, change)
                loss = abs(min(0, change))

                # Wilder's smoothing
                avg_gain = ((avg_gain * (self.rsi_period - 1)) + gain) / self.rsi_period
                avg_loss = ((avg_loss * (self.rsi_period - 1)) + loss) / self.rsi_period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_position_info(self) -> Dict[str, Any]:
        """Get extended position information."""
        base_info = super().get_position_info()
        base_info.update(
            {
                "open_positions": len(self.open_positions),
                "used_entry_levels": list(self.used_entry_levels),
                "current_rsi": self.current_rsi,
                "previous_rsi": self.previous_rsi,
                "max_positions": self.max_positions,
            }
        )
        return base_info

    def reset(self) -> None:
        """Reset strategy state."""
        super().reset()
        self.current_rsi = None
        self.previous_rsi = None
        self.open_positions.clear()
        self.used_entry_levels.clear()
