"""
Main backtester engine that coordinates all components.
"""

import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .analytics import AnalyticsEngine
from .data_reader import DataReader
from .models import BacktestResult, MarketData
from .portfolio import PortfolioManager
from .result_manager import ResultManager
from .strategy import Strategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backtester.log"), logging.StreamHandler()],
)


class Backtester:
    """
    Main backtesting engine that coordinates data, strategy, and portfolio management.
    """

    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting capital for backtesting
        """
        self.initial_capital = initial_capital
        self.portfolio_manager = PortfolioManager(initial_capital)
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.result_manager = ResultManager()

        # Backtesting state
        self.is_running = False
        self.current_data_index = 0
        self.market_data: List[MarketData] = []
        self.strategy: Optional[Strategy] = None

        # Results
        self.backtest_result: Optional[BacktestResult] = None

    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """
        Set callback function for progress updates.

        Args:
            callback: Function that takes (current_step, total_steps) as arguments
        """
        self.progress_callback = callback

    def run_backtest(
        self,
        data_reader: DataReader,
        strategy: Strategy,
        data_source: str,
        symbol: str = "DEFAULT",
    ) -> BacktestResult:
        """
        Run complete backtest.

        Args:
            data_reader: Data reader instance
            strategy: Trading strategy instance
            data_source: Path to data source
            symbol: Symbol being traded (for multi-symbol support)

        Returns:
            BacktestResult with comprehensive results
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Starting backtest for {symbol}...")
        print(f"Starting backtest for {symbol}...")
        start_time = time.time()

        try:
            # Validate inputs
            if not data_reader:
                raise ValueError("Data reader cannot be None")
            if not strategy:
                raise ValueError("Strategy cannot be None")
            if not data_source:
                raise ValueError("Data source cannot be empty")

            # Load market data
            logger.info("Loading market data...")
            print("Loading market data...")
            self.market_data = data_reader.load_data(data_source)
            logger.info(f"Loaded {len(self.market_data)} data points")
            print(f"Loaded {len(self.market_data)} data points")

            if not self.market_data:
                raise ValueError(
                    "No market data loaded - check data source path and format"
                )

            # Validate market data
            if len(self.market_data) < 10:
                logger.warning(
                    f"Very few data points ({len(self.market_data)}) - results may be unreliable"
                )

            # Initialize strategy and portfolio
            self.strategy = strategy
            self.strategy.reset()
            self.portfolio_manager.reset()
            logger.info(f"Initialized strategy: {strategy.get_strategy_name()}")

            # Run backtesting loop
            self.is_running = True
            self._run_backtesting_loop()

            # Generate results
            self.backtest_result = self._generate_results()

            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Backtest completed successfully in {duration:.2f} seconds")
            print(f"Backtest completed in {duration:.2f} seconds")

            return self.backtest_result

        except FileNotFoundError as e:
            self.is_running = False
            error_msg = (
                f"Data file not found: {data_source}. Please check the file path."
            )
            logger.error(error_msg)
            print(f"Backtest failed: {error_msg}")
            raise FileNotFoundError(error_msg) from e
        except ValueError as e:
            self.is_running = False
            error_msg = f"Invalid input or data: {str(e)}"
            logger.error(error_msg)
            print(f"Backtest failed: {error_msg}")
            raise ValueError(error_msg) from e
        except Exception as e:
            self.is_running = False
            error_msg = f"Unexpected error during backtesting: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"Backtest failed: {error_msg}")
            raise

    def _run_backtesting_loop(self) -> None:
        """Run the main backtesting loop."""
        total_steps = len(self.market_data)

        for i, current_data in enumerate(self.market_data):
            if not self.is_running:
                break

            self.current_data_index = i

            # Get historical data up to current point
            historical_data = self.market_data[: i + 1]

            # Generate trading signal
            order = self.strategy.generate_signal(current_data, historical_data[:-1])

            # Process order if generated
            if order is not None:
                trade = self.portfolio_manager.process_order(order, current_data)

                # Update strategy position tracking if trade executed
                if trade is not None:
                    self.strategy.update_position(order, trade.entry_price)

                    # Update strategy cash and position for compatibility
                    if hasattr(self.strategy, "cash") and hasattr(
                        self.strategy, "current_position"
                    ):
                        # Update strategy's cash and position tracking
                        self.strategy.cash = self.portfolio_manager.cash

                        # Calculate total position from portfolio
                        total_position = 0
                        for position in self.portfolio_manager.positions.values():
                            total_position += position.quantity
                        self.strategy.current_position = total_position

            # Record portfolio snapshot
            current_prices = {"DEFAULT": current_data.close}
            self.portfolio_manager.record_portfolio_snapshot(
                current_data.timestamp, current_prices
            )

            # Update progress
            if self.progress_callback and (i % 100 == 0 or i == total_steps - 1):
                self.progress_callback(i + 1, total_steps)

        self.is_running = False

    def _generate_results(self) -> BacktestResult:
        """Generate comprehensive backtest results."""
        if not self.portfolio_manager.portfolio_history:
            raise ValueError("No portfolio history available for results generation")

        # Get final portfolio value
        final_snapshot = self.portfolio_manager.portfolio_history[-1]
        final_capital = final_snapshot["total_value"]

        # Get portfolio value history
        portfolio_values = [
            snapshot["total_value"]
            for snapshot in self.portfolio_manager.portfolio_history
        ]

        # Generate comprehensive results using analytics engine
        result = AnalyticsEngine.generate_backtest_result(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            trades=self.portfolio_manager.trade_history,
            portfolio_history=portfolio_values,
        )

        return result

    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current backtesting status.

        Returns:
            Dictionary with current status information
        """
        if not self.market_data:
            return {
                "status": "not_started",
                "progress": 0.0,
                "current_date": None,
                "total_trades": 0,
                "current_value": self.initial_capital,
            }

        progress = (
            (self.current_data_index + 1) / len(self.market_data)
            if self.market_data
            else 0.0
        )
        current_date = (
            self.market_data[self.current_data_index].timestamp
            if self.current_data_index < len(self.market_data)
            else None
        )

        status = (
            "running"
            if self.is_running
            else ("completed" if self.backtest_result else "ready")
        )

        current_value = self.initial_capital
        if self.portfolio_manager.portfolio_history:
            current_value = self.portfolio_manager.portfolio_history[-1]["total_value"]

        return {
            "status": status,
            "progress": progress,
            "progress_pct": progress * 100,
            "current_date": current_date,
            "current_index": self.current_data_index,
            "total_data_points": len(self.market_data),
            "total_trades": len(self.portfolio_manager.trade_history),
            "current_value": current_value,
            "unrealized_pnl": self.portfolio_manager.get_unrealized_pnl(),
            "realized_pnl": self.portfolio_manager.get_realized_pnl(),
        }

    def stop_backtest(self) -> None:
        """Stop the currently running backtest."""
        self.is_running = False

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        Get formatted trade history.

        Returns:
            List of trade dictionaries
        """
        trades = []
        for trade in self.portfolio_manager.trade_history:
            trade_dict = {
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "action": trade.action.value,
                "order_type": trade.order_type.value,
                "quantity": trade.quantity,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": trade.pnl,
                "return_pct": trade.return_percentage,
            }
            trades.append(trade_dict)

        return trades

    def get_portfolio_history(self) -> List[Dict[str, Any]]:
        """
        Get portfolio value history.

        Returns:
            List of portfolio snapshots
        """
        return self.portfolio_manager.portfolio_history.copy()

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.

        Returns:
            Dictionary with key performance metrics
        """
        if not self.backtest_result:
            return {}

        return {
            "total_return": self.backtest_result.total_return,
            "total_return_pct": self.backtest_result.total_return * 100,
            "annualized_return": self.backtest_result.annualized_return,
            "annualized_return_pct": (
                self.backtest_result.annualized_return * 100
                if self.backtest_result.annualized_return
                else None
            ),
            "max_drawdown": self.backtest_result.max_drawdown,
            "max_drawdown_pct": self.backtest_result.max_drawdown * 100,
            "sharpe_ratio": self.backtest_result.sharpe_ratio,
            "profit_factor": self.backtest_result.profit_factor,
            "win_rate": self.backtest_result.win_rate,
            "win_rate_pct": self.backtest_result.win_rate * 100,
            "total_trades": self.backtest_result.total_trades,
            "winning_trades": self.backtest_result.winning_trades,
            "losing_trades": self.backtest_result.losing_trades,
            "gross_profit": self.backtest_result.gross_profit,
            "gross_loss": self.backtest_result.gross_loss,
            "net_profit": self.backtest_result.net_profit,
            "initial_capital": self.backtest_result.initial_capital,
            "final_capital": self.backtest_result.final_capital,
        }

    def save_results(self, strategy_name: str = None) -> Dict[str, str]:
        """
        Save backtest results using ResultManager.

        Args:
            strategy_name: Name of the strategy (auto-detected if None)

        Returns:
            Dictionary with paths to saved files
        """
        if not self.backtest_result:
            raise ValueError("No backtest results available for saving")

        if strategy_name is None:
            strategy_name = (
                self.strategy.get_strategy_name() if self.strategy else "Unknown"
            )

        # Save backtest results
        json_path = self.result_manager.save_backtest_results(
            self.backtest_result, strategy_name
        )

        # Save trade history
        csv_path = self.result_manager.save_trade_history(
            self.portfolio_manager.trade_history, strategy_name
        )

        return {"json_results": json_path, "csv_trades": csv_path}

    def export_results(self, filename: str, format: str = "json") -> None:
        """
        Export backtest results to file (legacy method).

        Args:
            filename: Output filename
            format: Export format ('json' or 'csv')
        """
        if not self.backtest_result:
            raise ValueError("No backtest results available for export")

        if format.lower() == "json":
            self._export_json(filename)
        elif format.lower() == "csv":
            self._export_csv(filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, filename: str) -> None:
        """Export results as JSON."""
        import json

        export_data = {
            "summary": self.get_performance_summary(),
            "trades": self.get_trade_history(),
            "portfolio_history": self.get_portfolio_history(),
            "strategy_name": (
                self.strategy.get_strategy_name() if self.strategy else "Unknown"
            ),
            "export_timestamp": datetime.now().isoformat(),
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

    def _export_csv(self, filename: str) -> None:
        """Export trade history as CSV."""
        import csv

        trades = self.get_trade_history()
        if not trades:
            return

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)

    def compare_strategies(
        self, strategies: List[Strategy], data_reader: DataReader, data_source: str
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies on the same data.

        Args:
            strategies: List of strategies to compare
            data_reader: Data reader instance
            data_source: Path to data source

        Returns:
            Dictionary mapping strategy names to results
        """
        results = {}

        for strategy in strategies:
            print(f"Running backtest for strategy: {strategy.get_strategy_name()}")

            # Reset backtester state
            self.backtest_result = None
            self.current_data_index = 0

            # Run backtest for this strategy
            result = self.run_backtest(data_reader, strategy, data_source)
            results[strategy.get_strategy_name()] = result

        return results

    def optimize_strategy(
        self,
        strategy_class: type,
        parameter_ranges: Dict[str, List],
        data_reader: DataReader,
        data_source: str,
        optimization_metric: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            strategy_class: Strategy class to optimize
            parameter_ranges: Dictionary of parameter names to lists of values to test
            data_reader: Data reader instance
            data_source: Path to data source
            optimization_metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)

        Returns:
            Dictionary with best parameters and results
        """
        import itertools

        # Generate all parameter combinations
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        combinations = list(itertools.product(*param_values))

        best_result = None
        best_params = None
        best_metric_value = float("-inf")

        print(f"Testing {len(combinations)} parameter combinations...")

        for i, combination in enumerate(combinations):
            # Create parameter dictionary
            params = dict(zip(param_names, combination))

            # Create strategy instance with these parameters
            strategy = strategy_class(**params)

            # Run backtest
            try:
                result = self.run_backtest(data_reader, strategy, data_source)

                # Get metric value
                metric_value = getattr(result, optimization_metric, None)
                if metric_value is not None and metric_value > best_metric_value:
                    best_metric_value = metric_value
                    best_result = result
                    best_params = params

                if (i + 1) % 10 == 0:
                    print(f"Completed {i + 1}/{len(combinations)} combinations")

            except Exception as e:
                print(f"Error with parameters {params}: {e}")
                continue

        return {
            "best_parameters": best_params,
            "best_result": best_result,
            "best_metric_value": best_metric_value,
            "optimization_metric": optimization_metric,
            "total_combinations_tested": len(combinations),
        }
