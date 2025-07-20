#!/usr/bin/env python3
"""
Test script to verify multiple position tracking and visualization.
"""

from backtester.crypto_data_reader import CryptoDataReader
from backtester.strategy import RSIAveragingStrategy
from backtester.backtester import Backtester
from backtester.visualization import VisualizationEngine
from datetime import datetime

def test_multiple_positions():
    """Test multiple position strategy with enhanced visualization."""
    print("🔍 Testing multiple position strategy with enhanced visualization...")
    
    # Create backtester and RSI averaging strategy
    backtester = Backtester(initial_capital=1000000)
    data_reader = CryptoDataReader()
    
    # RSI strategy with multiple positions
    strategy = RSIAveragingStrategy(
        rsi_period=14,
        oversold_levels=[50, 45, 40, 35, 30],  # Multiple entry levels
        overbought_level=60,
        position_size_pct=0.2,  # 20% per position
        max_positions=5,
        initial_capital=1000000
    )
    
    # Run backtest
    data_file = 'pricedata/BITFLYER_BTCJPY_1D_c51ab.csv'
    result = backtester.run_backtest(data_reader, strategy, data_file)
    
    # Load market data for visualization
    market_data = data_reader.load_data(data_file)
    
    # Create visualization
    viz = VisualizationEngine()
    
    # Generate charts
    saved_files = viz.save_all_charts(backtester, market_data, 'RSIナンピング_修正版', 'charts')
    print(f"✅ Charts saved: {list(saved_files.keys())}")
    
    # Check trade details
    trades = backtester.portfolio_manager.trade_history
    print(f"Total completed trades: {len(trades)}")
    
    if trades:
        profitable_trades = [t for t in trades if t.pnl > 0]
        loss_trades = [t for t in trades if t.pnl <= 0]
        print(f"Profitable trades: {len(profitable_trades)}")
        print(f"Loss trades: {len(loss_trades)}")
        
        # Show first few trades
        print("\nFirst 3 completed trades:")
        for i, trade in enumerate(trades[:3]):
            entry_date = trade.entry_time.strftime('%Y-%m-%d')
            exit_date = trade.exit_time.strftime('%Y-%m-%d')
            profit_status = "利益" if trade.pnl > 0 else "損失"
            print(f"  {i+1}: {trade.action.value} {entry_date} -> {exit_date}, {profit_status}: ¥{trade.pnl:,.0f}")
    else:
        print("No completed trades found")
    
    # Check strategy-specific info
    position_info = strategy.get_position_info()
    print(f"\n📊 Strategy info:")
    print(f"  - Max positions: {position_info.get('max_positions', 'N/A')}")
    print(f"  - Last RSI: {position_info.get('last_rsi', 'N/A')}")
    print(f"  - Positions opened: {position_info.get('positions_opened', 'N/A')}")

if __name__ == "__main__":
    test_multiple_positions()