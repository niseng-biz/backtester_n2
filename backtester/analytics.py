"""
Analytics engine for calculating performance metrics and statistics.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .models import Trade, BacktestResult


class AnalyticsEngine:
    """Engine for calculating trading performance metrics."""

    @staticmethod
    def calculate_profit_factor(trades: List[Trade]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).

        Args:
            trades: List of completed trades

        Returns:
            Profit factor value
        """
        if not trades:
            return 0.0

        gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
        gross_loss = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    @staticmethod
    def calculate_win_rate(trades: List[Trade]) -> float:
        """
        Calculate win rate (winning trades / total trades).

        Args:
            trades: List of completed trades

        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        if not trades:
            return 0.0

        winning_trades = sum(1 for trade in trades if trade.pnl > 0)
        return winning_trades / len(trades)

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float], risk_free_rate: float = 0.02
    ) -> Optional[float]:
        """
        Calculate Sharpe ratio.

        Args:
            returns: List of period returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio or None if insufficient data
        """
        if len(returns) < 2:
            return None

        # Convert annual risk-free rate to period rate
        period_risk_free_rate = risk_free_rate / 252  # Assuming daily returns

        # Calculate excess returns
        excess_returns = [r - period_risk_free_rate for r in returns]

        # Calculate mean and standard deviation
        mean_excess_return = sum(excess_returns) / len(excess_returns)

        if len(excess_returns) == 1:
            return None

        variance = sum((r - mean_excess_return) ** 2 for r in excess_returns) / (
            len(excess_returns) - 1
        )
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return None

        # Annualize the Sharpe ratio
        return (mean_excess_return * math.sqrt(252)) / std_dev

    @staticmethod
    def calculate_max_drawdown(portfolio_values: List[float]) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown.

        Args:
            portfolio_values: List of portfolio values over time

        Returns:
            Tuple of (max_drawdown_pct, peak_index, trough_index)
        """
        if len(portfolio_values) < 2:
            return 0.0, 0, 0

        peak_value = portfolio_values[0]
        peak_index = 0
        max_drawdown = 0.0
        max_drawdown_peak_idx = 0
        max_drawdown_trough_idx = 0

        for i, value in enumerate(portfolio_values):
            if value > peak_value:
                peak_value = value
                peak_index = i

            drawdown = (peak_value - value) / peak_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_peak_idx = peak_index
                max_drawdown_trough_idx = i

        return max_drawdown, max_drawdown_peak_idx, max_drawdown_trough_idx

    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float], risk_free_rate: float = 0.02
    ) -> Optional[float]:
        """
        Calculate Sortino ratio (focuses on downside deviation).

        Args:
            returns: List of period returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio or None if insufficient data
        """
        if len(returns) < 2:
            return None

        period_risk_free_rate = risk_free_rate / 252
        excess_returns = [r - period_risk_free_rate for r in returns]
        mean_excess_return = sum(excess_returns) / len(excess_returns)

        # Calculate downside deviation (only negative returns)
        negative_returns = [r for r in excess_returns if r < 0]

        if not negative_returns:
            return float("inf") if mean_excess_return > 0 else None

        downside_variance = sum(r**2 for r in negative_returns) / len(excess_returns)
        downside_deviation = math.sqrt(downside_variance)

        if downside_deviation == 0:
            return None

        return (mean_excess_return * math.sqrt(252)) / downside_deviation

    @staticmethod
    def calculate_calmar_ratio(
        total_return: float, max_drawdown: float, years: float
    ) -> Optional[float]:
        """
        Calculate Calmar ratio (annualized return / max drawdown).

        Args:
            total_return: Total return as decimal
            max_drawdown: Maximum drawdown as decimal
            years: Number of years in the period

        Returns:
            Calmar ratio or None if max drawdown is zero
        """
        if max_drawdown == 0 or years == 0:
            return None

        annualized_return = (1 + total_return) ** (1 / years) - 1
        return annualized_return / max_drawdown

    @staticmethod
    def calculate_var(
        returns: List[float], confidence_level: float = 0.05
    ) -> Optional[float]:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: List of period returns
            confidence_level: Confidence level (e.g., 0.05 for 95% VaR)

        Returns:
            VaR value or None if insufficient data
        """
        if not returns:
            return None

        sorted_returns = sorted(returns)
        index = int(len(sorted_returns) * confidence_level)

        if index >= len(sorted_returns):
            return sorted_returns[-1]

        return sorted_returns[index]

    @staticmethod
    def calculate_beta(
        strategy_returns: List[float], benchmark_returns: List[float]
    ) -> Optional[float]:
        """
        Calculate beta relative to benchmark.

        Args:
            strategy_returns: Strategy returns
            benchmark_returns: Benchmark returns

        Returns:
            Beta value or None if insufficient data
        """
        if len(strategy_returns) != len(benchmark_returns) or len(strategy_returns) < 2:
            return None

        # Calculate means
        strategy_mean = sum(strategy_returns) / len(strategy_returns)
        benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)

        # Calculate covariance and variance
        covariance = sum(
            (s - strategy_mean) * (b - benchmark_mean)
            for s, b in zip(strategy_returns, benchmark_returns)
        ) / (len(strategy_returns) - 1)

        benchmark_variance = sum(
            (b - benchmark_mean) ** 2 for b in benchmark_returns
        ) / (len(benchmark_returns) - 1)

        if benchmark_variance == 0:
            return None

        return covariance / benchmark_variance

    @staticmethod
    def calculate_alpha(
        strategy_returns: List[float],
        benchmark_returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> Optional[float]:
        """
        Calculate alpha (excess return over expected return based on beta).

        Args:
            strategy_returns: Strategy returns
            benchmark_returns: Benchmark returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Alpha value or None if insufficient data
        """
        if len(strategy_returns) != len(benchmark_returns) or len(strategy_returns) < 2:
            return None

        beta = AnalyticsEngine.calculate_beta(strategy_returns, benchmark_returns)
        if beta is None:
            return None

        period_risk_free_rate = risk_free_rate / 252

        strategy_mean = sum(strategy_returns) / len(strategy_returns)
        benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)

        expected_return = period_risk_free_rate + beta * (
            benchmark_mean - period_risk_free_rate
        )
        alpha = strategy_mean - expected_return

        # Annualize alpha
        return alpha * 252

    @staticmethod
    def calculate_information_ratio(
        strategy_returns: List[float], benchmark_returns: List[float]
    ) -> Optional[float]:
        """
        Calculate information ratio (active return / tracking error).

        Args:
            strategy_returns: Strategy returns
            benchmark_returns: Benchmark returns

        Returns:
            Information ratio or None if insufficient data
        """
        if len(strategy_returns) != len(benchmark_returns) or len(strategy_returns) < 2:
            return None

        # Calculate active returns
        active_returns = [s - b for s, b in zip(strategy_returns, benchmark_returns)]

        # Calculate mean active return
        mean_active_return = sum(active_returns) / len(active_returns)

        # Calculate tracking error (standard deviation of active returns)
        variance = sum((r - mean_active_return) ** 2 for r in active_returns) / (
            len(active_returns) - 1
        )
        tracking_error = math.sqrt(variance)

        if tracking_error == 0:
            return None

        # Annualize
        return (mean_active_return * math.sqrt(252)) / tracking_error

    @staticmethod
    def generate_backtest_result(
        initial_capital: float,
        final_capital: float,
        trades: List[Trade],
        portfolio_history: List[float],
        benchmark_returns: Optional[List[float]] = None,
        risk_free_rate: float = 0.02,
    ) -> BacktestResult:
        """
        Generate comprehensive backtest result.

        Args:
            initial_capital: Starting capital
            final_capital: Ending capital
            trades: List of all trades
            portfolio_history: Portfolio values over time
            benchmark_returns: Optional benchmark returns for comparison
            risk_free_rate: Annual risk-free rate

        Returns:
            BacktestResult object with all metrics
        """
        # Basic trade statistics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade.pnl > 0)
        losing_trades = total_trades - winning_trades

        gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
        gross_loss = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))

        profit_factor = AnalyticsEngine.calculate_profit_factor(trades)
        win_rate = AnalyticsEngine.calculate_win_rate(trades)

        # Portfolio performance
        total_return = (final_capital - initial_capital) / initial_capital
        max_drawdown, _, _ = AnalyticsEngine.calculate_max_drawdown(portfolio_history)

        # Calculate returns for ratio calculations
        returns = []
        if len(portfolio_history) > 1:
            for i in range(1, len(portfolio_history)):
                ret = (
                    portfolio_history[i] - portfolio_history[i - 1]
                ) / portfolio_history[i - 1]
                returns.append(ret)

        sharpe_ratio = AnalyticsEngine.calculate_sharpe_ratio(returns, risk_free_rate)

        # Calculate annualized return
        if len(portfolio_history) > 1:
            # Assume daily data points
            years = len(portfolio_history) / 252
            annualized_return = (
                (1 + total_return) ** (1 / years) - 1 if years > 0 else None
            )
        else:
            annualized_return = None

        return BacktestResult(
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_return=total_return,
            annualized_return=annualized_return,
            trades=trades.copy(),
            portfolio_history=portfolio_history.copy(),
        )

    @staticmethod
    def calculate_trade_statistics(trades: List[Trade]) -> Dict[str, Any]:
        """
        Calculate detailed trade statistics.

        Args:
            trades: List of trades

        Returns:
            Dictionary with trade statistics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
            }

        winning_trades = [trade for trade in trades if trade.pnl > 0]
        losing_trades = [trade for trade in trades if trade.pnl < 0]

        total_trades = len(trades)
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)

        win_rate = num_winning / total_trades

        average_win = (
            sum(trade.pnl for trade in winning_trades) / num_winning
            if num_winning > 0
            else 0.0
        )
        average_loss = (
            sum(trade.pnl for trade in losing_trades) / num_losing
            if num_losing > 0
            else 0.0
        )

        largest_win = max((trade.pnl for trade in winning_trades), default=0.0)
        largest_loss = min((trade.pnl for trade in losing_trades), default=0.0)

        profit_factor = AnalyticsEngine.calculate_profit_factor(trades)

        # Expectancy = (Win Rate × Average Win) + (Loss Rate × Average Loss)
        expectancy = (win_rate * average_win) + ((1 - win_rate) * average_loss)

        return {
            "total_trades": total_trades,
            "winning_trades": num_winning,
            "losing_trades": num_losing,
            "win_rate": win_rate,
            "average_win": average_win,
            "average_loss": average_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
        }

    @staticmethod
    def calculate_monthly_returns(
        portfolio_history: List[Tuple[datetime, float]],
    ) -> Dict[str, List[float]]:
        """
        Calculate monthly returns from portfolio history.

        Args:
            portfolio_history: List of (timestamp, portfolio_value) tuples

        Returns:
            Dictionary with monthly returns by year
        """
        if len(portfolio_history) < 2:
            return {}

        monthly_returns = {}
        current_month_start = None
        current_month_start_value = None

        for timestamp, value in portfolio_history:
            if (
                current_month_start is None
                or timestamp.month != current_month_start.month
            ):
                # New month
                if (
                    current_month_start is not None
                    and current_month_start_value is not None
                ):
                    # Calculate return for previous month
                    monthly_return = (
                        value - current_month_start_value
                    ) / current_month_start_value

                    year = str(current_month_start.year)
                    if year not in monthly_returns:
                        monthly_returns[year] = []
                    monthly_returns[year].append(monthly_return)

                current_month_start = timestamp
                current_month_start_value = value

        return monthly_returns
