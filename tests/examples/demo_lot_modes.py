#!/usr/bin/env python3
"""
LOT機能のFIXED（一定）とVARIABLE（可変）モードのデモンストレーション
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtester.models import LotConfig, LotSizeMode
from backtester.strategy import BuyAndHoldStrategy, MovingAverageStrategy, RSIAveragingStrategy
from backtester.crypto_data_reader import CryptoDataReader
from backtester.backtester import Backtester

def demo_lot_modes():
    """LOTモードの詳細デモンストレーション"""
    print("🎯 LOT機能: FIXED（一定）vs VARIABLE（可変）モード")
    print("=" * 70)
    
    # シナリオ設定
    initial_capital = 1000000  # 100万円
    btc_price = 400000        # 40万円
    available_cash = 800000   # 80万円（一部使用済み想定）
    
    print(f"📊 テストシナリオ:")
    print(f"  • 初期資本: ¥{initial_capital:,}")
    print(f"  • BTC価格: ¥{btc_price:,}")
    print(f"  • 利用可能現金: ¥{available_cash:,}")
    
    # FIXED（一定）モードのテスト
    print(f"\n🔒 FIXED（一定）モード:")
    fixed_config = LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01,
        lot_size_mode=LotSizeMode.FIXED
    )
    
    target_lots_list = [1.0, 0.5, 0.1, 0.01]
    
    for target_lots in target_lots_list:
        actual_lots = fixed_config.calculate_lot_size(available_cash, btc_price, target_lots)
        actual_units = fixed_config.lot_to_units(actual_lots)
        actual_cost = actual_units * btc_price
        
        print(f"  目標 {target_lots:4.2f}LOT → 実際 {actual_lots:4.2f}LOT ({actual_units:6.3f}BTC) = ¥{actual_cost:8,.0f}")
    
    # VARIABLE（可変）モードのテスト
    print(f"\n📈 VARIABLE（可変）モード:")
    
    capital_percentages = [0.1, 0.2, 0.5, 0.8]
    
    for capital_pct in capital_percentages:
        variable_config = LotConfig(
            asset_type="crypto",
            min_lot_size=0.01,
            lot_step=0.01,
            lot_size_mode=LotSizeMode.VARIABLE,
            capital_percentage=capital_pct,
            max_lot_size=10.0
        )
        
        actual_lots = variable_config.calculate_lot_size(available_cash, btc_price)
        actual_units = variable_config.lot_to_units(actual_lots)
        actual_cost = actual_units * btc_price
        
        print(f"  資金{capital_pct*100:2.0f}%使用 → {actual_lots:4.2f}LOT ({actual_units:6.3f}BTC) = ¥{actual_cost:8,.0f}")

def demo_strategy_comparison():
    """戦略でのLOTモード比較"""
    print(f"\n🔄 戦略でのLOTモード比較")
    print("=" * 70)
    
    # データ読み込み
    data_reader = CryptoDataReader()
    data_file = 'pricedata/BITFLYER_BTCJPY_1D_c51ab.csv'
    
    try:
        market_data = data_reader.load_data(data_file)
        print(f"✅ データ読み込み成功: {len(market_data)}件")
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return
    
    # FIXED vs VARIABLE モードの戦略比較
    strategies = [
        {
            "name": "移動平均戦略（FIXED 0.5LOT）",
            "strategy": MovingAverageStrategy(
                short_window=10,
                long_window=30,
                initial_capital=1000000,
                lot_config=LotConfig(
                    asset_type="crypto",
                    min_lot_size=0.01,
                    lot_step=0.01,
                    lot_size_mode=LotSizeMode.FIXED
                ),
                position_lots=0.5
            )
        },
        {
            "name": "移動平均戦略（VARIABLE 20%）",
            "strategy": MovingAverageStrategy(
                short_window=10,
                long_window=30,
                initial_capital=1000000,
                lot_config=LotConfig(
                    asset_type="crypto",
                    min_lot_size=0.01,
                    lot_step=0.01,
                    lot_size_mode=LotSizeMode.VARIABLE,
                    capital_percentage=0.2,
                    max_lot_size=5.0
                ),
                position_lots=0.5  # VARIABLEモードでは無視される
            )
        },
        {
            "name": "RSI戦略（FIXED 0.2LOT）",
            "strategy": RSIAveragingStrategy(
                rsi_period=14,
                entry_levels=[20, 25, 30, 35, 40],
                exit_level=70,
                max_positions=5,
                initial_capital=1000000,
                lot_config=LotConfig(
                    asset_type="crypto",
                    min_lot_size=0.01,
                    lot_step=0.01,
                    lot_size_mode=LotSizeMode.FIXED
                ),
                position_lots=0.2
            )
        },
        {
            "name": "RSI戦略（VARIABLE 15%）",
            "strategy": RSIAveragingStrategy(
                rsi_period=14,
                entry_levels=[20, 25, 30, 35, 40],
                exit_level=70,
                max_positions=5,
                initial_capital=1000000,
                lot_config=LotConfig(
                    asset_type="crypto",
                    min_lot_size=0.01,
                    lot_step=0.01,
                    lot_size_mode=LotSizeMode.VARIABLE,
                    capital_percentage=0.15,
                    max_lot_size=3.0
                ),
                position_lots=0.2  # VARIABLEモードでは無視される
            )
        }
    ]
    
    print(f"\n📊 戦略比較結果:")
    print("-" * 70)
    print(f"{'戦略名':<25} {'LOTモード':<10} {'取引数':<8} {'リターン':<10} {'勝率':<8}")
    print("-" * 70)
    
    for strategy_info in strategies:
        name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        
        try:
            backtester = Backtester(initial_capital=1000000)
            result = backtester.run_backtest(data_reader, strategy, data_file)
            
            lot_mode = "FIXED" if strategy.lot_config.lot_size_mode == LotSizeMode.FIXED else "VARIABLE"
            
            print(f"{name:<25} {lot_mode:<10} {len(result.trades):<8} {result.total_return*100:>6.1f}%   {result.win_rate*100:>5.1f}%")
            
        except Exception as e:
            print(f"{name:<25} エラー: {str(e)[:30]}")

def demo_lot_calculation_details():
    """LOT計算の詳細デモ"""
    print(f"\n🔍 LOT計算の詳細")
    print("=" * 70)
    
    # 異なる価格でのLOT計算
    prices = [100000, 300000, 500000, 1000000]  # 10万円〜100万円
    available_cash = 500000  # 50万円
    
    print(f"利用可能現金: ¥{available_cash:,}")
    print()
    
    # FIXED モード
    print("🔒 FIXED モード（目標: 0.5LOT）:")
    fixed_config = LotConfig(
        asset_type="crypto",
        lot_size_mode=LotSizeMode.FIXED
    )
    
    for price in prices:
        actual_lots = fixed_config.calculate_lot_size(available_cash, price, 0.5)
        actual_units = fixed_config.lot_to_units(actual_lots)
        actual_cost = actual_units * price
        
        print(f"  価格¥{price:7,} → {actual_lots:4.2f}LOT ({actual_units:6.3f}単位) = ¥{actual_cost:7,.0f}")
    
    print()
    
    # VARIABLE モード
    print("📈 VARIABLE モード（資金の30%使用）:")
    variable_config = LotConfig(
        asset_type="crypto",
        lot_size_mode=LotSizeMode.VARIABLE,
        capital_percentage=0.3
    )
    
    for price in prices:
        actual_lots = variable_config.calculate_lot_size(available_cash, price)
        actual_units = variable_config.lot_to_units(actual_lots)
        actual_cost = actual_units * price
        
        print(f"  価格¥{price:7,} → {actual_lots:4.2f}LOT ({actual_units:6.3f}単位) = ¥{actual_cost:7,.0f}")

def main():
    """メイン実行"""
    print("🚀 LOT機能: FIXED vs VARIABLE モード デモンストレーション")
    print("🎯 デフォルトはVARIABLE（可変）モードです")
    print()
    
    demo_lot_modes()
    demo_lot_calculation_details()
    demo_strategy_comparison()
    
    print("\n" + "=" * 70)
    print("✅ LOTモード デモンストレーション完了")
    print()
    print("📋 LOTモードの特徴:")
    print("  🔒 FIXED（一定）モード:")
    print("    • 指定したLOT数で固定取引")
    print("    • 資金不足の場合は購入可能な最大LOTに調整")
    print("    • 予測可能なポジションサイズ")
    print()
    print("  📈 VARIABLE（可変）モード（デフォルト）:")
    print("    • 利用可能資金の一定割合で取引")
    print("    • 資金量に応じて自動的にLOTサイズが調整")
    print("    • リスク管理に優れている")
    print("    • 複利効果を活用可能")

if __name__ == "__main__":
    main()