"""
Unit tests for visualization engine.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

from backtester.visualization import VisualizationEngine
from backtester.models import MarketData, Trade, OrderAction, OrderType
from backtester.backtester import Backtester


class TestVisualizationEngine(unittest.TestCase):
    """Test cases for VisualizationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viz_engine = VisualizationEngine()
        
        # Create sample market data
        base_date = datetime(2023, 1, 1)
        self.market_data = []
        for i in range(100):
            self.market_data.append(MarketData(
                timestamp=base_date + timedelta(days=i),
                open=100 + i * 0.5,
                high=105 + i * 0.5,
                low=95 + i * 0.5,
                close=102 + i * 0.5,
                volume=1000
            ))
        
        # Create sample trades
        self.trades = [
            Trade(
                entry_price=100,
                exit_price=110,
                quantity=10,
                entry_time=base_date + timedelta(days=10),
                exit_time=base_date + timedelta(days=20),
                action=OrderAction.BUY,
                order_type=OrderType.MARKET,
                pnl=100
            ),
            Trade(
                entry_price=120,
                exit_price=115,
                quantity=8,
                entry_time=base_date + timedelta(days=30),
                exit_time=base_date + timedelta(days=40),
                action=OrderAction.SELL,
                order_type=OrderType.MARKET,
                pnl=-40
            )
        ]
        
        # Create sample portfolio history
        self.portfolio_history = []
        for i in range(100):
            self.portfolio_history.append({
                'timestamp': base_date + timedelta(days=i),
                'total_value': 100000 + i * 100,
                'cash': 50000,
                'realized_pnl': i * 10,
                'unrealized_pnl': i * 5,
                'total_pnl': i * 15,
                'num_positions': 1,
                'total_trades': i // 10
            })
    
    def test_initialization(self):
        """Test VisualizationEngine initialization."""
        viz = VisualizationEngine()
        self.assertIsNotNone(viz.colors)
        self.assertEqual(viz.figsize, (15, 10))
        
        # Test custom initialization
        viz_custom = VisualizationEngine(style='default', figsize=(12, 8))
        self.assertEqual(viz_custom.figsize, (12, 8))
    
    def test_create_price_chart_with_signals(self):
        """Test price chart creation with trading signals."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig = self.viz_engine.create_price_chart_with_signals(
                self.market_data, 
                self.trades,
                title="Test Price Chart",
                save_path=tmp_file.name
            )
            
            self.assertIsNotNone(fig)
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Close figure before cleanup
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except PermissionError:
                pass  # Ignore permission errors on Windows
    
    def test_create_equity_curve(self):
        """Test equity curve creation."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig = self.viz_engine.create_equity_curve(
                self.portfolio_history,
                title="Test Equity Curve",
                save_path=tmp_file.name
            )
            
            self.assertIsNotNone(fig)
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Close figure before cleanup
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except PermissionError:
                pass  # Ignore permission errors on Windows
    
    def test_create_drawdown_chart(self):
        """Test drawdown chart creation."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig = self.viz_engine.create_drawdown_chart(
                self.portfolio_history,
                title="Test Drawdown Chart",
                save_path=tmp_file.name
            )
            
            self.assertIsNotNone(fig)
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Close figure before cleanup
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except PermissionError:
                pass  # Ignore permission errors on Windows
    
    def test_create_performance_dashboard(self):
        """Test performance dashboard creation."""
        # Mock backtester
        mock_backtester = Mock(spec=Backtester)
        mock_backtester.backtest_result = Mock()
        mock_backtester.get_trade_history.return_value = [
            {
                'entry_time': datetime(2023, 1, 10),
                'entry_price': 100,
                'exit_price': 110,
                'action': 'buy',
                'pnl': 100
            }
        ]
        mock_backtester.get_portfolio_history.return_value = self.portfolio_history
        mock_backtester.get_performance_summary.return_value = {
            'total_return_pct': 50.0,
            'annualized_return_pct': 25.0,
            'max_drawdown_pct': 10.0,
            'sharpe_ratio': 1.5,
            'profit_factor': 2.0,
            'win_rate_pct': 60.0,
            'total_trades': 10,
            'winning_trades': 6,
            'losing_trades': 4,
            'net_profit': 50000
        }
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig = self.viz_engine.create_performance_dashboard(
                mock_backtester,
                self.market_data,
                strategy_name="Test Strategy",
                save_path=tmp_file.name
            )
            
            self.assertIsNotNone(fig)
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Close figure before cleanup
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except PermissionError:
                pass  # Ignore permission errors on Windows
    
    def test_compare_strategies_chart(self):
        """Test strategy comparison chart creation."""
        # Mock results
        mock_results = {
            'Strategy A': Mock(total_return=0.5, sharpe_ratio=1.2, max_drawdown=0.1),
            'Strategy B': Mock(total_return=0.3, sharpe_ratio=1.0, max_drawdown=0.15),
            'Strategy C': Mock(total_return=0.7, sharpe_ratio=1.5, max_drawdown=0.08)
        }
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig = self.viz_engine.compare_strategies_chart(
                mock_results,
                metric='total_return',
                title="Test Strategy Comparison",
                save_path=tmp_file.name
            )
            
            self.assertIsNotNone(fig)
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Close figure before cleanup
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Clean up
            try:
                os.unlink(tmp_file.name)
            except PermissionError:
                pass  # Ignore permission errors on Windows
    
    def test_save_all_charts(self):
        """Test saving all charts functionality."""
        # Mock backtester
        mock_backtester = Mock(spec=Backtester)
        mock_backtester.backtest_result = Mock()
        mock_backtester.get_trade_history.return_value = [
            {
                'entry_time': datetime(2023, 1, 10),
                'entry_price': 100,
                'exit_price': 110,
                'exit_time': datetime(2023, 1, 20),
                'action': 'buy',
                'quantity': 10,
                'pnl': 100
            }
        ]
        mock_backtester.get_portfolio_history.return_value = self.portfolio_history
        mock_backtester.get_performance_summary.return_value = {
            'total_return_pct': 50.0,
            'annualized_return_pct': 25.0,
            'max_drawdown_pct': 10.0,
            'sharpe_ratio': 1.5,
            'profit_factor': 2.0,
            'win_rate_pct': 60.0,
            'total_trades': 10,
            'winning_trades': 6,
            'losing_trades': 4,
            'net_profit': 50000
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved_files = self.viz_engine.save_all_charts(
                mock_backtester,
                self.market_data,
                strategy_name="TestStrategy",
                output_dir=tmp_dir
            )
            
            self.assertIsInstance(saved_files, dict)
            self.assertIn('price_signals', saved_files)
            self.assertIn('equity_curve', saved_files)
            self.assertIn('drawdown', saved_files)
            self.assertIn('dashboard', saved_files)
            
            # Verify files exist
            for file_path in saved_files.values():
                self.assertTrue(os.path.exists(file_path))
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        # Test with empty market data
        fig = self.viz_engine.create_price_chart_with_signals([], [])
        self.assertIsNotNone(fig)
        
        # Test with empty portfolio history
        fig = self.viz_engine.create_equity_curve([])
        self.assertIsNotNone(fig)
        
        # Test with empty trades
        fig = self.viz_engine.create_price_chart_with_signals(self.market_data, [])
        self.assertIsNotNone(fig)
    
    def test_color_configuration(self):
        """Test color configuration."""
        self.assertIn('buy_signal', self.viz_engine.colors)
        self.assertIn('sell_signal', self.viz_engine.colors)
        self.assertIn('price_line', self.viz_engine.colors)
        self.assertIn('equity_line', self.viz_engine.colors)
        
        # Test that colors are valid hex codes or color names
        for color in self.viz_engine.colors.values():
            self.assertIsInstance(color, str)
            self.assertTrue(len(color) > 0)


if __name__ == '__main__':
    unittest.main()