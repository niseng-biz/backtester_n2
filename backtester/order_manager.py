"""
Order management system for handling market and limit orders.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Order, Trade, MarketData, OrderType, OrderAction


class OrderManager:
    """Manages order execution and tracking."""

    def __init__(self):
        """Initialize order manager."""
        self.pending_orders: List[Order] = []
        self.executed_trades: List[Trade] = []
        self.order_history: List[Order] = []
        self.slippage_factor = 0.001  # 0.1% slippage by default
        self.commission_rate = 0.001  # 0.1% commission by default

    def add_order(self, order: Order) -> None:
        """
        Add order to pending orders queue.

        Args:
            order: Order to add
        """
        if order.order_type == OrderType.MARKET:
            # Market orders are executed immediately
            self.pending_orders.append(order)
        elif order.order_type == OrderType.LIMIT:
            # Limit orders wait for price trigger
            self.pending_orders.append(order)

        self.order_history.append(order)

    def process_orders(self, current_data: MarketData) -> List[Trade]:
        """
        Process pending orders against current market data.

        Args:
            current_data: Current market data

        Returns:
            List of executed trades
        """
        executed_trades = []
        orders_to_remove = []

        for order in self.pending_orders:
            trade = self._try_execute_order(order, current_data)
            if trade:
                executed_trades.append(trade)
                self.executed_trades.append(trade)
                orders_to_remove.append(order)

        # Remove executed orders
        for order in orders_to_remove:
            self.pending_orders.remove(order)

        return executed_trades

    def _try_execute_order(
        self, order: Order, current_data: MarketData
    ) -> Optional[Trade]:
        """
        Try to execute a single order.

        Args:
            order: Order to execute
            current_data: Current market data

        Returns:
            Trade if executed, None otherwise
        """
        if order.order_type == OrderType.MARKET:
            return self._execute_market_order(order, current_data)
        elif order.order_type == OrderType.LIMIT:
            return self._execute_limit_order(order, current_data)

        return None

    def _execute_market_order(self, order: Order, current_data: MarketData) -> Trade:
        """
        Execute market order immediately at current price.

        Args:
            order: Market order to execute
            current_data: Current market data

        Returns:
            Executed trade
        """
        # Use current close price with slippage
        execution_price = self._apply_slippage(current_data.close, order.action)

        # Apply commission
        commission = execution_price * order.quantity * self.commission_rate

        # Create trade record - this represents a single order execution
        # P&L will be calculated later when position is closed
        trade = Trade(
            entry_price=execution_price,
            exit_price=execution_price,  # Will be updated when position is closed
            quantity=order.quantity,
            entry_time=current_data.timestamp,
            exit_time=current_data.timestamp,  # Will be updated when position is closed
            action=order.action,
            order_type=order.order_type,
            position_id=order.position_id,
        )

        # Set initial P&L to negative commission (will be updated when position closes)
        trade.pnl = -commission

        return trade

    def _execute_limit_order(
        self, order: Order, current_data: MarketData
    ) -> Optional[Trade]:
        """
        Execute limit order if price conditions are met.

        Args:
            order: Limit order to execute
            current_data: Current market data

        Returns:
            Trade if executed, None if conditions not met
        """
        if order.price is None:
            return None

        execution_price = None

        if order.action == OrderAction.BUY:
            # Buy limit order executes when market price <= limit price
            if current_data.low <= order.price:
                execution_price = min(order.price, current_data.close)
        else:
            # Sell limit order executes when market price >= limit price
            if current_data.high >= order.price:
                execution_price = max(order.price, current_data.close)

        if execution_price is not None:
            # Apply commission
            commission = execution_price * order.quantity * self.commission_rate

            # Create trade record
            trade = Trade(
                entry_price=execution_price,
                exit_price=execution_price,
                quantity=order.quantity,
                entry_time=current_data.timestamp,
                exit_time=current_data.timestamp,
                action=order.action,
                order_type=order.order_type,
                position_id=order.position_id,
            )

            # Adjust P&L for commission
            trade.pnl -= commission

            return trade

        return None

    def _apply_slippage(self, price: float, action: OrderAction) -> float:
        """
        Apply slippage to execution price.

        Args:
            price: Base price
            action: Order action (BUY/SELL)

        Returns:
            Price with slippage applied
        """
        if action == OrderAction.BUY:
            # Buying costs more due to slippage
            return price * (1 + self.slippage_factor)
        else:
            # Selling gets less due to slippage
            return price * (1 - self.slippage_factor)

    def set_slippage(self, slippage_factor: float) -> None:
        """
        Set slippage factor.

        Args:
            slippage_factor: Slippage as decimal (e.g., 0.001 for 0.1%)
        """
        if slippage_factor < 0:
            raise ValueError("Slippage factor cannot be negative")
        self.slippage_factor = slippage_factor

    def set_commission(self, commission_rate: float) -> None:
        """
        Set commission rate.

        Args:
            commission_rate: Commission as decimal (e.g., 0.001 for 0.1%)
        """
        if commission_rate < 0:
            raise ValueError("Commission rate cannot be negative")
        self.commission_rate = commission_rate

    def get_pending_orders(self) -> List[Order]:
        """Get list of pending orders."""
        return self.pending_orders.copy()

    def get_executed_trades(self) -> List[Trade]:
        """Get list of executed trades."""
        return self.executed_trades.copy()

    def get_order_history(self) -> List[Order]:
        """Get complete order history."""
        return self.order_history.copy()

    def cancel_order(self, order: Order) -> bool:
        """
        Cancel a pending order.

        Args:
            order: Order to cancel

        Returns:
            True if order was cancelled, False if not found
        """
        if order in self.pending_orders:
            self.pending_orders.remove(order)
            return True
        return False

    def cancel_all_orders(self) -> int:
        """
        Cancel all pending orders.

        Returns:
            Number of orders cancelled
        """
        count = len(self.pending_orders)
        self.pending_orders.clear()
        return count

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get order execution statistics.

        Returns:
            Dictionary with execution statistics
        """
        total_orders = len(self.order_history)
        executed_orders = len(self.executed_trades)
        pending_orders = len(self.pending_orders)

        buy_orders = sum(
            1 for trade in self.executed_trades if trade.action == OrderAction.BUY
        )
        sell_orders = executed_orders - buy_orders

        market_orders = sum(
            1 for trade in self.executed_trades if trade.order_type == OrderType.MARKET
        )
        limit_orders = executed_orders - market_orders

        total_commission = sum(
            trade.entry_price * trade.quantity * self.commission_rate
            for trade in self.executed_trades
        )

        return {
            "total_orders": total_orders,
            "executed_orders": executed_orders,
            "pending_orders": pending_orders,
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "market_orders": market_orders,
            "limit_orders": limit_orders,
            "total_commission_paid": total_commission,
            "execution_rate": (
                executed_orders / total_orders if total_orders > 0 else 0.0
            ),
        }

    def reset(self) -> None:
        """Reset order manager to initial state."""
        self.pending_orders.clear()
        self.executed_trades.clear()
        self.order_history.clear()


class AdvancedOrderManager(OrderManager):
    """Extended order manager with advanced features."""

    def __init__(self):
        """Initialize advanced order manager."""
        super().__init__()
        self.stop_loss_orders: Dict[str, float] = {}  # position_id -> stop_price
        self.take_profit_orders: Dict[str, float] = {}  # position_id -> target_price
        self.order_timeout: Dict[Order, datetime] = {}  # order -> expiry_time

    def add_stop_loss(self, position_id: str, stop_price: float) -> None:
        """
        Add stop-loss order for a position.

        Args:
            position_id: Identifier for the position
            stop_price: Price at which to trigger stop-loss
        """
        self.stop_loss_orders[position_id] = stop_price

    def add_take_profit(self, position_id: str, target_price: float) -> None:
        """
        Add take-profit order for a position.

        Args:
            position_id: Identifier for the position
            target_price: Price at which to trigger take-profit
        """
        self.take_profit_orders[position_id] = target_price

    def add_order_with_timeout(self, order: Order, timeout_minutes: int) -> None:
        """
        Add order with expiration timeout.

        Args:
            order: Order to add
            timeout_minutes: Minutes until order expires
        """
        from datetime import timedelta

        expiry_time = datetime.now() + timedelta(minutes=timeout_minutes)
        self.order_timeout[order] = expiry_time
        self.add_order(order)

    def process_orders(self, current_data: MarketData) -> List[Trade]:
        """
        Process orders including advanced order types.

        Args:
            current_data: Current market data

        Returns:
            List of executed trades
        """
        # Process regular orders
        trades = super().process_orders(current_data)

        # Process stop-loss and take-profit orders
        trades.extend(self._process_stop_orders(current_data))

        # Remove expired orders
        self._remove_expired_orders(current_data.timestamp)

        return trades

    def _process_stop_orders(self, current_data: MarketData) -> List[Trade]:
        """Process stop-loss and take-profit orders."""
        trades = []

        # This is a simplified implementation
        # In a real system, you'd track actual positions and their IDs

        return trades

    def _remove_expired_orders(self, current_time: datetime) -> None:
        """Remove orders that have expired."""
        expired_orders = []

        for order, expiry_time in self.order_timeout.items():
            if current_time >= expiry_time:
                expired_orders.append(order)

        for order in expired_orders:
            if order in self.pending_orders:
                self.pending_orders.remove(order)
            del self.order_timeout[order]
