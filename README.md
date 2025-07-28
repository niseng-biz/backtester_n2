# 📈 株式取引バックテスター

株式・仮想通貨取引戦略のための高性能で拡張可能なバックテストフレームワーク。Python で構築され、LOT ベースの高度なポジションサイジング、包括的なパフォーマンス分析、プロフェッショナルな可視化機能を特徴とします。

## ✨ 主な機能

### 🚀 コアバックテストエンジン
- **マルチアセット対応**: 株式、仮想通貨、その他の金融商品
- **高度な注文管理**: 成行注文、指値注文（スリッページ・手数料モデリング付き）
- **LOT ベースポジションサイジング**: FIXED・VARIABLE モードでの柔軟なポジションサイジング
- **リアルタイムポートフォリオ追跡**: 完全なポジション・損益モニタリング
- **リスク管理**: ポジション制限、資本制約、ドローダウン制御

### 📊 パフォーマンス分析
- **包括的指標**: 総リターン、シャープレシオ、最大ドローダウン、勝率
- **高度な統計**: プロフィットファクター、ソルティノレシオ、カルマーレシオ、VaR 計算
- **取引分析**: エントリー・エグジット追跡を含む詳細な取引履歴
- **リスク評価**: ベータ、アルファ、インフォメーションレシオ計算

### 🎨 プロフェッショナル可視化
- **インタラクティブチャート**: エントリー・エグジットシグナル付き価格チャート
- **資産曲線**: 時系列でのポートフォリオ価値推移
- **ドローダウン分析**: ドローダウン期間と回復の視覚化
- **パフォーマンスダッシュボード**: 多画面包括的概観
- **戦略比較**: サイドバイサイドでの戦略パフォーマンス分析

### 🔧 技術的優秀性
- **モジュラーアーキテクチャ**: 拡張可能な設計での関心事の明確な分離
- **タイプセーフティ**: より信頼性の高いコードのための完全な Python 型ヒント
- **包括的テスト**: 100+ のユニット・統合テスト
- **パフォーマンス最適化**: 大規模データセットの効率的処理
- **プロフェッショナルドキュメント**: 完全な API ドキュメントと例

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-username/stock-trading-backtester.git
cd stock-trading-backtester

# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# その他のインストールオプション
# 開発環境: pip install -r requirements/requirements-dev.txt
# 軽量版: pip install -r requirements/requirements-minimal.txt
# 株式データのみ: pip install -r requirements/stock_data_requirements.txt
```

### 📋 Requirements管理

プロジェクトでは用途別に複数のrequirementsファイルを提供しています：

- **`requirements.txt`**: プロダクション環境用（メイン）
- **`requirements/requirements-dev.txt`**: 開発環境用（テスト・コード品質ツール含む）
- **`requirements/requirements-minimal.txt`**: 軽量版（TA-Libなし）
- **`requirements/stock_data_requirements.txt`**: 株式データモジュール専用

詳細は [`requirements/README.md`](requirements/README.md) をご覧ください。

### 📊 株価データベース機能

このバックテスターには、Yahoo Financeから株価データを自動取得・管理する高性能データベースシステムが統合されています。

#### 🚀 curl_cffi による高速データ取得（デフォルト）

- **2倍高速**: 従来のyfinanceライブラリより50%高速なリクエスト処理
- **大容量バッチ**: 20銘柄の並列処理（従来の10銘柄から向上）
- **高い成功率**: ブラウザ偽装による95%の成功率
- **堅牢なエラー処理**: 指数バックオフによる自動リトライ

#### データベース機能

```python
from stock_database.utils.data_fetcher import DataFetcher
from stock_database.database import MongoDBManager

# 高性能データ取得（curl_cffiがデフォルト）
data_fetcher = DataFetcher()

# 複数銘柄の並列取得
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
results = data_fetcher.fetch_stock_data(symbols)

# 差分更新（新しいデータのみ取得）
incremental_results = data_fetcher.schedule_incremental_update(symbols)

# 包括的データ取得（株価・財務・企業情報）
all_data = data_fetcher.fetch_all_data(symbols)
```

### 基本的な使用方法

```python
from backtester.crypto_data_reader import CryptoDataReader
from backtester.strategy import MovingAverageStrategy
from backtester.backtester import Backtester
from backtester.models import LotConfig, LotSizeMode

# コンポーネント初期化
data_reader = CryptoDataReader()
backtester = Backtester(initial_capital=100000)  # $100,000

# LOT ベースポジションサイジング設定
lot_config = LotConfig(
    asset_type="crypto",
    lot_size_mode=LotSizeMode.VARIABLE,
    capital_percentage=0.8,  # 利用可能資本の80%を使用
    max_lot_size=10.0
)

# 取引戦略作成
strategy = MovingAverageStrategy(
    short_window=10, 
    long_window=30,
    initial_capital=100000,
    lot_config=lot_config
)

# バックテスト実行
result = backtester.run_backtest(
    data_reader, 
    strategy, 
    "data/BTCUSD_daily.csv"
)

# 結果表示
print(f"総リターン: {result.total_return*100:.2f}%")
print(f"シャープレシオ: {result.sharpe_ratio:.3f}")
print(f"最大ドローダウン: {result.max_drawdown*100:.2f}%")
print(f"勝率: {result.win_rate*100:.2f}%")
```

### デモ実行

```bash
python examples/example_usage.py
# または
backtester-demo
```

### 📁 Examples - 使用例集

`examples/` フォルダには、様々な使用例とデモンストレーションが含まれています：

- **`example_usage.py`** ⭐ - メインデモ（全機能の包括的な例）
- **`advanced_stock_dashboard.py`** - 高度な株式分析ダッシュボード
- **`backtester_adapter_example.py`** - システム統合の例
- **`data_access_api_example.py`** - データアクセスAPIの使用例

詳細は [`examples/README.md`](examples/README.md) をご覧ください。

これは以下を実演します：
- バイアンドホールド戦略
- 移動平均クロスオーバー戦略  
- RSI ベースドルコスト平均法
- 戦略比較分析
- プロフェッショナル可視化生成

## 📊 対応戦略

### 組み込み戦略

#### バイアンドホールド
```python
from backtester.strategy import BuyAndHoldStrategy

strategy = BuyAndHoldStrategy(
    initial_capital=100000,
    lot_config=lot_config
)
```

#### 移動平均クロスオーバー
```python
from backtester.strategy import MovingAverageStrategy

strategy = MovingAverageStrategy(
    short_window=10,    # 短期MA期間
    long_window=30,     # 長期MA期間
    initial_capital=100000,
    lot_config=lot_config
)
```

#### RSI ドルコスト平均法
```python
from backtester.strategy import RSIAveragingStrategy

strategy = RSIAveragingStrategy(
    rsi_period=14,
    entry_levels=[20, 25, 30, 35, 40],  # 複数エントリーポイント
    exit_level=70,
    max_positions=5,
    initial_capital=100000,
    lot_config=lot_config
)
```

### カスタム戦略開発

```python
from backtester.strategy import Strategy
from backtester.models import Order, OrderType, OrderAction

class MyCustomStrategy(Strategy):
    def __init__(self, parameter1, parameter2, initial_capital, lot_config):
        super().__init__(initial_capital, "MyStrategy", lot_config)
        self.parameter1 = parameter1
        self.parameter2 = parameter2
    
    def generate_signal(self, current_data, historical_data):
        # 取引ロジックを実装
        if self.should_buy(current_data, historical_data):
            lots = self.calculate_lot_size(self.cash, current_data.close, 1.0)
            return self.create_lot_order(
                action=OrderAction.BUY,
                lots=lots,
                current_price=current_data.close
            )
        elif self.should_sell(current_data, historical_data):
            current_lots = self.lot_config.units_to_lots(self.current_position)
            return self.create_lot_order(
                action=OrderAction.SELL,
                lots=current_lots,
                current_price=current_data.close
            )
        return None
    
    def get_strategy_name(self):
        return "My Custom Strategy"
```

## 🎨 可視化例

### プロフェッショナルチャート生成

```python
from backtester.visualization import VisualizationEngine

viz_engine = VisualizationEngine()

# シグナル付き価格チャート
fig = viz_engine.create_price_chart_with_signals(
    market_data, 
    trades,
    title="BTC/USD 取引シグナル",
    save_path="charts/btc_signals.png"
)

# 資産曲線
fig = viz_engine.create_equity_curve(
    portfolio_history,
    title="ポートフォリオパフォーマンス",
    save_path="charts/equity_curve.png"
)

# パフォーマンスダッシュボード
fig = viz_engine.create_performance_dashboard(
    backtester,
    market_data,
    strategy_name="移動平均戦略",
    save_path="charts/dashboard.png"
)
```

### 戦略比較

```python
# 複数戦略比較
strategies = [
    BuyAndHoldStrategy(100000, lot_config),
    MovingAverageStrategy(5, 20, 100000, lot_config),
    MovingAverageStrategy(10, 30, 100000, lot_config)
]

results = backtester.compare_strategies(strategies, data_reader, "data/BTCUSD.csv")

# 比較チャート生成
fig = viz_engine.compare_strategies_chart(
    results,
    metrics=['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate'],
    title="戦略パフォーマンス比較",
    save_path="charts/strategy_comparison.png"
)
```

## 📁 データ形式

### CSV データ要件

```csv
timestamp,open,high,low,close,volume
1640995200,46000.0,47500.0,45500.0,47000.0,1250
1641081600,47000.0,48200.0,46800.0,48100.0,1180
1641168000,48100.0,49000.0,47900.0,48800.0,1320
```

**必須列:**
- `timestamp`: Unix タイムスタンプまたは日付文字列
- `open`: 始値
- `high`: 高値
- `low`: 安値  
- `close`: 終値
- `volume`: 出来高

### カスタムデータリーダー

```python
from backtester.data_reader import CSVDataReader

# カスタム列マッピング
custom_reader = CSVDataReader(
    date_column='Date',
    open_column='O',
    high_column='H', 
    low_column='L',
    close_column='C',
    volume_column='Vol'
)
```

## ⚙️ 高度な設定

### LOT ベースポジションサイジング

```python
from backtester.models import LotConfig, LotSizeMode

# 可変LOTサイジング（資本の割合）
variable_config = LotConfig(
    asset_type="crypto",
    lot_size_mode=LotSizeMode.VARIABLE,
    capital_percentage=0.8,  # 利用可能資本の80%を使用
    max_lot_size=10.0,
    min_lot_size=0.01
)

# 固定LOTサイジング（一定LOTサイズ）
fixed_config = LotConfig(
    asset_type="stock", 
    lot_size_mode=LotSizeMode.FIXED,
    base_lot_size=100,  # 1LOTあたり100株
    min_lot_size=0.01
)
```

### リスク管理

```python
# ポートフォリオリスク制限
portfolio_manager.set_risk_limits(
    max_position_size=0.1,    # 1ポジション最大10%
    max_total_exposure=1.0    # 総エクスポージャー最大100%
)

# 注文執行コスト
order_manager.set_slippage(0.001)    # 0.1%スリッページ
order_manager.set_commission(0.001)  # 0.1%手数料
```

## 📊 パフォーマンス指標

### 基本指標
- **総リターン**: `(最終資本 - 初期資本) / 初期資本`
- **年率リターン**: 複利年間成長率
- **最大ドローダウン**: 最大のピークからトラフまでの下落
- **勝率**: 利益となった取引の割合

### リスク調整指標
- **シャープレシオ**: `(平均リターン - リスクフリーレート) / 標準偏差`
- **ソルティノレシオ**: 下方偏差を用いたシャープレシオ
- **カルマーレシオ**: `年率リターン / 最大ドローダウン`
- **インフォメーションレシオ**: トラッキングエラー1単位あたりのアクティブリターン

### 取引統計
- **プロフィットファクター**: `総利益 / 総損失`
- **平均勝敗**: 取引あたりの平均利益・損失
- **期待値**: `(勝率 × 平均勝ち) + (負け率 × 平均負け)`
- **最大連続勝敗**: 最長の連勝・連敗記録

## 🧪 テスト

### テスト実行

```bash
# 全テスト実行
pytest

# 特定テストカテゴリ実行
pytest tests/unit/          # ユニットテスト
pytest tests/integration/   # 統合テスト
pytest tests/examples/      # 例題テスト

# カバレッジ付き実行
pytest --cov=backtester tests/
```

### テストカテゴリ
- **ユニットテスト**: 個別コンポーネントテスト
- **統合テスト**: コンポーネント間相互作用テスト  
- **例題テスト**: エンドツーエンドシナリオテスト

## 📤 結果エクスポート

### JSON エクスポート
```python
# 完全結果エクスポート
backtester.export_results("results.json", format="json")
```

### CSV エクスポート
```python
# 取引履歴エクスポート
backtester.export_results("trades.csv", format="csv")
```

### エクスポートデータ内容
- 全指標を含むパフォーマンス要約
- エントリー・エグジット詳細を含む完全取引履歴
- ポートフォリオ価値推移
- 戦略パラメータと設定
- 実行メタデータとタイムスタンプ

## 🏗️ アーキテクチャ

### コンポーネント概要

```
backtester/
├── models.py              # データモデル（MarketData、Trade、Order等）
├── data_reader.py         # データ読み込みベースクラス
├── crypto_data_reader.py  # 仮想通貨データリーダー
├── strategy.py            # 戦略フレームワークと実装
├── order_manager.py       # 注文実行・管理
├── portfolio.py           # ポートフォリオ・ポジション管理
├── analytics.py           # パフォーマンス分析エンジン
├── backtester.py          # メインバックテストエンジン
├── visualization.py       # チャート・可視化エンジン
└── result_manager.py      # 結果エクスポート・管理
```

### 設計原則
- **モジュラー設計**: 独立した疎結合コンポーネント
- **拡張性**: 新しい戦略・データソースの簡単追加
- **タイプセーフティ**: 信頼性のための包括的型ヒント
- **テスト可能性**: 各コンポーネントの独立テスト
- **パフォーマンス**: 大規模データセット処理最適化

## 🔍 トラブルシューティング

### よくある問題

#### データ読み込みエラー
```
FileNotFoundError: CSV file not found
```
**解決策**: ファイルパスを確認し、CSV形式が要件に一致することを確認してください。

#### メモリ問題
```
MemoryError: Unable to allocate array
```
**解決策**: より小さなデータセットを使用するか、大きなファイルにはデータチャンクを実装してください。

#### 可視化警告
```
UserWarning: Glyph missing from current font
```
**解決策**: 日本語フォント警告 - チャートは正しく生成されます。

### パフォーマンス最適化

```python
# 大規模データセットの進捗追跡
backtester.set_progress_callback(
    lambda current, total: print(f"進捗: {current/total*100:.1f}%")
)

# メモリ監視
import psutil
process = psutil.Process()
print(f"メモリ使用量: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

## 🤝 貢献

貢献を歓迎します！詳細は[貢献ガイドライン](CONTRIBUTING.md)をご覧ください。

### 開発環境セットアップ

```bash
# 開発環境のクローンとセットアップ
git clone https://github.com/your-username/stock-trading-backtester.git
cd stock-trading-backtester
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/requirements-dev.txt

# pre-commit フック インストール
pre-commit install
```

### コード標準
- **PEP 8**: Python スタイルガイド準拠
- **型ヒント**: 全関数に型注釈必須
- **ドキュメント**: 包括的な docstring 必須
- **テスト**: 新機能にはテストを含める

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています - 詳細は [LICENSE](LICENSE) ファイルをご覧ください。
