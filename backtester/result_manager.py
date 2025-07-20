"""
Result management system for organizing backtest outputs.
"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import Trade, BacktestResult


class ResultManager:
    """Manages the organization and storage of backtest results."""

    def __init__(self, base_dir: str = "test_results"):
        """
        Initialize the result manager.

        Args:
            base_dir: Base directory for storing results
        """
        self.base_dir = base_dir
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create test_results directory if it doesn't exist."""
        try:
            Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning: Could not create {self.base_dir} directory: {e}")
            print(f"   Results will be saved to current directory instead.")
            self.base_dir = "."

    def save_backtest_results(self, results: BacktestResult, strategy_name: str) -> str:
        """
        Save backtest results to JSON file.

        Args:
            results: BacktestResult object to save
            strategy_name: Name of the strategy for filename

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.json"
        filepath = self.get_results_path(filename)

        try:
            # Convert BacktestResult to dictionary
            results_dict = {
                "strategy_name": strategy_name,
                "timestamp": timestamp,
                "initial_capital": results.initial_capital,
                "final_capital": results.final_capital,
                "net_profit": results.net_profit,
                "total_return_pct": (results.final_capital - results.initial_capital)
                / results.initial_capital
                * 100,
                "annualized_return_pct": results.annualized_return,
                "total_trades": results.total_trades,
                "winning_trades": results.winning_trades,
                "losing_trades": results.losing_trades,
                "win_rate_pct": results.win_rate,
                "gross_profit": results.gross_profit,
                "gross_loss": results.gross_loss,
                "profit_factor": results.profit_factor,
                "max_drawdown_pct": results.max_drawdown,
                "sharpe_ratio": results.sharpe_ratio,
                "average_win": results.average_win,
                "average_loss": results.average_loss,
                "portfolio_history": results.portfolio_history,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results_dict, f, indent=2, default=str)

            return filepath

        except Exception as e:
            print(f"⚠️ Error saving backtest results: {e}")
            return ""

    def save_trade_history(self, trades: List[Trade], strategy_name: str) -> str:
        """
        Save trade history to CSV file.

        Args:
            trades: List of Trade objects to save
            strategy_name: Name of the strategy for filename

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trade_history_{timestamp}.csv"
        filepath = self.get_results_path(filename)

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(
                    [
                        "entry_time",
                        "exit_time",
                        "action",
                        "entry_price",
                        "exit_price",
                        "quantity",
                        "pnl",
                        "return_pct",
                        "order_type",
                        "is_profitable",
                    ]
                )

                # Write trade data
                for trade in trades:
                    writer.writerow(
                        [
                            trade.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                            trade.exit_time.strftime("%Y-%m-%d %H:%M:%S"),
                            trade.action.value,
                            trade.entry_price,
                            trade.exit_price,
                            trade.quantity,
                            trade.pnl,
                            trade.return_percentage,
                            trade.order_type.value,
                            trade.is_profitable,
                        ]
                    )

            return filepath

        except Exception as e:
            print(f"⚠️ Error saving trade history: {e}")
            return ""

    def get_results_path(self, filename: str) -> str:
        """
        Generate full path for results file.

        Args:
            filename: Name of the file

        Returns:
            Full path to the file
        """
        return os.path.join(self.base_dir, filename)

    def list_result_files(self) -> Dict[str, List[str]]:
        """
        List all result files in the results directory.

        Returns:
            Dictionary with 'json' and 'csv' keys containing file lists
        """
        try:
            files = os.listdir(self.base_dir)
            json_files = [
                f for f in files if f.endswith(".json") and "backtest_results" in f
            ]
            csv_files = [
                f for f in files if f.endswith(".csv") and "trade_history" in f
            ]

            return {
                "json": sorted(json_files, reverse=True),  # Most recent first
                "csv": sorted(csv_files, reverse=True),
            }
        except Exception as e:
            print(f"⚠️ Error listing result files: {e}")
            return {"json": [], "csv": []}

    def load_backtest_results(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load backtest results from JSON file.

        Args:
            filename: Name of the JSON file to load

        Returns:
            Dictionary containing backtest results or None if error
        """
        filepath = self.get_results_path(filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading backtest results from {filename}: {e}")
            return None
