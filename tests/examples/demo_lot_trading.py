#!/usr/bin/env python3
"""
Simple demonstration of LOT-based trading with 0.1 and 0.01 LOT sizes.
"""

from backtester.models import LotConfig, Order, OrderType, OrderAction
from backtester.strategy import MovingAverageStrategy, RSIAveragingStrategy

def demo_lot_basics():
    """Demonstrate basic LOT functionality."""
    print("🎯 LOT取引の基本デモンストレーション")
    print("=" * 50)
    
    # Create crypto configuration for Bitcoin trading
    crypto_config = LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01,
        base_lot_size=1.0
    )
    
    print(f"📊 暗号通貨LOT設定:")
    print(f"  • 最小LOTサイズ: {crypto_config.min_lot_size}")
    print(f"  • LOTステップ: {crypto_config.lot_step}")
    print(f"  • 1LOT = {crypto_config.lot_to_units(1.0)} BTC")
    
    # Demonstrate different lot sizes
    btc_price = 400000  # 40万円
    lot_sizes = [1.0, 0.5, 0.1, 0.05, 0.01]
    
    print(f"\n💰 BTC価格: ¥{btc_price:,}")
    print(f"📈 各LOTサイズでの取引例:")
    
    for lots in lot_sizes:
        units = crypto_config.lot_to_units(lots)
        cost = units * btc_price
        
        print(f"  • {lots:4.2f}LOT = {units:6.3f}BTC = ¥{cost:8,.0f}")

def demo_lot_orders():
    """Demonstrate LOT-based order creation."""
    print(f"\n🛒 LOTベースオーダー作成デモ")
    print("=" * 50)
    
    # Create different lot orders
    lot_orders = [
        {"lots": 0.1, "action": "買い"},
        {"lots": 0.05, "action": "買い"},
        {"lots": 0.01, "action": "買い"},
        {"lots": 0.1, "action": "売り"},
    ]
    
    for i, order_info in enumerate(lot_orders, 1):
        lots = order_info["lots"]
        action_str = order_info["action"]
        action = OrderAction.BUY if action_str == "買い" else OrderAction.SELL
        
        order = Order.create_lot_order(
            order_type=OrderType.MARKET,
            action=action,
            lots=lots,
            lot_size=1.0
        )
        
        print(f"注文{i}: {action_str} {lots}LOT")
        print(f"  • 注文数量: {order.quantity}")
        print(f"  • 実効数量: {order.effective_quantity}")
        print(f"  • LOTサイズ: {order.lot_size}")
        print()

def demo_lot_strategies():
    """Demonstrate strategies with LOT-based position sizing."""
    print(f"📊 LOTベース戦略デモ")
    print("=" * 50)
    
    # Create crypto lot configuration
    crypto_config = LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01
    )
    
    # Create strategies with different lot sizes
    strategies = [
        {
            "name": "移動平均戦略 (0.1LOT)",
            "strategy": MovingAverageStrategy(
                short_window=10,
                long_window=30,
                initial_capital=1000000,
                lot_config=crypto_config,
                position_lots=0.1
            )
        },
        {
            "name": "RSI戦略 (0.05LOT)",
            "strategy": RSIAveragingStrategy(
                rsi_period=14,
                entry_levels=[20, 25, 30, 35, 40],
                exit_level=70,
                max_positions=5,
                initial_capital=1000000,
                lot_config=crypto_config,
                position_lots=0.05
            )
        }
    ]
    
    btc_price = 400000
    available_cash = 500000
    
    print(f"💰 利用可能現金: ¥{available_cash:,}")
    print(f"💰 BTC価格: ¥{btc_price:,}")
    print()
    
    for strategy_info in strategies:
        name = strategy_info["name"]
        strategy = strategy_info["strategy"]
        
        print(f"🎯 {name}")
        
        # Calculate what this strategy would trade
        if hasattr(strategy, 'position_lots'):
            target_lots = strategy.position_lots
            actual_lots = strategy.calculate_lot_size(available_cash, btc_price, target_lots)
            actual_units = strategy.lot_config.lot_to_units(actual_lots)
            actual_cost = actual_units * btc_price
            
            print(f"  • 目標LOTサイズ: {target_lots}")
            print(f"  • 実際のLOTサイズ: {actual_lots:.3f}")
            print(f"  • 取引単位: {actual_units:.4f} BTC")
            print(f"  • 必要資金: ¥{actual_cost:,.0f}")
            print(f"  • 資金使用率: {(actual_cost/available_cash)*100:.1f}%")
        print()

def demo_lot_precision():
    """Demonstrate LOT precision and rounding."""
    print(f"🔧 LOT精度と丸め処理デモ")
    print("=" * 50)
    
    crypto_config = LotConfig(
        asset_type="crypto",
        min_lot_size=0.01,
        lot_step=0.01
    )
    
    # Test various lot sizes for validation and rounding
    test_lots = [0.1, 0.05, 0.01, 0.005, 0.123, 0.999, 1.234]
    
    print("LOTサイズ検証と丸め処理:")
    print("入力LOT  | 有効性 | 丸め後LOT")
    print("-" * 35)
    
    for lot in test_lots:
        is_valid = crypto_config.validate_lot_size(lot)
        rounded = crypto_config.round_lot_size(lot)
        print(f"{lot:8.3f} | {'✓' if is_valid else '✗':^6} | {rounded:8.3f}")

def demo_practical_example():
    """Show a practical trading example."""
    print(f"\n💼 実践的な取引例")
    print("=" * 50)
    
    # Scenario: Small investor with limited capital
    initial_capital = 100000  # 10万円
    btc_price = 400000       # 40万円
    
    crypto_config = LotConfig(asset_type="crypto", min_lot_size=0.01, lot_step=0.01)
    
    print(f"シナリオ: 小額投資家")
    print(f"  • 初期資金: ¥{initial_capital:,}")
    print(f"  • BTC価格: ¥{btc_price:,}")
    print()
    
    # Calculate different investment strategies
    strategies = [
        {"name": "フル投資", "target_lots": 1.0},
        {"name": "半分投資", "target_lots": 0.5},
        {"name": "小額投資", "target_lots": 0.1},
        {"name": "超小額投資", "target_lots": 0.01},
    ]
    
    for strategy in strategies:
        name = strategy["name"]
        target_lots = strategy["target_lots"]
        
        # Calculate maximum affordable lots
        max_affordable_units = initial_capital / btc_price
        max_affordable_lots = crypto_config.units_to_lots(max_affordable_units)
        
        # Calculate actual lots
        actual_lots = min(target_lots, max_affordable_lots)
        actual_lots = crypto_config.round_lot_size(actual_lots)
        
        # Calculate actual investment
        actual_units = crypto_config.lot_to_units(actual_lots)
        actual_cost = actual_units * btc_price
        
        print(f"{name}:")
        print(f"  • 目標: {target_lots}LOT")
        print(f"  • 実際: {actual_lots}LOT ({actual_units:.4f} BTC)")
        print(f"  • 投資額: ¥{actual_cost:,.0f}")
        print(f"  • 残り資金: ¥{initial_capital - actual_cost:,.0f}")
        print()

def main():
    """Run all demonstrations."""
    print("🚀 LOT取引システム デモンストレーション")
    print("🎯 0.1LOTや0.01LOTでの小額取引が可能です")
    print()
    
    demo_lot_basics()
    demo_lot_orders()
    demo_lot_strategies()
    demo_lot_precision()
    demo_practical_example()
    
    print("✅ デモンストレーション完了!")
    print("\n📋 LOT取引の利点:")
    print("  • 小額から投資可能 (0.01LOT = 約3,000円から)")
    print("  • 柔軟なポジションサイズ調整")
    print("  • リスク管理の向上")
    print("  • 資金効率の最適化")

if __name__ == "__main__":
    main()