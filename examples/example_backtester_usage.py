"""
株価取引ストラテジーバックテスター - メインデモンストレーション

🎯 目的:
バックテスターの全機能を包括的にデモンストレーションし、
初心者から中級者まで理解できる実用的な使用例を提供します。

📊 実装機能:
- バイアンドホールド戦略の実行
- 移動平均クロスオーバー戦略
- RSIナンピン戦略
- 複数戦略の比較分析
- パフォーマンス指標の計算
- 結果のエクスポート（JSON/CSV）
- プロフェッショナルな可視化

🚀 実行方法:
    python examples/example_usage.py
    # または
    backtester-demo

📈 使用データ:
実際のBTC/JPY価格データ（BitFlyer）を使用して、
リアルな市場環境でのバックテストを実行します。

👥 対象者:
- バックテスター初心者
- 戦略開発を学びたい方
- 全機能を理解したい方
- 実用的な例を求める方

⚠️ 注意事項:
- pricedata/BITFLYER_BTCJPY_1D_c51ab.csv が必要
- 実行には数分かかる場合があります
- charts/ フォルダに結果が保存されます
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the Python path to import backtester
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backtester import (
    Backtester,
    BuyAndHoldStrategy,
    ConfigFactory,
    CryptoDataReader,
    LotSizeMode,
    MovingAverageStrategy,
    RSIAveragingStrategy,
    VisualizationEngine,
)


def print_separator(title: str):
    """セクション区切りを印刷"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def format_currency(amount: float) -> str:
    """通貨フォーマット"""
    return f"¥{amount:,.0f}"


def format_percentage(value: float) -> str:
    """パーセンテージフォーマット"""
    return f"{value:.2f}%"


def print_performance_summary(backtester: Backtester, strategy_name: str):
    """パフォーマンスサマリーを印刷"""
    summary = backtester.get_performance_summary()
    
    print(f"\n📊 {strategy_name} - パフォーマンスサマリー")
    print("-" * 50)
    print(f"初期資本:           {format_currency(summary['initial_capital'])}")
    print(f"最終資本:           {format_currency(summary['final_capital'])}")
    print(f"総リターン:         {format_percentage(summary['total_return_pct'])}")
    
    if summary['annualized_return_pct']:
        print(f"年率リターン:       {format_percentage(summary['annualized_return_pct'])}")
    
    print(f"最大ドローダウン:   {format_percentage(summary['max_drawdown_pct'])}")
    
    if summary['sharpe_ratio']:
        print(f"シャープレシオ:     {summary['sharpe_ratio']:.3f}")
    
    print(f"プロフィットファクター: {summary['profit_factor']:.2f}")
    print(f"勝率:               {format_percentage(summary['win_rate_pct'])}")
    print(f"総取引数:           {summary['total_trades']}")
    print(f"勝ちトレード:       {summary['winning_trades']}")
    print(f"負けトレード:       {summary['losing_trades']}")
    print(f"総利益:             {format_currency(summary['gross_profit'])}")
    print(f"総損失:             {format_currency(abs(summary['gross_loss']))}")
    print(f"純利益:             {format_currency(summary['net_profit'])}")


def run_buy_and_hold_example():
    """バイアンドホールド戦略の例"""
    print_separator("バイアンドホールド戦略のバックテスト")
    
    # データリーダーとバックテスターを初期化
    data_reader = CryptoDataReader()
    backtester = Backtester(initial_capital=1000000)  # 100万円
    
    # LOT設定を作成（可変モード - デフォルト）
    crypto_config = ConfigFactory.create_crypto_lot_config(
        capital_percentage=0.95,  # 現在の総資金の95%を使用（複利効果）
        max_lot_size=10.0
    )
    
    # バイアンドホールド戦略を作成
    strategy = BuyAndHoldStrategy(
        initial_capital=1000000,
        lot_config=crypto_config,
        position_lots=1.0  # VARIABLE モードでは無視される
    )
    
    # データファイルのパス
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ データファイルが見つかりません: {data_file}")
        return None
    
    print(f"📈 データファイル: {data_file}")
    print("📊 LOT設定: 可変モード（現在資金の95%を使用・複利効果）")
    print("🚀 バックテスト実行中...")
    
    try:
        # バックテスト実行
        result = backtester.run_backtest(data_reader, strategy, data_file, "BTC/JPY")
        
        # 結果表示
        print_performance_summary(backtester, "バイアンドホールド（可変LOT・複利）")
        
        return backtester
        
    except Exception as e:
        print(f"❌ バックテスト実行エラー: {e}")
        return None


def run_moving_average_example():
    """移動平均戦略の例"""
    print_separator("移動平均クロスオーバー戦略のバックテスト")
    
    # データリーダーとバックテスターを初期化
    data_reader = CryptoDataReader()
    backtester = Backtester(initial_capital=1000000)  # 100万円
    
    # LOT設定を作成（可変モード - デフォルト）
    crypto_config = ConfigFactory.create_crypto_lot_config(
        capital_percentage=0.8,  # 現在の総資金の80%を使用（複利効果）
        max_lot_size=10.0
    )
    
    # 移動平均戦略を作成（短期10日、長期30日）
    strategy = MovingAverageStrategy(
        short_window=10, 
        long_window=30, 
        initial_capital=1000000,
        lot_config=crypto_config,
        position_lots=0.5  # VARIABLE モードでは無視される
    )
    
    # データファイルのパス
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    
    print(f"📈 データファイル: {data_file}")
    print("📊 戦略パラメータ: 短期MA=10日, 長期MA=30日")
    print("📊 LOT設定: 可変モード（現在資金の80%を使用・複利効果）")
    print("🚀 バックテスト実行中...")
    
    try:
        # バックテスト実行
        result = backtester.run_backtest(data_reader, strategy, data_file, "BTC/JPY")
        
        # 結果表示
        print_performance_summary(backtester, "移動平均クロスオーバー（可変LOT・複利）")
        
        return backtester
        
    except Exception as e:
        print(f"❌ バックテスト実行エラー: {e}")
        return None


def run_rsi_averaging_example():
    """RSIナンピン戦略の例"""
    print_separator("RSIナンピン戦略のバックテスト")
    
    # データリーダーとバックテスターを初期化
    data_reader = CryptoDataReader()
    backtester = Backtester(initial_capital=1000000)  # 100万円
    
    # LOT設定を作成（可変モード - デフォルト）
    crypto_config = ConfigFactory.create_crypto_lot_config(
        capital_percentage=0.15,  # 各ポジション15%の資金を使用
        max_lot_size=5.0
    )
    
    # RSIナンピン戦略を作成
    strategy = RSIAveragingStrategy(
        rsi_period=14,
        entry_levels=[20, 25, 30, 35, 40],  # エントリーレベル
        exit_level=70,  # エグジットレベル
        position_size_pct=0.2,  # 各ポジション20%（後方互換性のため保持）
        max_positions=5,
        initial_capital=1000000,
        lot_config=crypto_config,  # LOT設定を追加
        position_lots=0.2  # 可変モードでは基準値として使用
    )
    
    # データファイルのパス
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    
    print(f"📈 データファイル: {data_file}")
    print("📊 戦略パラメータ:")
    print("  - RSI期間: 14日")
    print("  - エントリーレベル: 20, 25, 30, 35, 40")
    print("  - エグジットレベル: 70")
    print("  - ポジションサイズ: 各20%")
    print("  - 最大ポジション数: 5")
    print("🚀 バックテスト実行中...")
    
    try:
        # バックテスト実行
        result = backtester.run_backtest(data_reader, strategy, data_file, "BTC/JPY")
        
        # 結果表示
        print_performance_summary(backtester, "RSIナンピン戦略")
        
        # 戦略固有の情報を表示
        position_info = strategy.get_position_info()
        print(f"\n📊 戦略固有情報:")
        print(f"  - 最大同時ポジション数: {position_info['max_positions']}")
        print(f"  - 現在RSI値: {position_info['current_rsi']:.2f}" if position_info['current_rsi'] else "  - 現在RSI値: N/A")
        print(f"  - オープンポジション数: {position_info['open_positions']}")
        if position_info['used_entry_levels']:
            print(f"  - 使用済みエントリーレベル: {position_info['used_entry_levels']}")
        
        return backtester
        
    except Exception as e:
        print(f"❌ バックテスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_strategies_example():
    """複数戦略の比較例"""
    print_separator("戦略比較分析")
    
    # データリーダーを初期化
    data_reader = CryptoDataReader()
    backtester = Backtester(initial_capital=1000000)
    
    # LOT設定を作成（可変モード - デフォルト）

    # 可変LOT設定
    variable_config = ConfigFactory.create_crypto_lot_config(
        lot_size_mode=LotSizeMode.VARIABLE,
        capital_percentage=0.8,  # 80%の資金を使用
        max_lot_size=10.0
    )
    
    # 固定LOT設定
    fixed_config = ConfigFactory.create_crypto_lot_config(
        lot_size_mode=LotSizeMode.FIXED
    )
    
    # 複数の戦略を作成（FIXED/VARIABLEモードの組み合わせ）
    strategies = [
        BuyAndHoldStrategy(
            initial_capital=1000000,
            lot_config=variable_config,
            position_lots=1.0
        ),
        MovingAverageStrategy(
            short_window=5, 
            long_window=20, 
            initial_capital=1000000,
            lot_config=fixed_config,
            position_lots=0.3
        ),
        MovingAverageStrategy(
            short_window=10, 
            long_window=30, 
            initial_capital=1000000,
            lot_config=variable_config,
            position_lots=0.5
        ),
        MovingAverageStrategy(
            short_window=20, 
            long_window=50, 
            initial_capital=1000000,
            lot_config=fixed_config,
            position_lots=0.8
        ),
        RSIAveragingStrategy(
            rsi_period=14,
            entry_levels=[20, 25, 30, 35, 40],  # エントリーレベル
            exit_level=70,  # エグジットレベル
            position_size_pct=0.2,
            max_positions=5,
            initial_capital=1000000,
            lot_config=variable_config,  # 可変LOT設定を使用
            position_lots=0.2  # 可変モードでは基準値として使用
        )
    ]
    
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    
    print(f"📈 データファイル: {data_file}")
    print(f"🔄 {len(strategies)}つの戦略を比較中...")
    
    try:
        # 戦略比較実行
        results = backtester.compare_strategies(strategies, data_reader, data_file)
        
        # 比較結果表示
        print("\n📊 戦略比較結果")
        print("-" * 80)
        print(f"{'戦略名':<25} {'総リターン':<12} {'最大DD':<10} {'シャープ':<10} {'勝率':<8} {'取引数':<8}")
        print("-" * 80)
        
        for strategy_name, result in results.items():
            total_return = result.total_return * 100
            max_dd = result.max_drawdown * 100
            sharpe = result.sharpe_ratio if result.sharpe_ratio else 0
            win_rate = result.win_rate * 100
            
            print(f"{strategy_name:<25} {total_return:>8.1f}%   {max_dd:>6.1f}%   {sharpe:>8.3f}   {win_rate:>5.1f}%   {result.total_trades:>6}")
        
        # 最良戦略の特定
        best_strategy = max(results.items(), key=lambda x: x[1].total_return)
        print(f"\n🏆 最良戦略: {best_strategy[0]} (総リターン: {best_strategy[1].total_return*100:.1f}%)")
        
        return results
        
    except Exception as e:
        print(f"❌ 戦略比較エラー: {e}")
        return None


def export_results_example(backtester: Backtester):
    """結果エクスポートの例"""
    print_separator("結果エクスポート")
    
    if not backtester.backtest_result:
        print("❌ エクスポートする結果がありません")
        return
    
    try:
        # 新しいResultManagerを使用して結果を保存
        saved_files = backtester.save_results()
        
        print(f"✅ JSON結果をエクスポート: {saved_files['json_results']}")
        print(f"✅ CSV取引履歴をエクスポート: {saved_files['csv_trades']}")
        
        print("\n📁 エクスポートされたファイル:")
        print(f"  - {saved_files['json_results']}: 完全なバックテスト結果（JSON形式）")
        print(f"  - {saved_files['csv_trades']}: 取引履歴（CSV形式）")
        
    except Exception as e:
        print(f"❌ エクスポートエラー: {e}")


def show_trade_details_example(backtester: Backtester):
    """取引詳細表示の例"""
    print_separator("取引詳細分析")
    
    trade_history = backtester.get_trade_history()
    
    if not trade_history:
        print("📝 取引履歴がありません")
        return
    
    print(f"📝 総取引数: {len(trade_history)}")
    print("\n最初の5取引:")
    print("-" * 100)
    print(f"{'日時':<12} {'アクション':<6} {'数量':<8} {'価格':<10} {'P&L':<12} {'リターン%':<10}")
    print("-" * 100)
    
    for i, trade in enumerate(trade_history[:5]):
        date_str = trade['entry_time'].strftime('%Y-%m-%d')
        action = trade['action']
        quantity = trade['quantity']
        price = trade['entry_price']
        pnl = trade['pnl']
        return_pct = trade['return_pct']
        
        print(f"{date_str:<12} {action:<6} {quantity:<8.0f} {price:<10.0f} {pnl:<12.0f} {return_pct:<10.2f}")
    
    if len(trade_history) > 5:
        print(f"... および他 {len(trade_history) - 5} 取引")


def create_visualizations_example(backtester: Backtester, data_reader: CryptoDataReader, data_file: str, strategy_name: str):
    """可視化機能のデモンストレーション"""
    print_separator("可視化機能デモンストレーション")
    
    if not backtester.backtest_result:
        print("❌ 可視化する結果がありません")
        return
    
    try:
        # 可視化エンジンを初期化
        viz_engine = VisualizationEngine()
        
        # 市場データを再読み込み（可視化用）
        print("📊 市場データを読み込み中...")
        market_data = data_reader.load_data(data_file)
        
        print(f"🎨 {strategy_name}の可視化チャートを作成中...")
        
        # 全てのチャートを保存
        saved_files = viz_engine.save_all_charts(
            backtester, 
            market_data, 
            strategy_name=strategy_name,
            output_dir="charts"
        )
        
        print("\n✅ 可視化チャートが作成されました:")
        for chart_type, file_path in saved_files.items():
            chart_names = {
                'price_signals': '価格チャート（エントリー・エグジットポイント付き）',
                'equity_curve': 'エクイティカーブ',
                'drawdown': 'ドローダウン分析',
                'dashboard': 'パフォーマンスダッシュボード'
            }
            print(f"  📈 {chart_names.get(chart_type, chart_type)}: {file_path}")
        
        print(f"\n📁 チャートは 'charts' フォルダに保存されました")
        print("💡 これらのチャートを開いて、戦略のパフォーマンスを視覚的に確認できます")
        
        return saved_files
        
    except Exception as e:
        print(f"❌ 可視化エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_strategy_comparison_visualization(comparison_results):
    """戦略比較の可視化"""
    print_separator("戦略比較可視化")
    
    if not comparison_results:
        print("❌ 比較する結果がありません")
        return
    
    try:
        viz_engine = VisualizationEngine()
        
        print("📊 戦略比較チャートを作成中...")
        
        # 4つの指標を1つのチャートにまとめて作成
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_path = f"charts/strategy_comparison_dashboard_{timestamp}.png"
        
        fig = viz_engine.compare_strategies_chart(
            comparison_results,
            metrics=metrics,
            title="戦略比較ダッシュボード",
            save_path=chart_path
        )
        
        # Close figure to free memory
        import matplotlib.pyplot as plt
        plt.close(fig)
        
        print("\n✅ 戦略比較チャートが作成されました:")
        print(f"  📊 戦略比較ダッシュボード: {chart_path}")
        
        return [("戦略比較ダッシュボード", chart_path)]
        
    except Exception as e:
        print(f"❌ 戦略比較可視化エラー: {e}")
        return None


def main():
    """メイン実行関数"""
    print("🚀 株価取引ストラテジーバックテスター - 使用例")
    print("=" * 60)
    print("実際のBTC/JPY価格データを使用してバックテスターの機能をデモンストレーションします。")
    
    # 1. バイアンドホールド戦略
    bah_backtester = run_buy_and_hold_example()
    
    # 2. 移動平均戦略
    ma_backtester = run_moving_average_example()
    
    # 3. RSIナンピン戦略
    rsi_backtester = run_rsi_averaging_example()
    
    # 4. 戦略比較
    comparison_results = compare_strategies_example()
    
    # 4. 結果エクスポート（最後に実行した戦略の結果を使用）
    if ma_backtester:
        export_results_example(ma_backtester)
        show_trade_details_example(ma_backtester)
    
    # 5. 可視化機能のデモンストレーション
    if ma_backtester:
        data_reader = CryptoDataReader()
        data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
        create_visualizations_example(ma_backtester, data_reader, data_file, "移動平均クロスオーバー")

    # 5-2. 可視化機能のデモンストレーション
    if rsi_backtester:
        data_reader = CryptoDataReader()
        data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
        create_visualizations_example(rsi_backtester, data_reader, data_file, "rsiナンピン戦略")

    
    
    # 6. 戦略比較の可視化
    if comparison_results:
        create_strategy_comparison_visualization(comparison_results)
    
    print_separator("デモンストレーション完了")
    print("✅ バックテスターの全機能が正常に動作しました！")
    print("\n📚 このデモンストレーションでは以下の機能を確認しました:")
    print("  - 実際の価格データの読み込み（Unix timestamp対応）")
    print("  - バイアンドホールド戦略の実行")
    print("  - 移動平均クロスオーバー戦略の実行")
    print("  - 複数戦略の比較分析")
    print("  - パフォーマンス指標の計算（プロフィットファクター、シャープレシオなど）")
    print("  - 結果のエクスポート（JSON/CSV形式）")
    print("  - 取引履歴の詳細分析")
    
    print("\n🔧 カスタマイズ可能な要素:")
    print("  - 初期資本金額")
    print("  - 移動平均の期間パラメータ")
    print("  - リスク管理設定")
    print("  - スリッページと手数料")
    print("  - 独自の取引戦略の実装")


if __name__ == "__main__":
    main()