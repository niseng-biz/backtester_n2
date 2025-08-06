"""
Unit tests for analytics engine.
"""

from datetime import datetime, timedelta

import pytest

from backtester.analytics import AnalyticsEngine
from backtester.models import OrderAction, OrderType, Trade


class TestAnalyticsEngine:
    """Test cases for AnalyticsEngine class."""
    
    def create_sample_trades(self) -> list:
        """Create sample trades for testing."""
        trades = []
        
        # Profitable trade
        trade1 = Trade(
            entry_price=100.0, exit_price=110.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        trades.append(trade1)
        
        # Losing trade
        trade2 = Trade(
            entry_price=100.0, exit_price=90.0, quantity=100,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        trades.append(trade2)
        
        # Another profitable trade
        trade3 = Trade(
            entry_price=100.0, exit_price=120.0, quantity=50,
            entry_time=datetime.now(), exit_time=datetime.now(),
            action=OrderAction.BUY, order_type=OrderType.MARKET
        )
        trades.append(trade3)
        
        return trades
    
    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        trades = self.create_sample_trades()
        
        # Expected: gross_profit = 1000 + 1000 = 2000, gross_loss = 1000
        # Profit factor = 2000 / 1000 = 2.0
        profit_factor = AnalyticsEngine.calculate_profit_factor(trades)
        assert profit_factor == 2.0
        
        # Test with empty trades
        assert AnalyticsEngine.calculate_profit_factor([]) == 0.0
        
        # Test with only profitable trades
        profitable_trades = [trades[0], trades[2]]
        profit_factor = AnalyticsEngine.calculate_profit_factor(profitable_trades)
        assert profit_factor == float('inf')
        
        # Test with only losing trades
        losing_trades = [trades[1]]
        profit_factor = AnalyticsEngine.calculate_profit_factor(losing_trades)
        assert profit_factor == 0.0
    
    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        trades = self.create_sample_trades()
        
        # 2 winning trades out of 3 total = 2/3 ≈ 0.667
        win_rate = AnalyticsEngine.calculate_win_rate(trades)
        assert abs(win_rate - 2/3) < 0.001
        
        # Test with empty trades
        assert AnalyticsEngine.calculate_win_rate([]) == 0.0
        
        # Test with all winning trades
        profitable_trades = [trades[0], trades[2]]
        win_rate = AnalyticsEngine.calculate_win_rate(profitable_trades)
        assert win_rate == 1.0
        
        # Test with all losing trades
        losing_trades = [trades[1]]
        win_rate = AnalyticsEngine.calculate_win_rate(losing_trades)
        assert win_rate == 0.0
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        # Create sample returns (daily)
        returns = [0.01, -0.005, 0.02, -0.01, 0.015, 0.008, -0.003]
        
        sharpe_ratio = AnalyticsEngine.calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        
        # Should return a numeric value
        assert sharpe_ratio is not None
        assert isinstance(sharpe_ratio, float)
        
        # Test with insufficient data
        assert AnalyticsEngine.calculate_sharpe_ratio([0.01]) is None
        assert AnalyticsEngine.calculate_sharpe_ratio([]) is None
        
        # Test with zero volatility
        zero_vol_returns = [0.01] * 10
        sharpe_ratio = AnalyticsEngine.calculate_sharpe_ratio(zero_vol_returns)
        # With constant returns, std dev approaches zero, so Sharpe ratio becomes very large
        assert sharpe_ratio is None or abs(sharpe_ratio) > 1000
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        # Portfolio values with a clear drawdown
        portfolio_values = [100000, 110000, 105000, 95000, 120000, 115000]
        
        max_dd, peak_idx, trough_idx = AnalyticsEngine.calculate_max_drawdown(portfolio_values)
        
        # Maximum drawdown should be from 110000 to 95000 = 13.64%
        expected_dd = (110000 - 95000) / 110000
        assert abs(max_dd - expected_dd) < 0.001
        assert peak_idx == 1  # Index of 110000
        assert trough_idx == 3  # Index of 95000
        
        # Test with insufficient data
        max_dd, _, _ = AnalyticsEngine.calculate_max_drawdown([100000])
        assert max_dd == 0.0
        
        # Test with always increasing values
        increasing_values = [100000, 110000, 120000, 130000]
        max_dd, _, _ = AnalyticsEngine.calculate_max_drawdown(increasing_values)
        assert max_dd == 0.0
    
    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        # Mix of positive and negative returns
        returns = [0.02, -0.01, 0.015, -0.02, 0.01, 0.005, -0.005]
        
        sortino_ratio = AnalyticsEngine.calculate_sortino_ratio(returns, risk_free_rate=0.02)
        
        # Should return a numeric value
        assert sortino_ratio is not None
        assert isinstance(sortino_ratio, float)
        
        # Test with no negative returns
        positive_returns = [0.01, 0.02, 0.015, 0.008]
        sortino_ratio = AnalyticsEngine.calculate_sortino_ratio(positive_returns)
        assert sortino_ratio == float('inf')
        
        # Test with insufficient data
        assert AnalyticsEngine.calculate_sortino_ratio([0.01]) is None
    
    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        total_return = 0.15  # 15% total return
        max_drawdown = 0.05  # 5% max drawdown
        years = 1.0
        
        calmar_ratio = AnalyticsEngine.calculate_calmar_ratio(total_return, max_drawdown, years)
        
        # Calmar ratio = annualized return / max drawdown = 0.15 / 0.05 = 3.0
        assert abs(calmar_ratio - 3.0) < 0.001
        
        # Test with zero drawdown
        assert AnalyticsEngine.calculate_calmar_ratio(0.15, 0.0, 1.0) is None
        
        # Test with zero years
        assert AnalyticsEngine.calculate_calmar_ratio(0.15, 0.05, 0.0) is None
    
    def test_calculate_var(self):
        """Test Value at Risk calculation."""
        returns = [-0.05, -0.02, 0.01, 0.03, -0.01, 0.02, -0.03, 0.015, -0.008, 0.025]
        
        # 5% VaR (95th percentile of losses)
        var_5 = AnalyticsEngine.calculate_var(returns, confidence_level=0.05)
        
        # Should return the 5th percentile (worst 5% of returns)
        assert var_5 is not None
        assert var_5 < 0  # Should be negative (a loss)
        
        # Test with empty returns
        assert AnalyticsEngine.calculate_var([]) is None
    
    def test_calculate_beta(self):
        """Test beta calculation."""
        # Strategy returns that are more volatile than benchmark
        strategy_returns = [0.02, -0.015, 0.03, -0.02, 0.025]
        benchmark_returns = [0.01, -0.008, 0.015, -0.01, 0.012]
        
        beta = AnalyticsEngine.calculate_beta(strategy_returns, benchmark_returns)
        
        # Should return a positive beta (strategy moves with benchmark)
        assert beta is not None
        assert beta > 0
        
        # Test with mismatched lengths
        assert AnalyticsEngine.calculate_beta([0.01], [0.01, 0.02]) is None
        
        # Test with insufficient data
        assert AnalyticsEngine.calculate_beta([0.01], [0.01]) is None
        
        # Test with zero benchmark variance
        zero_var_benchmark = [0.01] * 5
        assert AnalyticsEngine.calculate_beta(strategy_returns, zero_var_benchmark) is None
    
    def test_calculate_alpha(self):
        """Test alpha calculation."""
        strategy_returns = [0.02, -0.01, 0.025, -0.015, 0.02]
        benchmark_returns = [0.015, -0.008, 0.02, -0.012, 0.015]
        
        alpha = AnalyticsEngine.calculate_alpha(strategy_returns, benchmark_returns, risk_free_rate=0.02)
        
        # Should return a numeric alpha value
        assert alpha is not None
        assert isinstance(alpha, float)
        
        # Test with insufficient data
        assert AnalyticsEngine.calculate_alpha([0.01], [0.01]) is None
    
    def test_calculate_information_ratio(self):
        """Test information ratio calculation."""
        strategy_returns = [0.02, -0.01, 0.025, -0.015, 0.02]
        benchmark_returns = [0.015, -0.008, 0.02, -0.012, 0.015]
        
        info_ratio = AnalyticsEngine.calculate_information_ratio(strategy_returns, benchmark_returns)
        
        # Should return a numeric value
        assert info_ratio is not None
        assert isinstance(info_ratio, float)
        
        # Test with identical returns (zero tracking error)
        identical_returns = [0.01, 0.02, 0.015]
        assert AnalyticsEngine.calculate_information_ratio(identical_returns, identical_returns) is None
    
    def test_generate_backtest_result(self):
        """Test backtest result generation."""
        trades = self.create_sample_trades()
        portfolio_history = [100000, 101000, 99000, 102000, 105000]
        
        result = AnalyticsEngine.generate_backtest_result(
            initial_capital=100000,
            final_capital=105000,
            trades=trades,
            portfolio_history=portfolio_history
        )
        
        # Check basic properties
        assert result.initial_capital == 100000
        assert result.final_capital == 105000
        assert result.total_trades == 3
        assert result.winning_trades == 2
        assert result.losing_trades == 1
        assert result.profit_factor == 2.0
        assert abs(result.win_rate - 2/3) < 0.001
        assert result.total_return == 0.05  # 5% return
        assert result.max_drawdown > 0  # Should have some drawdown
        
        # Check that trades and history are copied
        assert len(result.trades) == 3
        assert len(result.portfolio_history) == 5
    
    def test_calculate_trade_statistics(self):
        """Test detailed trade statistics calculation."""
        trades = self.create_sample_trades()
        
        stats = AnalyticsEngine.calculate_trade_statistics(trades)
        
        assert stats['total_trades'] == 3
        assert stats['winning_trades'] == 2
        assert stats['losing_trades'] == 1
        assert abs(stats['win_rate'] - 2/3) < 0.001
        assert stats['average_win'] == 1000.0  # Both winning trades have 1000 P&L
        assert stats['average_loss'] == -1000.0
        assert stats['largest_win'] == 1000.0
        assert stats['largest_loss'] == -1000.0
        assert stats['profit_factor'] == 2.0
        assert stats['expectancy'] > 0  # Should be positive expectancy
        
        # Test with empty trades
        empty_stats = AnalyticsEngine.calculate_trade_statistics([])
        assert empty_stats['total_trades'] == 0
        assert empty_stats['win_rate'] == 0.0
        assert empty_stats['profit_factor'] == 0.0
    
    def test_calculate_monthly_returns(self):
        """Test monthly returns calculation."""
        # Create portfolio history spanning multiple months
        portfolio_history = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(90):  # 3 months of daily data
            date = base_date + timedelta(days=i)
            value = 100000 + i * 100  # Steadily increasing
            portfolio_history.append((date, value))
        
        monthly_returns = AnalyticsEngine.calculate_monthly_returns(portfolio_history)
        
        # Should have returns for 2023
        assert '2023' in monthly_returns
        assert len(monthly_returns['2023']) > 0
        
        # All returns should be positive (steadily increasing portfolio)
        for year_returns in monthly_returns.values():
            for monthly_return in year_returns:
                assert monthly_return > 0
        
        # Test with insufficient data
        short_history = [(datetime.now(), 100000)]
        monthly_returns = AnalyticsEngine.calculate_monthly_returns(short_history)
        assert monthly_returns == {}