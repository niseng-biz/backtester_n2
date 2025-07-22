"""
Portfolio management system for tracking positions, cash, and performance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import MarketData, Order, OrderAction, Trade
from .order_manager import OrderManager


class Position:
    """Represents a single position in a security with LOT support."""

    def __init__(
        self,
        symbol: str,
        quantity: float = 0,
        avg_price: float = 0.0,
        position_id: str = None,
    ):
        """
        Initialize position.

        Args:
            symbol: Security symbol
            position_id: Unique identifier for this position 
                (for multiple position support)
            quantity: Number of units (positive = long, negative = short, supports fractional)
            avg_price: Average cost basis per unit
        """
        self.symbol = symbol
        self.position_id = position_id or f"{symbol}_{datetime.now().timestamp()}"
        self.quantity = float(quantity)  # Support fractional quantities
        self.avg_price = avg_price
        self.realized_pnl = 0.0
        self.trades: List[Trade] = []
        self.entry_time = datetime.now()
        self.is_closed = False

    def add_trade(self, trade: Trade, current_price: float) -> Optional[Trade]:
        """
        Add trade to position and update average price.
        Creates completed trade records when positions are closed.

        Args:
            trade: Trade to add
            current_price: Current market price

        Returns:
            Completed trade if position was closed, None otherwise
        """
        completed_trade = None

        if trade.action == OrderAction.BUY:
            if self.quantity >= 0:
                # Adding to long position or starting new long position
                if self.quantity == 0:
                    # Starting new long position - record entry time
                    self.quantity = trade.quantity
                    self.avg_price = trade.entry_price
                    self.entry_time = trade.entry_time
                else:
                    # Adding to existing long position
                    total_cost = (self.quantity * self.avg_price) + (
                        trade.quantity * trade.entry_price
                    )
                    self.quantity += trade.quantity
                    self.avg_price = total_cost / self.quantity
            else:
                # Reducing short position (covering)
                if trade.quantity >= abs(self.quantity):
                    # Closing entire short position and potentially going long
                    pnl = abs(self.quantity) * (self.avg_price - trade.entry_price)
                    self.realized_pnl += pnl

                    # Create completed trade for the closed short position
                    completed_trade = Trade(
                        entry_price=self.avg_price,
                        exit_price=trade.entry_price,
                        quantity=abs(self.quantity),
                        entry_time=self.entry_time,  # Use position's entry time
                        exit_time=trade.entry_time,
                        action=OrderAction.SELL,  # Original short position
                        order_type=trade.order_type,
                        pnl=pnl,
                    )

                    # Set up remaining long position if any
                    remaining_quantity = trade.quantity - abs(self.quantity)
                    if remaining_quantity > 0:
                        self.quantity = remaining_quantity
                        self.avg_price = trade.entry_price
                        self.entry_time = (
                            trade.entry_time
                        )  # New entry time for long position
                    else:
                        self.quantity = 0
                        self.avg_price = 0.0

                    self.trades.clear()
                else:
                    # Partially covering short position
                    pnl = trade.quantity * (self.avg_price - trade.entry_price)
                    self.realized_pnl += pnl
                    self.quantity += trade.quantity  # quantity becomes less negative

        else:  # SELL
            if self.quantity > 0:
                # Reducing long position
                if trade.quantity >= self.quantity:
                    # Closing entire long position and potentially going short
                    pnl = self.quantity * (trade.entry_price - self.avg_price)
                    self.realized_pnl += pnl

                    # Create completed trade for the closed long position
                    completed_trade = Trade(
                        entry_price=self.avg_price,
                        exit_price=trade.entry_price,
                        quantity=self.quantity,
                        entry_time=self.entry_time,  # Use position's entry time
                        exit_time=trade.entry_time,
                        action=OrderAction.BUY,  # Original long position
                        order_type=trade.order_type,
                        pnl=pnl,
                    )

                    # Set up remaining short position if any
                    remaining_quantity = trade.quantity - self.quantity
                    if remaining_quantity > 0:
                        self.quantity = -remaining_quantity
                        self.avg_price = trade.entry_price
                        self.entry_time = (
                            trade.entry_time
                        )  # New entry time for short position
                    else:
                        self.quantity = 0
                        self.avg_price = 0.0

                    self.trades.clear()
                else:
                    # Partially closing long position
                    pnl = trade.quantity * (trade.entry_price - self.avg_price)
                    self.realized_pnl += pnl
                    self.quantity -= trade.quantity
            else:
                # Adding to short position or starting new short position
                if self.quantity == 0:
                    # Starting new short position - record entry time
                    self.quantity = -trade.quantity
                    self.avg_price = trade.entry_price
                    self.entry_time = trade.entry_time
                else:
                    # Adding to existing short position
                    total_cost = (abs(self.quantity) * self.avg_price) + (
                        trade.quantity * trade.entry_price
                    )
                    self.quantity -= trade.quantity
                    self.avg_price = total_cost / abs(self.quantity)

        # Add the trade to our history
        self.trades.append(trade)

        return completed_trade

    def get_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L based on current price.

        Args:
            current_price: Current market price

        Returns:
            Unrealized P&L
        """
        if self.quantity == 0:
            return 0.0

        if self.quantity > 0:
            # Long position
            return self.quantity * (current_price - self.avg_price)
        else:
            # Short position
            return abs(self.quantity) * (self.avg_price - current_price)

    def get_market_value(self, current_price: float) -> float:
        """
        Get current market value of position.

        Args:
            current_price: Current market price

        Returns:
            Market value of position
        """
        return abs(self.quantity) * current_price

    def is_flat(self) -> bool:
        """Check if position is flat (no shares held)."""
        return self.quantity == 0


class PortfolioManager:
    """Manages portfolio positions, cash, and performance tracking."""

    def __init__(self, initial_capital: float = 100000.0, max_positions: int = 5):
        """
        Initialize portfolio manager.

        Args:
            initial_capital: Starting cash amount
            max_positions: Maximum number of concurrent positions
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}  # position_id -> Position
        self.order_manager = OrderManager()
        self.max_positions = max_positions

        # Performance tracking
        self.portfolio_history: List[Dict[str, Any]] = []
        self.trade_history: List[Trade] = []
        self.daily_returns: List[float] = []

        # Risk management
        self.max_position_size = (
            1.0  # 100% of portfolio per position (allow full investment)
        )
        self.max_total_exposure = 1.0  # 100% total exposure

    def process_order(self, order: Order, current_data: MarketData) -> Optional[Trade]:
        """
        Process order and update portfolio if executed.

        Args:
            order: Order to process
            current_data: Current market data

        Returns:
            Trade if order was executed, None otherwise
        """
        # Check if order can be executed based on available cash/positions
        if not self._can_execute_order(order, current_data.close):
            return None

        # Add order to order manager
        self.order_manager.add_order(order)

        # Process orders and get executed trades
        trades = self.order_manager.process_orders(current_data)

        # Update portfolio with executed trades
        for trade in trades:
            self._update_portfolio_with_trade(trade, current_data.close)
            # Note: completed trades are added to history in _update_portfolio_with_trade

        return trades[0] if trades else None

    def _can_execute_order(self, order: Order, current_price: float) -> bool:
        """
        Check if order can be executed based on available capital and risk limits.

        Args:
            order: Order to check
            current_price: Current market price

        Returns:
            True if order can be executed, False otherwise
        """
        # Get position key from order
        position_key = order.position_id if order.position_id else "DEFAULT"

        if order.action == OrderAction.BUY:
            # Check if we have enough cash
            required_cash = order.quantity * current_price
            if required_cash > self.cash:
                return False

            # Check if we can open a new position (if this is a new position)
            if position_key not in self.positions and not self.can_open_new_position():
                return False

            # Check position size limits
            position_value = order.quantity * current_price
            portfolio_value = self.get_total_value({"DEFAULT": current_price})
            if position_value > portfolio_value * self.max_position_size:
                return False

        else:  # SELL
            # Check if we have enough shares to sell
            position = self.positions.get(position_key)
            if position is None or position.quantity < order.quantity:
                return False

        return True

    def _update_portfolio_with_trade(self, trade: Trade, current_price: float) -> None:
        """
        Update portfolio positions and cash with executed trade.

        Args:
            trade: Executed trade
            current_price: Current market price
        """
        # Use position_id from trade, or default to "DEFAULT"
        position_key = trade.position_id if trade.position_id else "DEFAULT"
        symbol = "DEFAULT"  # In a real system, this would come from the trade

        # Get or create position
        if position_key not in self.positions:
            self.positions[position_key] = Position(symbol, 0, 0.0, position_key)

        position = self.positions[position_key]

        # Update position and get completed trade if any
        completed_trade = position.add_trade(trade, current_price)

        # Only add completed trades to history (not individual order executions)
        # This prevents duplicate entries and ensures proper entry/exit pairing
        if completed_trade:
            self.trade_history.append(completed_trade)

        # Update cash
        if trade.action == OrderAction.BUY:
            self.cash -= trade.quantity * trade.entry_price
        else:
            self.cash += trade.quantity * trade.entry_price

        # Remove position if flat
        if position.is_flat():
            del self.positions[position_key]

    def get_total_value(self, current_prices: Dict[str, float] = None) -> float:
        """
        Calculate total portfolio value.

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            Total portfolio value
        """
        if current_prices is None:
            current_prices = {}

        total_value = self.cash

        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.avg_price)
            total_value += position.get_market_value(current_price)

        return total_value

    def get_unrealized_pnl(self, current_prices: Dict[str, float] = None) -> float:
        """
        Calculate total unrealized P&L.

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            Total unrealized P&L
        """
        if current_prices is None:
            current_prices = {}

        total_unrealized = 0.0

        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.avg_price)
            total_unrealized += position.get_unrealized_pnl(current_price)

        return total_unrealized

    def get_realized_pnl(self) -> float:
        """
        Calculate total realized P&L.

        Returns:
            Total realized P&L
        """
        total_realized = 0.0

        for position in self.positions.values():
            total_realized += position.realized_pnl

        return total_realized

    def get_total_pnl(self, current_prices: Dict[str, float] = None) -> float:
        """
        Calculate total P&L (realized + unrealized).

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            Total P&L
        """
        return self.get_realized_pnl() + self.get_unrealized_pnl(current_prices)

    def get_positions_summary(
        self, current_prices: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get summary of all positions.

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            List of position summaries
        """
        if current_prices is None:
            current_prices = {}

        summaries = []

        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.avg_price)

            summary = {
                "symbol": symbol,
                "quantity": position.quantity,
                "avg_price": position.avg_price,
                "current_price": current_price,
                "market_value": position.get_market_value(current_price),
                "unrealized_pnl": position.get_unrealized_pnl(current_price),
                "realized_pnl": position.realized_pnl,
                "total_trades": len(position.trades),
            }
            summaries.append(summary)

        return summaries

    def record_portfolio_snapshot(
        self, timestamp: datetime, current_prices: Dict[str, float] = None
    ) -> None:
        """
        Record portfolio snapshot for performance tracking.

        Args:
            timestamp: Timestamp for snapshot
            current_prices: Dictionary of symbol -> current price
        """
        total_value = self.get_total_value(current_prices)

        snapshot = {
            "timestamp": timestamp,
            "total_value": total_value,
            "cash": self.cash,
            "realized_pnl": self.get_realized_pnl(),
            "unrealized_pnl": self.get_unrealized_pnl(current_prices),
            "total_pnl": self.get_total_pnl(current_prices),
            "num_positions": len(self.positions),
            "total_trades": len(self.trade_history),
        }

        self.portfolio_history.append(snapshot)

        # Calculate daily return if we have previous data
        if len(self.portfolio_history) > 1:
            prev_value = self.portfolio_history[-2]["total_value"]
            daily_return = (total_value - prev_value) / prev_value
            self.daily_returns.append(daily_return)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        if not self.portfolio_history:
            return {}

        current_value = self.portfolio_history[-1]["total_value"]
        total_return = (current_value - self.initial_capital) / self.initial_capital

        # Calculate maximum drawdown
        peak_value = self.initial_capital
        max_drawdown = 0.0

        for snapshot in self.portfolio_history:
            value = snapshot["total_value"]
            if value > peak_value:
                peak_value = value

            drawdown = (peak_value - value) / peak_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate Sharpe ratio if we have returns
        sharpe_ratio = None
        if len(self.daily_returns) > 1:
            avg_return = sum(self.daily_returns) / len(self.daily_returns)
            variance = sum((r - avg_return) ** 2 for r in self.daily_returns) / len(
                self.daily_returns
            )
            std_dev = variance**0.5

            if std_dev > 0:
                sharpe_ratio = (avg_return * 252) / (std_dev * (252**0.5))  # Annualized

        # Win rate calculation
        profitable_trades = sum(1 for trade in self.trade_history if trade.pnl > 0)
        total_trades = len(self.trade_history)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0

        return {
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown * 100,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "win_rate_pct": win_rate * 100,
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "losing_trades": total_trades - profitable_trades,
            "current_value": current_value,
            "initial_capital": self.initial_capital,
        }

    def set_risk_limits(
        self, max_position_size: float = None, max_total_exposure: float = None
    ) -> None:
        """
        Set risk management limits.

        Args:
            max_position_size: Maximum position size as fraction of portfolio
            max_total_exposure: Maximum total exposure as fraction of portfolio
        """
        if max_position_size is not None:
            if not 0 < max_position_size <= 1:
                raise ValueError("Max position size must be between 0 and 1")
            self.max_position_size = max_position_size

        if max_total_exposure is not None:
            if not 0 < max_total_exposure <= 2:  # Allow up to 200% for margin
                raise ValueError("Max total exposure must be between 0 and 2")
            self.max_total_exposure = max_total_exposure

    def get_available_position_slots(self) -> int:
        """
        Get number of available position slots.

        Returns:
            Number of available position slots
        """
        return self.max_positions - len(self.positions)

    def can_open_new_position(self) -> bool:
        """
        Check if a new position can be opened.

        Returns:
            True if new position can be opened, False otherwise
        """
        return len(self.positions) < self.max_positions

    def create_new_position(
        self, symbol: str, trade: Trade, current_price: float
    ) -> str:
        """
        Create a new position for multiple position strategies.

        Args:
            symbol: Symbol for the position
            trade: Initial trade for the position
            current_price: Current market price

        Returns:
            Position ID of the created position
        """
        if not self.can_open_new_position():
            raise ValueError(
                f"Cannot open new position: maximum positions ({self.max_positions}) reached"
            )

        # Create unique position ID
        position_id = f"{symbol}_{len(self.positions)}_{datetime.now().timestamp()}"

        # Create new position
        position = Position(symbol, 0, 0.0, position_id)
        position.add_trade(trade, current_price)

        # Add to positions
        self.positions[position_id] = position

        return position_id

    def close_position(self, position_id: str, current_price: float) -> Optional[Trade]:
        """
        Close a specific position.

        Args:
            position_id: ID of position to close
            current_price: Current market price

        Returns:
            Completed trade if position was closed, None otherwise
        """
        if position_id not in self.positions:
            return None

        position = self.positions[position_id]

        if position.quantity == 0:
            return None

        # Create closing trade
        closing_action = OrderAction.SELL if position.quantity > 0 else OrderAction.BUY
        closing_quantity = abs(position.quantity)

        closing_trade = Trade(
            entry_price=position.avg_price,
            exit_price=current_price,
            quantity=closing_quantity,
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            action=(
                OrderAction.BUY if position.quantity > 0 else OrderAction.SELL
            ),  # Original position action
            order_type=position.trades[0].order_type if position.trades else None,
        )

        # Calculate P&L
        if position.quantity > 0:
            # Long position
            closing_trade.pnl = position.quantity * (current_price - position.avg_price)
        else:
            # Short position
            closing_trade.pnl = abs(position.quantity) * (
                position.avg_price - current_price
            )

        # Update cash
        if closing_action == OrderAction.SELL:
            self.cash += closing_quantity * current_price
        else:
            self.cash -= closing_quantity * current_price

        # Mark position as closed and remove
        position.is_closed = True
        position.quantity = 0
        del self.positions[position_id]

        # Add to trade history
        self.trade_history.append(closing_trade)

        return closing_trade

    def reset(self) -> None:
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.portfolio_history.clear()
        self.trade_history.clear()
        self.daily_returns.clear()
        self.order_manager.reset()
