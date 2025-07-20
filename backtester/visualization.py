"""
Visualization engine for backtesting results with matplotlib integration.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
import japanize_matplotlib

from .models import Trade, MarketData, OrderAction
from .backtester import Backtester


class VisualizationEngine:
    """Engine for creating charts and visualizations of backtesting results."""

    def __init__(
        self, style: str = "seaborn-v0_8", figsize: Tuple[int, int] = (15, 10)
    ):
        """
        Initialize visualization engine.

        Args:
            style: Matplotlib style to use
            figsize: Default figure size (width, height)
        """
        self.style = style
        self.figsize = figsize
        self.colors = {
            "entry_signal": "#808080",  # Gray for entry signals
            "exit_profit": "#00ff00",  # Green for profitable exits
            "exit_loss": "#ff0000",  # Red for loss exits
            "price_line": "#1f77b4",  # Blue for price line
            "equity_line": "#2ca02c",  # Green for equity curve
            "drawdown_fill": "#ff7f7f",  # Light red for drawdown
            "ma_short": "#ff7f0e",  # Orange for short MA
            "ma_long": "#d62728",  # Red for long MA
            "connection_line": "#666666",  # Gray for connection lines
        }

        # Set matplotlib style
        try:
            plt.style.use(self.style)
        except OSError:
            # Fallback to default style if seaborn is not available
            plt.style.use("default")

    def legend_without_duplicate_labels(ax):
        handles, labels = ax.get_legend_handles_labels()
        unique = [
            (h, l)
            for i, (h, l) in enumerate(zip(handles, labels))
            if l not in labels[:i]
        ]
        ax.legend(*zip(*unique))

    def create_price_chart_with_signals(
        self,
        market_data: List[MarketData],
        trades: List[Trade],
        title: str = "Price Chart with Entry/Exit Points",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create price chart with enhanced entry/exit signal markers.

        Args:
            market_data: List of market data points
            trades: List of completed trades
            title: Chart title
            save_path: Optional path to save the chart

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        japanize_matplotlib.japanize()

        # Extract price data
        dates = [data.timestamp for data in market_data]
        prices = [data.close for data in market_data]

        # Plot price line
        ax.plot(
            dates, prices, color=self.colors["price_line"], linewidth=1.5, label="Price"
        )

        # Separate entry and exit signals with proper colors
        buy_entries = []  # Buy entries (gray up triangles)
        sell_entries = []  # Sell entries (gray down triangles)
        buy_exits_profit = []  # Buy exits with profit (green down triangles)
        buy_exits_loss = []  # Buy exits with loss (red down triangles)
        sell_exits_profit = []  # Sell exits with profit (green up triangles)
        sell_exits_loss = []  # Sell exits with loss (red up triangles)
        connection_lines = []  # Lines connecting entry and exit

        for trade in trades:
            # Entry signals (always gray)
            if trade.action == OrderAction.BUY:
                buy_entries.append((trade.entry_time, trade.entry_price))
                # Exit signals for buy trades (down triangles)
                if trade.is_profitable:
                    buy_exits_profit.append((trade.exit_time, trade.exit_price))
                else:
                    buy_exits_loss.append((trade.exit_time, trade.exit_price))
            else:  # SELL entry
                sell_entries.append((trade.entry_time, trade.entry_price))
                # Exit signals for sell trades (up triangles)
                if trade.is_profitable:
                    sell_exits_profit.append((trade.exit_time, trade.exit_price))
                else:
                    sell_exits_loss.append((trade.exit_time, trade.exit_price))

            # Add connection line between entry and exit
            connection_lines.append(
                [
                    [trade.entry_time, trade.exit_time],
                    [trade.entry_price, trade.exit_price],
                ]
            )

        # Plot entry signals (gray markers)
        if buy_entries:
            buy_dates, buy_prices = zip(*buy_entries)
            ax.scatter(
                buy_dates,
                buy_prices,
                color=self.colors["entry_signal"],
                marker="^",
                s=80,
                label="Buy Entry",
                zorder=5,
                alpha=0.8,
            )

        if sell_entries:
            sell_dates, sell_prices = zip(*sell_entries)
            ax.scatter(
                sell_dates,
                sell_prices,
                color=self.colors["entry_signal"],
                marker="v",
                s=80,
                label="Sell Entry",
                zorder=5,
                alpha=0.8,
            )

        # Plot exit signals (colored by profit/loss)
        if buy_exits_profit:
            dates, prices = zip(*buy_exits_profit)
            ax.scatter(
                dates,
                prices,
                color=self.colors["exit_profit"],
                marker="v",
                s=80,
                label="Profitable Exit",
                zorder=5,
                alpha=0.8,
            )

        if buy_exits_loss:
            dates, prices = zip(*buy_exits_loss)
            ax.scatter(
                dates,
                prices,
                color=self.colors["exit_loss"],
                marker="v",
                s=80,
                label="Loss Exit",
                zorder=5,
                alpha=0.8,
            )

        if sell_exits_profit:
            dates, prices = zip(*sell_exits_profit)
            ax.scatter(
                dates,
                prices,
                color=self.colors["exit_profit"],
                marker="^",
                s=80,
                label="Profitable Exit",
                zorder=5,
                alpha=0.8,
            )

        if sell_exits_loss:
            dates, prices = zip(*sell_exits_loss)
            ax.scatter(
                dates,
                prices,
                color=self.colors["exit_loss"],
                marker="^",
                s=80,
                label="Loss Exit",
                zorder=5,
                alpha=0.8,
            )

        # Plot connection lines between entry and exit points
        for line_data in connection_lines:
            ax.plot(
                line_data[0],
                line_data[1],
                color=self.colors["connection_line"],
                linestyle="--",
                alpha=0.5,
                linewidth=1,
                zorder=3,
            )

        # Format chart
        japanize_matplotlib.japanize()
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price", fontsize=12)

        # Remove duplicate labels in legend
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), loc="upper left")

        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x:,.0f}"))

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Price chart saved: {save_path}")

        return fig

    def create_equity_curve(
        self,
        portfolio_history: List[Dict[str, Any]],
        title: str = "Equity Curve",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create equity curve showing portfolio value over time.

        Args:
            portfolio_history: List of portfolio snapshots
            title: Chart title
            save_path: Optional path to save the chart

        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        japanize_matplotlib.japanize()

        # Extract data
        dates = [snapshot["timestamp"] for snapshot in portfolio_history]
        values = [snapshot["total_value"] for snapshot in portfolio_history]

        # Plot equity curve
        ax.plot(
            dates,
            values,
            color=self.colors["equity_line"],
            linewidth=2,
            label="Portfolio Value",
        )

        # Add initial capital line for reference
        if values:
            initial_value = values[0]
            ax.axhline(
                y=initial_value,
                color="gray",
                linestyle="--",
                alpha=0.7,
                label=f"Initial Capital (¥{initial_value:,.0f})",
            )

        # Format chart
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Portfolio Value", fontsize=12)
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x:,.0f}"))

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Equity curve saved: {save_path}")

        return fig

    def create_drawdown_chart(
        self,
        portfolio_history: List[Dict[str, Any]],
        title: str = "Drawdown Analysis",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create drawdown chart showing portfolio drawdowns over time.

        Args:
            portfolio_history: List of portfolio snapshots
            title: Chart title
            save_path: Optional path to save the chart

        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(self.figsize[0], self.figsize[1] + 2)
        )
        japanize_matplotlib.japanize()

        # Extract data
        dates = [snapshot["timestamp"] for snapshot in portfolio_history]
        values = [snapshot["total_value"] for snapshot in portfolio_history]

        # Calculate drawdowns
        peak_values = []
        drawdowns = []
        peak = values[0] if values else 0

        for value in values:
            if value > peak:
                peak = value
            peak_values.append(peak)
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            drawdowns.append(drawdown)

        # Plot equity curve with peak line
        ax1.plot(
            dates,
            values,
            color=self.colors["equity_line"],
            linewidth=2,
            label="Portfolio Value",
        )
        ax1.plot(
            dates,
            peak_values,
            color="red",
            linestyle="--",
            alpha=0.7,
            label="Peak Value",
        )
        ax1.set_title(f"{title} - Portfolio Value", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Portfolio Value", fontsize=12)
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x:,.0f}"))

        # Plot drawdown
        ax2.fill_between(
            dates,
            drawdowns,
            0,
            color=self.colors["drawdown_fill"],
            alpha=0.7,
            label="Drawdown",
        )
        ax2.plot(dates, drawdowns, color="red", linewidth=1)
        ax2.set_title("Drawdown Percentage", fontsize=14, fontweight="bold")
        ax2.set_xlabel("Date", fontsize=12)
        ax2.set_ylabel("Drawdown (%)", fontsize=12)
        ax2.legend(loc="lower right")
        ax2.grid(True, alpha=0.3)
        ax2.invert_yaxis()  # Invert y-axis so drawdowns go down

        # Format x-axis dates for both subplots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Drawdown chart saved: {save_path}")

        return fig

    def create_performance_dashboard(
        self,
        backtester: Backtester,
        market_data: List[MarketData],
        strategy_name: str = "Strategy",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create comprehensive performance dashboard with multiple charts.

        Args:
            backtester: Backtester instance with results
            market_data: Market data used in backtesting
            strategy_name: Name of the strategy
            save_path: Optional path to save the dashboard

        Returns:
            Matplotlib figure object
        """
        if not backtester.backtest_result:
            raise ValueError("No backtest results available")

        fig = plt.figure(figsize=(20, 18))  # 高さを増やす
        japanize_matplotlib.japanize()

        # Create subplots
        gs = fig.add_gridspec(
            3, 2, height_ratios=[2, 2, 1.8], hspace=0.4, wspace=0.3
        )  # 下部のスペースを増やし、間隔も広げる

        # 1. Price chart with signals (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        dates = [data.timestamp for data in market_data]
        prices = [data.close for data in market_data]
        ax1.plot(dates, prices, color=self.colors["price_line"], linewidth=1.5)

        # Add enhanced trade signals with proper colors
        trades_data = backtester.get_trade_history()
        trades = [
            Trade(
                entry_price=t["entry_price"],
                exit_price=t["exit_price"],
                quantity=t["quantity"],
                entry_time=t["entry_time"],
                exit_time=t["exit_time"],
                action=OrderAction.BUY if t["action"] == "buy" else OrderAction.SELL,
                order_type=None,
                pnl=t["pnl"],
            )
            for t in trades_data
        ]

        # Separate entry and exit signals with proper colors
        buy_entries = []
        sell_entries = []
        buy_exits_profit = []
        buy_exits_loss = []
        sell_exits_profit = []
        sell_exits_loss = []

        for trade in trades:
            if trade.action == OrderAction.BUY:
                buy_entries.append((trade.entry_time, trade.entry_price))
                if trade.is_profitable:
                    buy_exits_profit.append((trade.exit_time, trade.exit_price))
                else:
                    buy_exits_loss.append((trade.exit_time, trade.exit_price))
            else:
                sell_entries.append((trade.entry_time, trade.entry_price))
                if trade.is_profitable:
                    sell_exits_profit.append((trade.exit_time, trade.exit_price))
                else:
                    sell_exits_loss.append((trade.exit_time, trade.exit_price))

        # Plot entry signals (gray)
        if buy_entries:
            dates, prices = zip(*buy_entries)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["entry_signal"],
                marker="^",
                s=60,
                alpha=0.8,
                zorder=5,
            )
        if sell_entries:
            dates, prices = zip(*sell_entries)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["entry_signal"],
                marker="v",
                s=60,
                alpha=0.8,
                zorder=5,
            )

        # Plot exit signals (colored by profit/loss)
        if buy_exits_profit:
            dates, prices = zip(*buy_exits_profit)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["exit_profit"],
                marker="v",
                s=60,
                alpha=0.8,
                zorder=5,
            )
        if buy_exits_loss:
            dates, prices = zip(*buy_exits_loss)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["exit_loss"],
                marker="v",
                s=60,
                alpha=0.8,
                zorder=5,
            )
        if sell_exits_profit:
            dates, prices = zip(*sell_exits_profit)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["exit_profit"],
                marker="^",
                s=60,
                alpha=0.8,
                zorder=5,
            )
        if sell_exits_loss:
            dates, prices = zip(*sell_exits_loss)
            ax1.scatter(
                dates,
                prices,
                color=self.colors["exit_loss"],
                marker="^",
                s=60,
                alpha=0.8,
                zorder=5,
            )

        ax1.set_title(f"{strategy_name} - Price & Signals", fontweight="bold")
        ax1.set_ylabel("Price")
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x:,.0f}"))

        # 2. Equity curve (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        portfolio_history = backtester.get_portfolio_history()
        eq_dates = [snapshot["timestamp"] for snapshot in portfolio_history]
        eq_values = [snapshot["total_value"] for snapshot in portfolio_history]
        ax2.plot(eq_dates, eq_values, color=self.colors["equity_line"], linewidth=2)

        if eq_values:
            ax2.axhline(y=eq_values[0], color="gray", linestyle="--", alpha=0.7)

        ax2.set_title("Equity Curve", fontweight="bold")
        ax2.set_ylabel("Portfolio Value")
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x:,.0f}"))

        # 3. Drawdown (middle left)
        ax3 = fig.add_subplot(gs[1, 0])

        # Calculate drawdowns
        peak = eq_values[0] if eq_values else 0
        drawdowns = []
        for value in eq_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            drawdowns.append(drawdown)

        ax3.fill_between(
            eq_dates, drawdowns, 0, color=self.colors["drawdown_fill"], alpha=0.7
        )
        ax3.plot(eq_dates, drawdowns, color="red", linewidth=1)
        ax3.set_title("Drawdown Analysis", fontweight="bold")
        ax3.set_ylabel("Drawdown (%)")
        ax3.grid(True, alpha=0.3)
        ax3.invert_yaxis()

        # 4. Monthly returns heatmap (middle right)
        ax4 = fig.add_subplot(gs[1, 1])
        self._create_monthly_returns_heatmap(ax4, portfolio_history)

        # 5. Performance metrics table (bottom)
        ax5 = fig.add_subplot(gs[2, :])
        self._create_performance_table(ax5, backtester.get_performance_summary())

        # Format x-axis dates
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.xaxis.set_major_locator(mdates.YearLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.suptitle(
            f"{strategy_name} - Performance Dashboard", fontsize=20, fontweight="bold"
        )

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Performance dashboard saved: {save_path}")

        return fig

    def _create_monthly_returns_heatmap(
        self, ax: plt.Axes, portfolio_history: List[Dict[str, Any]]
    ) -> None:
        """Create monthly returns heatmap."""
        if len(portfolio_history) < 2:
            ax.text(
                0.5,
                0.5,
                "Insufficient data for monthly returns",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title("Monthly Returns", fontweight="bold")
            return

        # Calculate monthly returns
        monthly_data = {}
        prev_value = portfolio_history[0]["total_value"]
        prev_date = portfolio_history[0]["timestamp"]

        for snapshot in portfolio_history[1:]:
            current_date = snapshot["timestamp"]
            current_value = snapshot["total_value"]

            # Check if we've moved to a new month
            if (
                current_date.month != prev_date.month
                or current_date.year != prev_date.year
            ):
                month_key = f"{prev_date.year}-{prev_date.month:02d}"
                monthly_return = (current_value - prev_value) / prev_value * 100
                monthly_data[month_key] = monthly_return
                prev_value = current_value

            prev_date = current_date

        if not monthly_data:
            ax.text(
                0.5,
                0.5,
                "No monthly data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title("Monthly Returns", fontweight="bold")
            return

        # Create simple bar chart for monthly returns
        months = list(monthly_data.keys())[-12:]  # Last 12 months
        returns = [monthly_data[month] for month in months]

        colors = ["green" if r > 0 else "red" for r in returns]
        bars = ax.bar(range(len(months)), returns, color=colors, alpha=0.7)

        ax.set_title("Monthly Returns (Last 12 Months)", fontweight="bold")
        ax.set_ylabel("Return (%)")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels([m.split("-")[1] for m in months], rotation=45)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="black", linewidth=0.8)

        # Add value labels on bars
        for bar, value in zip(bars, returns):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + (0.5 if height > 0 else -1.5),
                f"{value:.1f}%",
                ha="center",
                va="bottom" if height > 0 else "top",
                fontsize=8,
            )

    def _create_performance_table(
        self, ax: plt.Axes, performance_summary: Dict[str, Any]
    ) -> None:
        """Create performance metrics table."""
        ax.axis("off")

        # Prepare data for table
        metrics = [
            ["総リターン", f"{performance_summary.get('total_return_pct', 0):.2f}%"],
            [
                "年率リターン",
                (
                    f"{performance_summary.get('annualized_return_pct', 0):.2f}%"
                    if performance_summary.get("annualized_return_pct")
                    else "N/A"
                ),
            ],
            [
                "最大ドローダウン",
                f"{performance_summary.get('max_drawdown_pct', 0):.2f}%",
            ],
            [
                "シャープレシオ",
                (
                    f"{performance_summary.get('sharpe_ratio', 0):.3f}"
                    if performance_summary.get("sharpe_ratio")
                    else "N/A"
                ),
            ],
            [
                "プロフィットファクター",
                f"{performance_summary.get('profit_factor', 0):.2f}",
            ],
            ["勝率", f"{performance_summary.get('win_rate_pct', 0):.2f}%"],
            ["総取引数", f"{performance_summary.get('total_trades', 0)}"],
            ["勝ちトレード", f"{performance_summary.get('winning_trades', 0)}"],
            ["負けトレード", f"{performance_summary.get('losing_trades', 0)}"],
            ["純利益", f"¥{performance_summary.get('net_profit', 0):,.0f}"],
        ]

        # Create table
        table = ax.table(
            cellText=metrics,
            colLabels=["指標", "値"],
            cellLoc="center",
            loc="center",
            colWidths=[0.3, 0.2],
        )

        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 1.5)  # 表を大きくして見やすくする

        # Style the table
        for i in range(len(metrics) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # Header row
                    cell.set_facecolor("#4CAF50")
                    cell.set_text_props(weight="bold", color="white")
                else:
                    cell.set_facecolor("#f0f0f0" if i % 2 == 0 else "white")

        ax.set_title("パフォーマンス指標", fontweight="bold", pad=20)

    # def compare_strategies_chart(self, results: Dict[str, Any],
    #                            metric: str = 'total_return',
    #                            title: str = "Strategy Comparison",
    #                            save_path: Optional[str] = None) -> plt.Figure:
    #     """
    #     Create comparison chart for multiple strategies.

    #     Args:
    #         results: Dictionary of strategy results
    #         metric: Metric to compare ('total_return', 'sharpe_ratio', etc.)
    #         title: Chart title
    #         save_path: Optional path to save the chart

    #     Returns:
    #         Matplotlib figure object
    #     """
    #     fig, ax = plt.subplots(2,2, figsize=(12, 8))
    #     japanize_matplotlib.japanize()

    #     strategy_names = list(results.keys())
    #     values = []

    #     for strategy_name, result in results.items():
    #         if hasattr(result, metric):
    #             value = getattr(result, metric)
    #             if metric in ['total_return', 'max_drawdown'] and value is not None:
    #                 value *= 100  # Convert to percentage
    #             values.append(value if value is not None else 0)
    #         else:
    #             values.append(0)

    #     # Create bar chart
    #     bars = ax.bar(strategy_names, values, color=plt.cm.Set3(np.linspace(0, 1, len(strategy_names))))

    #     # Add value labels on bars
    #     for bar, value in zip(bars, values):
    #         height = bar.get_height()
    #         japanize_matplotlib.japanize()
    #         ax.text(bar.get_x() + bar.get_width()/2., height + (height * 0.01),
    #                f'{value:.2f}{"%" if metric in ["total_return", "max_drawdown", "win_rate"] else ""}',
    #                ha='center', va='bottom', fontweight='bold')

    #     japanize_matplotlib.japanize()
    #     ax.set_title(f'{title} - {metric.replace("_", " ").title()}', fontsize=16, fontweight='bold')
    #     ax.set_ylabel(metric.replace("_", " ").title())
    #     plt.xticks(rotation=45, ha='right')
    #     ax.grid(True, alpha=0.3, axis='y')

    #     plt.tight_layout()

    #     if save_path:
    #         fig.savefig(save_path, dpi=300, bbox_inches='tight')
    #         print(f"✅ Strategy comparison chart saved: {save_path}")

    #     return fig

    def compare_strategies_chart(
        self,
        results: Dict[str, Any],
        metrics: List[str] = [
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
        ],
        title: str = "Strategy Comparison",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create comparison chart for multiple strategies with multiple metrics.

        Args:
            results: Dictionary of strategy results
            metrics: List of metrics to compare
            title: Chart title
            save_path: Optional path to save the chart

        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        japanize_matplotlib.japanize()

        # axesを1次元配列に変換
        axes_flat = axes.flatten()

        strategy_names = list(results.keys())
        colors = plt.cm.Set3(np.linspace(0, 1, len(strategy_names)))

        # 各メトリクスに対してサブプロットを作成
        for idx, metric in enumerate(metrics[:4]):  # 最大4つまで
            ax = axes_flat[idx]
            values = []

            # 各戦略の値を取得
            for strategy_name, result in results.items():
                if hasattr(result, metric):
                    value = getattr(result, metric)
                    if metric in ["total_return", "max_drawdown"] and value is not None:
                        value *= 100  # Convert to percentage
                    values.append(value if value is not None else 0)
                else:
                    values.append(0)

            # バーチャートを作成
            bars = ax.bar(strategy_names, values, color=colors, alpha=0.8)

            # 値のラベルをバーの上に追加
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + (abs(height) * 0.01),
                    f'{value:.2f}{"%" if metric in ["total_return", "max_drawdown", "win_rate"] else ""}',
                    ha="center",
                    va="bottom" if height >= 0 else "top",
                    fontweight="bold",
                    fontsize=10,
                )

            # サブプロットの設定
            ax.set_title(
                f'{metric.replace("_", " ").title()}', fontsize=14, fontweight="bold"
            )
            ax.set_ylabel(f'{metric.replace("_", " ").title()}')
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3, axis="y")

            # Y軸の範囲を調整（負の値がある場合）
            if any(v < 0 for v in values):
                y_min = min(values) * 1.1
                y_max = max(values) * 1.1
                ax.set_ylim(y_min, y_max)

        # メインタイトルを設定
        fig.suptitle(title, fontsize=18, fontweight="bold", y=0.98)

        # レイアウトを調整
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)  # メインタイトル用のスペースを確保

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Strategy comparison chart saved: {save_path}")

        return fig

    def save_all_charts(
        self,
        backtester: Backtester,
        market_data: List[MarketData],
        strategy_name: str = "Strategy",
        output_dir: str = "charts",
    ) -> Dict[str, str]:
        """
        Save all available charts to files.

        Args:
            backtester: Backtester instance with results
            market_data: Market data used in backtesting
            strategy_name: Name of the strategy
            output_dir: Directory to save charts

        Returns:
            Dictionary mapping chart types to file paths
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = {}

        try:
            # Price chart with signals
            price_chart_path = os.path.join(
                output_dir, f"{strategy_name}_price_signals_{timestamp}.png"
            )
            trades = [
                Trade(
                    entry_price=t["entry_price"],
                    exit_price=t["exit_price"],
                    quantity=t["quantity"],
                    entry_time=t["entry_time"],
                    exit_time=t["exit_time"],
                    action=(
                        OrderAction.BUY if t["action"] == "buy" else OrderAction.SELL
                    ),
                    order_type=None,
                    pnl=t["pnl"],
                )
                for t in backtester.get_trade_history()
            ]

            japanize_matplotlib.japanize()

            fig1 = self.create_price_chart_with_signals(
                market_data,
                trades,
                f"{strategy_name} - Price & Signals",
                price_chart_path,
            )
            plt.close(fig1)
            saved_files["price_signals"] = price_chart_path

            # Equity curve - drawdownに書いてあるので削除
            # equity_path = os.path.join(output_dir, f"{strategy_name}_equity_curve_{timestamp}.png")
            # fig2 = self.create_equity_curve(backtester.get_portfolio_history(),
            #                               f"{strategy_name} - Equity Curve",
            #                               equity_path)
            # plt.close(fig2)
            # saved_files['equity_curve'] = equity_path

            # Drawdown chart
            drawdown_path = os.path.join(
                output_dir, f"{strategy_name}_equity_and_drawdown_{timestamp}.png"
            )
            fig3 = self.create_drawdown_chart(
                backtester.get_portfolio_history(),
                f"{strategy_name} - Equity and Drawdown Analysis",
                drawdown_path,
            )
            plt.close(fig3)
            saved_files["drawdown"] = drawdown_path

            # Performance dashboard
            dashboard_path = os.path.join(
                output_dir, f"{strategy_name}_dashboard_{timestamp}.png"
            )
            fig4 = self.create_performance_dashboard(
                backtester, market_data, strategy_name, dashboard_path
            )
            plt.close(fig4)
            saved_files["dashboard"] = dashboard_path

        except Exception as e:
            print(f"⚠️ Error saving charts: {e}")

        return saved_files
