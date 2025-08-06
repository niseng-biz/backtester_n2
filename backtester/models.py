"""
Core data models for the backtesting system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict


class OrderType(Enum):
    """Order execution types."""

    MARKET = "market"
    LIMIT = "limit"


class OrderAction(Enum):
    """Order actions."""

    BUY = "buy"
    SELL = "sell"


class LotSizeMode(Enum):
    """LOT size calculation modes."""

    FIXED = "fixed"  # Fixed lot size (constant)
    VARIABLE = "variable"  # Variable lot size based on available capital


@dataclass
class LotConfig:
    """Configuration for LOT-based trading."""

    base_lot_size: float = 1.0  # Base size of 1 LOT
    min_lot_size: float = 0.01  # Minimum allowed lot size
    lot_step: float = 0.01  # Minimum increment for lot sizes
    asset_type: str = "stock"  # Asset type: "stock", "crypto", "forex"
    lot_size_mode: LotSizeMode = LotSizeMode.VARIABLE  # Default to variable lot sizing

    # Variable lot sizing parameters
    capital_percentage: float = (
        0.1  # Percentage of available capital per trade (10% default)
    )
    max_lot_size: float = 10.0  # Maximum lot size for variable mode

    # Asset-specific lot configurations
    lot_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "stock": 100,  # 1 LOT = 100 shares for stocks
            "crypto": 1,  # 1 LOT = 1 unit for crypto
            "forex": 100000,  # 1 LOT = 100,000 units for forex
        }
    )

    def __post_init__(self):
        """Validate lot configuration."""
        if self.base_lot_size <= 0:
            raise ValueError("Base lot size must be positive")
        if self.min_lot_size <= 0:
            raise ValueError("Minimum lot size must be positive")
        if self.lot_step <= 0:
            raise ValueError("Lot step must be positive")
        if self.min_lot_size < self.lot_step:
            raise ValueError("Minimum lot size cannot be smaller than lot step")

    def validate_lot_size(self, lot_size: float) -> bool:
        """Validate if a lot size is allowed."""
        if lot_size < self.min_lot_size:
            return False

        # Check if lot size is a valid multiple of lot_step
        remainder = (lot_size - self.min_lot_size) % self.lot_step
        return abs(remainder) < 1e-10  # Account for floating point precision

    def round_lot_size(self, lot_size: float) -> float:
        """Round lot size to nearest valid increment."""
        if lot_size < self.min_lot_size:
            return self.min_lot_size

        # Round to nearest lot_step with proper precision handling
        steps = round((lot_size - self.min_lot_size) / self.lot_step)
        result = self.min_lot_size + (steps * self.lot_step)

        # Round to avoid floating point precision issues
        decimal_places = (
            len(str(self.lot_step).split(".")[-1]) if "." in str(self.lot_step) else 0
        )
        return round(result, decimal_places)

    def lot_to_units(self, lots: float) -> float:
        """Convert lot size to actual units based on asset type."""
        multiplier = self.lot_multipliers.get(self.asset_type, 1)
        return lots * self.base_lot_size * multiplier

    def units_to_lots(self, units: float) -> float:
        """Convert units to lot size based on asset type."""
        multiplier = self.lot_multipliers.get(self.asset_type, 1)
        return units / (self.base_lot_size * multiplier)

    def validate_and_round(self, lot_size: float) -> float:
        """
        Validate and round lot size to nearest valid increment.
        
        This method combines validation and rounding logic to eliminate
        duplicate code patterns across the codebase.
        
        Args:
            lot_size: The lot size to validate and round
            
        Returns:
            Validated and rounded lot size
        """
        if not self.validate_lot_size(lot_size):
            lot_size = self.round_lot_size(lot_size)
        return lot_size

    @classmethod
    def create_standard_configs(cls) -> Dict[str, 'LotConfig']:
        """
        Create standard LOT configurations for different asset types.
        
        This factory method eliminates duplicate LOT configuration initialization
        code by providing pre-configured settings for common asset types.
        
        Returns:
            Dictionary of standard LOT configurations keyed by asset type
        """
        return {
            'crypto': cls(
                asset_type="crypto",
                min_lot_size=0.01,
                lot_step=0.01,
                lot_size_mode=LotSizeMode.VARIABLE,
                capital_percentage=0.1,
                max_lot_size=10.0
            ),
            'stock': cls(
                asset_type="stock",
                min_lot_size=0.01,
                lot_step=0.01,
                lot_size_mode=LotSizeMode.FIXED,
                capital_percentage=0.1,
                max_lot_size=100.0
            ),
            'forex': cls(
                asset_type="forex",
                min_lot_size=0.01,
                lot_step=0.01,
                lot_size_mode=LotSizeMode.VARIABLE,
                capital_percentage=0.05,
                max_lot_size=50.0
            )
        }

    def calculate_lot_size(
        self,
        available_capital: float,
        current_price: float,
        target_lots: float = None,
        total_portfolio_value: float = None,
    ) -> float:
        """
        Calculate lot size based on mode (fixed or variable).

        Args:
            available_capital: Available cash for trading
            current_price: Current market price
            target_lots: Target lot size for fixed mode (ignored in variable mode)
            total_portfolio_value: Total portfolio value (cash + positions) for variable mode

        Returns:
            Calculated lot size
        """
        if self.lot_size_mode == LotSizeMode.FIXED:
            # Fixed mode: use target_lots or default to 1.0
            if target_lots is None:
                target_lots = 1.0

            # Check if we can afford the target lot size
            required_capital = self.lot_to_units(target_lots) * current_price
            if required_capital <= available_capital:
                return self.round_lot_size(target_lots)
            else:
                # Calculate maximum affordable lots
                max_affordable_units = available_capital / current_price
                max_affordable_lots = self.units_to_lots(max_affordable_units)
                return self.round_lot_size(max_affordable_lots)

        else:  # VARIABLE mode
            # Variable mode: calculate based on total portfolio value percentage
            # Use total portfolio value if provided, otherwise fall back to available capital
            base_capital = (
                total_portfolio_value
                if total_portfolio_value is not None
                else available_capital
            )

            # Calculate trade capital as percentage of total portfolio value
            trade_capital = base_capital * self.capital_percentage

            # Ensure we don't exceed available cash
            trade_capital = min(trade_capital, available_capital)

            max_affordable_units = trade_capital / current_price
            calculated_lots = self.units_to_lots(max_affordable_units)

            # Apply maximum lot size limit
            calculated_lots = min(calculated_lots, self.max_lot_size)

            return self.round_lot_size(calculated_lots)


@dataclass
class MarketData:
    """Represents a single candlestick with OHLCV data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __post_init__(self):
        """Validate price data consistency."""
        # Check for negative values first
        if any(price < 0 for price in [self.open, self.high, self.low, self.close]):
            raise ValueError("Prices cannot be negative")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

        # Check price consistency
        if self.high < max(self.open, self.close):
            raise ValueError(
                f"High price {self.high} cannot be lower than open {self.open} or close {self.close}"
            )

        if self.low > min(self.open, self.close):
            raise ValueError(
                f"Low price {self.low} cannot be higher than open {self.open} or close {self.close}"
            )


@dataclass
class Order:
    """Represents a trading order with LOT-based sizing support."""

    order_type: OrderType
    action: OrderAction
    quantity: float  # Changed to float to support fractional lots (0.1, 0.01)
    price: Optional[float] = None  # None for market orders
    position_id: Optional[str] = None  # For multiple position support
    lot_size: float = 1.0  # LOT size (1.0 = 1 LOT, 0.1 = 0.1 LOT, etc.)
    timestamp: datetime = field(default_factory=datetime.now)
    order_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))

    def __post_init__(self):
        """Validate order parameters."""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")

        if self.lot_size <= 0:
            raise ValueError("LOT size must be positive")

        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must specify a price")

        if self.order_type == OrderType.MARKET and self.price is not None:
            raise ValueError("Market orders should not specify a price")

        if self.price is not None and self.price <= 0:
            raise ValueError("Order price must be positive")

    @property
    def effective_quantity(self) -> float:
        """Calculate effective quantity based on lot size."""
        return self.quantity * self.lot_size

    @classmethod
    def create_lot_order(
        cls,
        order_type: OrderType,
        action: OrderAction,
        lots: float,
        lot_size: float = 1.0,
        price: Optional[float] = None,
        position_id: Optional[str] = None,
    ) -> "Order":
        """
        Create an order using LOT-based sizing.

        Args:
            order_type: Market or limit order
            action: Buy or sell
            lots: Number of lots (can be fractional like 0.1, 0.01)
            lot_size: Size of one lot (default 1.0)
            price: Price for limit orders
            position_id: Position identifier

        Returns:
            Order with calculated quantity based on lots
        """
        # For lot-based orders, quantity represents the number of lots
        return cls(
            order_type=order_type,
            action=action,
            quantity=lots,
            price=price,
            position_id=position_id,
            lot_size=lot_size,
        )

    def __hash__(self):
        """Make Order hashable using order_id."""
        return hash(self.order_id)

    def __eq__(self, other):
        """Compare orders by order_id."""
        if not isinstance(other, Order):
            return False
        return self.order_id == other.order_id


@dataclass
class Trade:
    """Represents a completed trade with entry/exit details and LOT support."""

    entry_price: float
    exit_price: float
    quantity: float  # Changed to float to support fractional lots
    entry_time: datetime
    exit_time: datetime
    action: OrderAction  # BUY or SELL for the entry
    order_type: OrderType
    position_id: Optional[str] = None  # For multiple position support
    lot_size: float = 1.0  # LOT size used for this trade
    pnl: Optional[float] = None  # Allow manual P&L setting

    def __post_init__(self):
        """Calculate P&L after initialization if not already set."""
        if self.pnl is None:
            if self.action == OrderAction.BUY:
                # Long position: profit when exit > entry
                self.pnl = (self.exit_price - self.entry_price) * self.quantity
            else:
                # Short position: profit when entry > exit
                self.pnl = (self.entry_price - self.exit_price) * self.quantity

    @property
    def return_percentage(self) -> float:
        """Calculate return as percentage."""
        if self.action == OrderAction.BUY:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.exit_price) / self.entry_price) * 100

    @property
    def is_profitable(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0


@dataclass
class BacktestResult:
    """Container for comprehensive backtesting results."""

    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    gross_profit: float
    gross_loss: float
    profit_factor: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    total_return: float
    annualized_return: Optional[float]
    trades: list[Trade] = field(default_factory=list)
    portfolio_history: list[float] = field(default_factory=list)

    @property
    def net_profit(self) -> float:
        """Calculate net profit."""
        return self.final_capital - self.initial_capital

    @property
    def average_win(self) -> float:
        """Calculate average winning trade."""
        if self.winning_trades == 0:
            return 0.0
        return self.gross_profit / self.winning_trades

    @property
    def average_loss(self) -> float:
        """Calculate average losing trade."""
        if self.losing_trades == 0:
            return 0.0
        return abs(self.gross_loss) / self.losing_trades
