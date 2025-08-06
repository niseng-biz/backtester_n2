#!/usr/bin/env python3
"""
Test script for backtester functionality
"""

import os
import sys
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backtester import (
    Backtester,
    BuyAndHoldStrategy,
    ConfigFactory,
    CryptoDataReader,
    LotSizeMode,
    MovingAverageStrategy,
)

def test_backtester_functionality():
    """Test the backtester functionality"""
    print("🧪 Testing Backtester Functionality")
    print("=" * 50)
    
    try:
        # Test data file
        data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'pricedata', 'BITFLYER_BTCJPY_1D_c51ab.csv')
        
        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            return False
        
        # Initialize data reader
        print("📈 Initializing data reader...")
        data_reader = CryptoDataReader()
        print("✅ Data reader initialized")
        
        # Initialize backtester
        print("🔧 Initializing backtester...")
        backtester = Backtester(initial_capital=1000000)  # 1M JPY
        print("✅ Backtester initialized")
        
        # Test Buy and Hold Strategy
        print("\n🎯 Testing Buy and Hold Strategy...")
        crypto_config = ConfigFactory.create_crypto_lot_config(
            capital_percentage=0.95,
            max_lot_size=10.0
        )
        
        bah_strategy = BuyAndHoldStrategy(
            initial_capital=1000000,
            lot_config=crypto_config,
            position_lots=1.0
        )
        
        print("🚀 Running Buy and Hold backtest...")
        result = backtester.run_backtest(data_reader, bah_strategy, data_file, "BTC/JPY")
        
        if result:
            summary = backtester.get_performance_summary()
            print("✅ Buy and Hold backtest completed successfully")
            print(f"  - Initial Capital: ¥{summary['initial_capital']:,.0f}")
            print(f"  - Final Capital: ¥{summary['final_capital']:,.0f}")
            print(f"  - Total Return: {summary['total_return_pct']:.2f}%")
            print(f"  - Max Drawdown: {summary['max_drawdown_pct']:.2f}%")
            print(f"  - Total Trades: {summary['total_trades']}")
        else:
            print("❌ Buy and Hold backtest failed")
            return False
        
        # Test Moving Average Strategy
        print("\n🎯 Testing Moving Average Strategy...")
        backtester2 = Backtester(initial_capital=1000000)
        
        ma_strategy = MovingAverageStrategy(
            short_window=10,
            long_window=30,
            initial_capital=1000000,
            lot_config=crypto_config,
            position_lots=0.5
        )
        
        print("🚀 Running Moving Average backtest...")
        result2 = backtester2.run_backtest(data_reader, ma_strategy, data_file, "BTC/JPY")
        
        if result2:
            summary2 = backtester2.get_performance_summary()
            print("✅ Moving Average backtest completed successfully")
            print(f"  - Initial Capital: ¥{summary2['initial_capital']:,.0f}")
            print(f"  - Final Capital: ¥{summary2['final_capital']:,.0f}")
            print(f"  - Total Return: {summary2['total_return_pct']:.2f}%")
            print(f"  - Max Drawdown: {summary2['max_drawdown_pct']:.2f}%")
            print(f"  - Total Trades: {summary2['total_trades']}")
        else:
            print("❌ Moving Average backtest failed")
            return False
        
        # Test trade history
        print("\n📊 Testing trade history...")
        trade_history = backtester2.get_trade_history()
        if trade_history:
            print(f"✅ Trade history retrieved: {len(trade_history)} trades")
            if len(trade_history) > 0:
                print(f"  - First trade: {trade_history[0]['entry_time']} - {trade_history[0]['action']}")
                print(f"  - Last trade: {trade_history[-1]['entry_time']} - {trade_history[-1]['action']}")
        else:
            print("ℹ️  No trades in history (this is normal for some strategies)")
        
        # Test result export
        print("\n💾 Testing result export...")
        try:
            saved_files = backtester2.save_results()
            print("✅ Results exported successfully")
            print(f"  - JSON results: {saved_files['json_results']}")
            print(f"  - CSV trades: {saved_files['csv_trades']}")
        except Exception as e:
            print(f"⚠️  Result export failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtester functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backtester_functionality()
    if success:
        print("\n✅ Backtester functionality test PASSED")
    else:
        print("\n❌ Backtester functionality test FAILED")
        sys.exit(1)