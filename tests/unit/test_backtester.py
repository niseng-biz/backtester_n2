"""
Unit tests for main backtester engine.
"""

import pytest
import os
from datetime import datetime, timedelta
from backtester.backtester import Backtester
from backtester.data_reader import CSVDataReader
from backtester.strategy import BuyAndHoldStrategy, MovingAverageStrategy
from backtester.models import MarketData


class TestBacktester:
    """Test cases for Backtester class."""
    
    def test_backtester_initialization(self):
        """Test backtester initialization."""
        backtester = Backtester(50000.0)
        
        assert backtester.initial_capital == 50000.0
        assert backtester.portfolio_manager.initial_capital == 50000.0
        assert backtester.is_running is False
        assert backtester.current_data_index == 0
        assert len(backtester.market_data) == 0
        assert backtester.strategy is None
        assert backtester.backtest_result is None
    
    def test_run_backtest_buy_and_hold(self, stock_lot_config, temp_csv_file):
        """Test running backtest with buy-and-hold strategy."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=stock_lot_config)
        
        result = backtester.run_backtest(data_reader, strategy, temp_csv_file)
        
        # Check that backtest completed
        assert result is not None
        assert result.initial_capital == 100000.0
        assert result.final_capital > 0
        # Note: BuyAndHold may not generate completed trades in short test data
        # but should show portfolio value changes
        assert result.final_capital != result.initial_capital
        
        # Check that portfolio history was recorded
        portfolio_history = backtester.get_portfolio_history()
        assert len(portfolio_history) > 0
        
        # Check performance summary
        summary = backtester.get_performance_summary()
        assert 'total_return' in summary
        assert 'max_drawdown' in summary
        assert 'total_trades' in summary
    
    def test_run_backtest_moving_average(self, temp_csv_file):
        """Test running backtest with moving average strategy."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = MovingAverageStrategy(short_window=2, long_window=4, initial_capital=100000.0)
        
        result = backtester.run_backtest(data_reader, strategy, temp_csv_file)
        
        # Check that backtest completed
        assert result is not None
        assert result.initial_capital == 100000.0
        assert result.final_capital > 0
        
        # Moving average strategy might not trade if conditions aren't met
        assert result.total_trades >= 0
    
    def test_get_current_status(self, temp_csv_file):
        """Test getting current backtesting status."""
        backtester = Backtester(100000.0)
        
        # Initial status
        status = backtester.get_current_status()
        assert status['status'] == 'not_started'
        assert status['progress'] == 0.0
        assert status['current_value'] == 100000.0
        
        # After loading data but before running
        data_reader = CSVDataReader()
        backtester.market_data = data_reader.load_data(temp_csv_file)
        status = backtester.get_current_status()
        assert status['status'] == 'ready'
        assert status['total_data_points'] > 0
    
    def test_get_trade_history(self, crypto_lot_config, temp_csv_file):
        """Test getting formatted trade history."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=crypto_lot_config)
        
        backtester.run_backtest(data_reader, strategy, temp_csv_file)
        
        trade_history = backtester.get_trade_history()
        
        # Trade history should be a list (may be empty for buy-and-hold with short data)
        assert isinstance(trade_history, list)
        
        # Check trade format
        if trade_history:
            trade = trade_history[0]
            required_fields = ['entry_time', 'exit_time', 'action', 'order_type', 
                             'quantity', 'entry_price', 'exit_price', 'pnl', 'return_pct']
            for field in required_fields:
                assert field in trade
    
    def test_get_portfolio_history(self, stock_lot_config, temp_csv_file):
        """Test getting portfolio history."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=stock_lot_config)
        
        backtester.run_backtest(data_reader, strategy, temp_csv_file)
        
        portfolio_history = backtester.get_portfolio_history()
        
        # Should have portfolio snapshots
        assert len(portfolio_history) > 0
        
        # Check snapshot format
        snapshot = portfolio_history[0]
        required_fields = ['timestamp', 'total_value', 'cash', 'realized_pnl', 
                         'unrealized_pnl', 'total_pnl', 'num_positions', 'total_trades']
        for field in required_fields:
            assert field in snapshot
    
    def test_export_results_json(self, stock_lot_config, temp_csv_file, tmp_path):
        """Test exporting results to JSON."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=stock_lot_config)
        
        json_file = tmp_path / "test_results.json"
        
        backtester.run_backtest(data_reader, strategy, temp_csv_file)
        backtester.export_results(str(json_file), 'json')
        
        # Check that file was created
        assert json_file.exists()
        
        # Check file content
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert 'summary' in data
        assert 'trades' in data
        assert 'portfolio_history' in data
        assert 'strategy_name' in data
    
    def test_export_results_csv(self, stock_lot_config, temp_csv_file, tmp_path):
        """Test exporting results to CSV."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=stock_lot_config)
        
        csv_export_file = tmp_path / "test_results.csv"
        
        backtester.run_backtest(data_reader, strategy, temp_csv_file)
        backtester.export_results(str(csv_export_file), 'csv')
        
        # Check that file was created
        assert csv_export_file.exists()
        
        # Check file content
        with open(csv_export_file, 'r') as f:
            content = f.read()
            assert 'entry_time' in content  # Should have header
            assert 'pnl' in content
    
    def test_export_results_no_backtest(self):
        """Test exporting results when no backtest has been run."""
        backtester = Backtester()
        
        with pytest.raises(ValueError, match="No backtest results available"):
            backtester.export_results("test.json")
    
    def test_export_results_invalid_format(self, stock_lot_config, temp_csv_file):
        """Test exporting results with invalid format."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = BuyAndHoldStrategy(100000.0, lot_config=stock_lot_config)
        
        backtester.run_backtest(data_reader, strategy, temp_csv_file)
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            backtester.export_results("test.xml", "xml")
    
    def test_compare_strategies(self, stock_lot_config, temp_csv_file):
        """Test comparing multiple strategies."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = stock_lot_config
        
        strategies = [
            BuyAndHoldStrategy(100000.0, lot_config=lot_config),
            MovingAverageStrategy(short_window=2, long_window=4, initial_capital=100000.0, lot_config=lot_config)
        ]
        
        results = backtester.compare_strategies(strategies, data_reader, temp_csv_file)
        
        # Should have results for both strategies
        assert len(results) == 2
        assert "Buy and Hold" in results
        assert "Moving Average (2/4)" in results
        
        # Each result should be a BacktestResult
        for strategy_name, result in results.items():
            assert result.initial_capital == 100000.0
            assert result.final_capital > 0
    
    def test_stop_backtest(self):
        """Test stopping a running backtest."""
        backtester = Backtester()
        
        # Initially not running
        assert backtester.is_running is False
        
        # Start running state
        backtester.is_running = True
        assert backtester.is_running is True
        
        # Stop backtest
        backtester.stop_backtest()
        assert backtester.is_running is False
    
    def test_set_progress_callback(self):
        """Test setting progress callback."""
        backtester = Backtester()
        
        callback_calls = []
        
        def progress_callback(current, total):
            callback_calls.append((current, total))
        
        backtester.set_progress_callback(progress_callback)
        assert backtester.progress_callback is not None
        
        # Test callback
        backtester.progress_callback(50, 100)
        assert len(callback_calls) == 1
        assert callback_calls[0] == (50, 100)