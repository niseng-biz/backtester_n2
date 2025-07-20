"""
Unit tests for main backtester engine.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from backtester.backtester import Backtester
from backtester.data_reader import CSVDataReader
from backtester.strategy import BuyAndHoldStrategy, MovingAverageStrategy
from backtester.models import MarketData


class TestBacktester:
    """Test cases for Backtester class."""
    
    def create_test_csv_data(self) -> str:
        """Create test CSV data file."""
        csv_content = """Date,Open,High,Low,Close,Volume
2023-01-01,100.0,105.0,95.0,102.0,1000
2023-01-02,102.0,108.0,100.0,106.0,1200
2023-01-03,106.0,110.0,104.0,108.0,1100
2023-01-04,108.0,112.0,106.0,110.0,1300
2023-01-05,110.0,115.0,108.0,112.0,1400
2023-01-06,112.0,116.0,110.0,114.0,1500
2023-01-07,114.0,118.0,112.0,116.0,1600
2023-01-08,116.0,120.0,114.0,118.0,1700
2023-01-09,118.0,122.0,116.0,120.0,1800
2023-01-10,120.0,125.0,118.0,122.0,1900"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name
    
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
    
    def test_run_backtest_buy_and_hold(self):
        """Test running backtest with buy-and-hold strategy."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_file = self.create_test_csv_data()
        
        try:
            result = backtester.run_backtest(data_reader, strategy, csv_file)
            
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
            
        finally:
            os.unlink(csv_file)
    
    def test_run_backtest_moving_average(self):
        """Test running backtest with moving average strategy."""
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        strategy = MovingAverageStrategy(short_window=2, long_window=4, initial_capital=100000.0)
        
        csv_file = self.create_test_csv_data()
        
        try:
            result = backtester.run_backtest(data_reader, strategy, csv_file)
            
            # Check that backtest completed
            assert result is not None
            assert result.initial_capital == 100000.0
            assert result.final_capital > 0
            
            # Moving average strategy might not trade if conditions aren't met
            assert result.total_trades >= 0
            
        finally:
            os.unlink(csv_file)
    
    def test_get_current_status(self):
        """Test getting current backtesting status."""
        backtester = Backtester(100000.0)
        
        # Initial status
        status = backtester.get_current_status()
        assert status['status'] == 'not_started'
        assert status['progress'] == 0.0
        assert status['current_value'] == 100000.0
        
        # After loading data but before running
        data_reader = CSVDataReader()
        csv_file = self.create_test_csv_data()
        
        try:
            backtester.market_data = data_reader.load_data(csv_file)
            status = backtester.get_current_status()
            assert status['status'] == 'ready'
            assert status['total_data_points'] > 0
            
        finally:
            os.unlink(csv_file)
    
    def test_get_trade_history(self):
        """Test getting formatted trade history."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_file = self.create_test_csv_data()
        
        try:
            backtester.run_backtest(data_reader, strategy, csv_file)
            
            trade_history = backtester.get_trade_history()
            
            # Should have at least one trade (buy-and-hold buys at start)
            assert len(trade_history) >= 1
            
            # Check trade format
            if trade_history:
                trade = trade_history[0]
                required_fields = ['entry_time', 'exit_time', 'action', 'order_type', 
                                 'quantity', 'entry_price', 'exit_price', 'pnl', 'return_pct']
                for field in required_fields:
                    assert field in trade
            
        finally:
            os.unlink(csv_file)
    
    def test_get_portfolio_history(self):
        """Test getting portfolio history."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_file = self.create_test_csv_data()
        
        try:
            backtester.run_backtest(data_reader, strategy, csv_file)
            
            portfolio_history = backtester.get_portfolio_history()
            
            # Should have portfolio snapshots
            assert len(portfolio_history) > 0
            
            # Check snapshot format
            snapshot = portfolio_history[0]
            required_fields = ['timestamp', 'total_value', 'cash', 'realized_pnl', 
                             'unrealized_pnl', 'total_pnl', 'num_positions', 'total_trades']
            for field in required_fields:
                assert field in snapshot
            
        finally:
            os.unlink(csv_file)
    
    def test_export_results_json(self):
        """Test exporting results to JSON."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_file = self.create_test_csv_data()
        json_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False).name
        
        try:
            backtester.run_backtest(data_reader, strategy, csv_file)
            backtester.export_results(json_file, 'json')
            
            # Check that file was created
            assert os.path.exists(json_file)
            
            # Check file content
            import json
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            assert 'summary' in data
            assert 'trades' in data
            assert 'portfolio_history' in data
            assert 'strategy_name' in data
            
        finally:
            os.unlink(csv_file)
            if os.path.exists(json_file):
                os.unlink(json_file)
    
    def test_export_results_csv(self):
        """Test exporting results to CSV."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_data_file = self.create_test_csv_data()
        csv_export_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        
        try:
            backtester.run_backtest(data_reader, strategy, csv_data_file)
            backtester.export_results(csv_export_file, 'csv')
            
            # Check that file was created
            assert os.path.exists(csv_export_file)
            
            # Check file content
            with open(csv_export_file, 'r') as f:
                content = f.read()
                assert 'entry_time' in content  # Should have header
                assert 'pnl' in content
            
        finally:
            os.unlink(csv_data_file)
            if os.path.exists(csv_export_file):
                os.unlink(csv_export_file)
    
    def test_export_results_no_backtest(self):
        """Test exporting results when no backtest has been run."""
        backtester = Backtester()
        
        with pytest.raises(ValueError, match="No backtest results available"):
            backtester.export_results("test.json")
    
    def test_export_results_invalid_format(self):
        """Test exporting results with invalid format."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        strategy = BuyAndHoldStrategy(100000.0, lot_config=lot_config)
        
        csv_file = self.create_test_csv_data()
        
        try:
            backtester.run_backtest(data_reader, strategy, csv_file)
            
            with pytest.raises(ValueError, match="Unsupported export format"):
                backtester.export_results("test.xml", "xml")
            
        finally:
            os.unlink(csv_file)
    
    def test_compare_strategies(self):
        """Test comparing multiple strategies."""
        from backtester.models import LotConfig
        
        backtester = Backtester(100000.0)
        data_reader = CSVDataReader()
        lot_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
        
        strategies = [
            BuyAndHoldStrategy(100000.0, lot_config=lot_config),
            MovingAverageStrategy(short_window=2, long_window=4, initial_capital=100000.0, lot_config=lot_config)
        ]
        
        csv_file = self.create_test_csv_data()
        
        try:
            results = backtester.compare_strategies(strategies, data_reader, csv_file)
            
            # Should have results for both strategies
            assert len(results) == 2
            assert "Buy and Hold" in results
            assert "Moving Average (2/4)" in results
            
            # Each result should be a BacktestResult
            for strategy_name, result in results.items():
                assert result.initial_capital == 100000.0
                assert result.final_capital > 0
            
        finally:
            os.unlink(csv_file)
    
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