#!/usr/bin/env python3
"""
Test LOT-based position sizing functionality.
Demonstrates trading with 0.1 and 0.01 LOT sizes.
"""

from backtester.models import LotConfig, Order, OrderType, OrderAction
from backtester.strategy import MovingAverageStrategy, RSIAveragingStrategy
from backtester.crypto_data_reader import CryptoDataReader
from backtester.backtester import Backtester
import datetime

def test_lot_config():
    """Test LOT configuration functionality."""
    print("🧪 LOT設定機能をテスト...")
    
    # Test different asset types
    stock_config = LotConfig(asset_type="stock", min_lot_size=0.01, lot_step=0.01)
    crypto_config = LotConfig(asset_type="crypto", min_lot_size=0.001, lot_step=0.001)
    
    print(f"\n📊 株式LOT設定:")
    print(f"  基本LOTサイズ: {stock_config.base_lot_size}")
    print(f"  最小LOTサイズ: {stock_config.min_lot_size}")
    print(f"  LOTステップ: {stock_config.lot_step}")
    print(f"  1LOT = {stock_config.lot_to_units(1.0)} 株")
    print(f"  0.1LOT = {stock_config.lot_to_units(0.1)} 株")
    print(f"  0.01LOT = {stock_config.lot_to_units(0.01)} 株")
    
    print(f"\n📊 暗号通貨LOT設定:")
    print(f"  基本LOTサイズ: {crypto_config.base_lot_size}")
    print(f"  最小LOTサイズ: {crypto_config.min_lot_size}")
    print(f"  LOTステップ: {crypto_config.lot_step}")
    print(f"  1LOT = {crypto_config.lot_to_units(1.0)} 単位")
    print(f"  0.1LOT = {crypto_config.lot_to_units(0.1)} 単位")
    print(f"  0.01LOT = {crypto_config.lot_to_units(0.01)} 単位")
    
    # Test lot size validation and rounding
    print(f"\n🔍 LOTサイズ検証テスト:")
    test_lots = [0.1, 0.01, 0.005, 0.123, 1.5]
    
    for lot_size in test_lots:
        is_valid = stock_config.validate_lot_size(lot_size)
        rounded = stock_config.round_lot_size(lot_size)
        print(f"  {lot_size}LOT: 有効={is_valid}, 丸め後={rounded}LOT")

def test_lot_orders():
    """Test LOT-based order creation."""
    print(f"\n🧪 LOTベースオーダー作成をテスト...")
    
    # Create crypto lot config for Bitcoin trading
    crypto_config = LotConfig(asset_type="crypto", min_lot_size=0.01, lot_step=0.01)
    
    # Test different lot sizes
    lot_sizes = [1.0, 0.5, 0.1, 0.01]
    current_price = 300000  # 30万円のBTC価格
    
    for lots in lot_sizes:
        order = Order.create_lot_order(
            order_type=OrderType.MARKET,
            action=OrderAction.BUY,
            lots=lots,
            lot_size=crypto_config.base_lot_size
        )
        
        effective_quantity = order.effective_quantity
        cost = effective_quantity * current_price
        
        print(f"  {lots}LOT注文:")
        print(f"    数量: {order.quantity}")
        print(f"    実効数量: {effective_quantity}")
        print(f"    コスト: ¥{cost:,.0f}")

def test_lot_strategies():
    """Test strategies with LOT-based position sizing."""
    print(f"\n🧪 LOTベース戦略をテスト...")
    
    # Load sample data
    data_reader = CryptoDataReader()
    data_file = 'pricedata/BITFLYER_BTCJPY_1D_c51ab.csv'
    
    try:
        market_data = data_reader.load_data(data_file)
        print(f"データ読み込み成功: {len(market_data)}件")
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return
    
    # Create crypto lot configuration
    crypto_config = LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01,
        base_lot_size=1.0
    )
    
    # Test Moving Average strategy with 0.1 LOT positions
    print(f"\n📈 移動平均戦略 (0.1LOT)をテスト...")
    ma_strategy = MovingAverageStrategy(
        short_window=10,
        long_window=30,
        initial_capital=1000000,
        lot_config=crypto_config,
        position_lots=0.1  # 0.1 LOT per trade
    )
    
    # Test RSI strategy with 0.05 LOT positions
    print(f"📈 RSI戦略 (0.05LOT)をテスト...")
    rsi_strategy = RSIAveragingStrategy(
        rsi_period=14,
        entry_levels=[20, 25, 30, 35, 40],
        exit_level=70,
        max_positions=5,
        initial_capital=1000000,
        lot_config=crypto_config,
        position_lots=0.05  # 0.05 LOT per position
    )
    
    # Run short backtests to test functionality
    print(f"\n🔄 短期バックテストを実行...")
    
    # Test with first 100 data points
    test_data = market_data[:100]
    
    # Test MA strategy
    backtester_ma = Backtester(initial_capital=1000000)
    try:
        # Create a temporary data file for testing
        import tempfile
        import csv
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            for data_point in test_data:
                writer.writerow([
                    data_point.timestamp.strftime('%Y-%m-%d'),
                    data_point.open,
                    data_point.high,
                    data_point.low,
                    data_point.close,
                    data_point.volume
                ])
            
            temp_file_path = temp_file.name
        
        # Run backtest
        ma_result = backtester_ma.run_backtest(data_reader, ma_strategy, temp_file_path)
        
        print(f"移動平均戦略結果:")
        print(f"  取引数: {len(ma_result.trades)}")
        print(f"  最終価値: ¥{ma_result.final_capital:,.0f}")
        print(f"  リターン: {ma_result.total_return:.2%}")
        
        # Show lot sizes used in trades
        if ma_result.trades:
            print(f"  取引詳細:")
            for i, trade in enumerate(ma_result.trades[:3]):  # Show first 3 trades
                lot_size = crypto_config.units_to_lots(trade.quantity)
                print(f"    取引{i+1}: {trade.quantity:.3f}単位 ({lot_size:.3f}LOT)")
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"バックテストエラー: {e}")

def test_lot_calculations():
    """Test lot calculation edge cases."""
    print(f"\n🧪 LOT計算エッジケースをテスト...")
    
    crypto_config = LotConfig(asset_type="crypto", min_lot_size=0.01, lot_step=0.01)
    
    # Test scenarios
    scenarios = [
        {"cash": 100000, "price": 300000, "target_lots": 1.0},  # Not enough cash for 1 LOT
        {"cash": 500000, "price": 300000, "target_lots": 0.5},  # Can afford 0.5 LOT
        {"cash": 50000, "price": 300000, "target_lots": 0.1},   # Can afford 0.1 LOT
        {"cash": 10000, "price": 300000, "target_lots": 0.01},  # Can barely afford 0.01 LOT
        {"cash": 1000, "price": 300000, "target_lots": 0.01},   # Cannot afford even 0.01 LOT
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        cash = scenario["cash"]
        price = scenario["price"]
        target_lots = scenario["target_lots"]
        
        # Calculate maximum affordable lots
        max_affordable_units = cash / price
        max_affordable_lots = crypto_config.units_to_lots(max_affordable_units)
        
        # Calculate actual lots (minimum of target and affordable)
        actual_lots = min(target_lots, max_affordable_lots)
        actual_lots = crypto_config.round_lot_size(actual_lots)
        
        # Calculate actual cost
        actual_units = crypto_config.lot_to_units(actual_lots)
        actual_cost = actual_units * price
        
        print(f"  シナリオ{i}:")
        print(f"    利用可能現金: ¥{cash:,.0f}")
        print(f"    価格: ¥{price:,.0f}")
        print(f"    目標LOT: {target_lots}")
        print(f"    最大購入可能LOT: {max_affordable_lots:.4f}")
        print(f"    実際のLOT: {actual_lots}")
        print(f"    実際の単位: {actual_units:.4f}")
        print(f"    実際のコスト: ¥{actual_cost:,.0f}")
        print(f"    実行可能: {'はい' if actual_lots > 0 else 'いいえ'}")
        print()

def main():
    """Run all LOT functionality tests."""
    print("🚀 LOT機能の包括的テストを開始...")
    print("=" * 60)
    
    test_lot_config()
    test_lot_orders()
    test_lot_calculations()
    test_lot_strategies()
    
    print("=" * 60)
    print("✅ LOT機能テスト完了!")
    print("\n📋 LOT機能の主な特徴:")
    print("  • 0.01LOTから取引可能")
    print("  • 株式、暗号通貨、FXに対応")
    print("  • 自動的なLOTサイズ検証と丸め")
    print("  • 利用可能現金に基づく自動調整")
    print("  • 既存戦略との完全互換性")

if __name__ == "__main__":
    main()