# 投資システム統合プラットフォーム - Exampleファイルガイド

このディレクトリには、株式データ取得、バックテスト、ダッシュボードシステムの使用方法を学ぶためのexampleファイルが含まれています。

## 📋 Exampleファイル一覧

### 📊 株式データ取得システム


#### 1. `example_stockdatafetch_data_fetching.py` - 実践的なデータ取得
**実際の運用で使用するパターン**
- 大量データの効率的な取得
- バッチ処理と進捗表示
- エラーハンドリングと再試行
- 増分更新

```bash
python examples/example_stockdatafetch_data_fetching.py
```

### 🔄 バックテストシステム

#### 2. `example_basktester_usage.py` - 基本的なバックテスト
- バイアンドホールド戦略の実行
- 移動平均クロスオーバー戦略
- RSIナンピン戦略
- 複数戦略の比較分析

```bash
python examples/example_basktester_usage.py
```

#### 3. `example_basktester_usage_optimize.py` - パラメータ最適化
- Optunaを使用した戦略パラメータ最適化
- 訓練・検証・テストデータ分割
- 最適化結果の可視化

```bash
python examples/example_basktester_usage_optimize.py
```

#### 4. `example_basktester_usage_optimize_with_suggestions.py` - 提案付き最適化
- ユーザー提案を活用した最適化
- 初期パラメータ提案機能
- 最適化効率の向上

```bash
python examples/example_basktester_usage_optimize_with_suggestions.py
```

### 📈 ダッシュボードシステム

#### 5. `example_dashboard_run_dashboard.py` - 基本ダッシュボード
- Streamlitベースの株式ダッシュボード
- リアルタイムデータ表示
- インタラクティブなチャート

```bash
python examples/example_dashboard_run_dashboard.py
```

#### 6. `example_dashboard_advanced_stock_dashboard.py` - 高度なダッシュボード
- 高度な分析機能
- カスタマイズ可能なビュー
- 複数データソースの統合

```bash
python examples/example_dashboard_advanced_stock_dashboard.py
```

## 🎯 実行順序の推奨

### 初回セットアップ時
```bash
# 1. システム要件確認とデータベース初期化
python examples/example_stockdatafetch_database_setup_example.py

# 2. 基本機能の確認（最初に実行）
python examples/example_stockdatafetch_quick_start.py

# 3. 基本的な使用方法の学習
python examples/example_stockdatafetch_basic_stock_data.py
```

### 日常的な運用
```bash
# 大量データの取得・更新
python examples/example_stockdatafetch_data_fetching.py

# バックテストの実行
python examples/example_basktester_usage.py

# ダッシュボードの起動
python examples/example_dashboard_run_dashboard.py
```

### 高度な機能
```bash
# パラメータ最適化
python examples/example_basktester_usage_optimize.py

# 提案付き最適化
python examples/example_basktester_usage_optimize_with_suggestions.py

# 高度なダッシュボード
python examples/example_dashboard_advanced_stock_dashboard.py
```

## 📊 各ファイルの特徴

### 株式データ取得システム
| ファイル | 対象者 | 実行時間 | 取得銘柄数 | 主な学習内容 |
|---------|--------|----------|------------|-------------|
| `example_stockdatafetch_quick_start.py` | 初心者 | 2-3分 | 3銘柄 | 基本的な流れ |
| `example_stockdatafetch_basic_stock_data.py` | 初心者〜中級者 | 3-5分 | 3銘柄 | データ操作の基本 |
| `example_stockdatafetch_database_setup_example.py` | 管理者 | 5-10分 | 0銘柄 | システム初期化 |
| `example_stockdatafetch_data_fetching.py` | 中級者〜上級者 | 10-30分 | 50銘柄 | 実践的な運用 |

### バックテストシステム
| ファイル | 対象者 | 実行時間 | データ要件 | 主な学習内容 |
|---------|--------|----------|------------|-------------|
| `example_basktester_usage.py` | 初心者〜中級者 | 5-10分 | 価格データ | 基本的なバックテスト |
| `example_basktester_usage_optimize.py` | 中級者〜上級者 | 10-30分 | 価格データ | パラメータ最適化 |
| `example_basktester_usage_optimize_with_suggestions.py` | 上級者 | 10-30分 | 価格データ | 高度な最適化 |

### ダッシュボードシステム
| ファイル | 対象者 | 実行時間 | データ要件 | 主な学習内容 |
|---------|--------|----------|------------|-------------|
| `example_dashboard_run_dashboard.py` | 初心者〜中級者 | 起動後常駐 | 株式データ | 基本ダッシュボード |
| `example_dashboard_advanced_stock_dashboard.py` | 中級者〜上級者 | 起動後常駐 | 株式データ | 高度な分析機能 |

## 🔧 前提条件

### 必要なソフトウェア
- Python 3.8以上
- SQLite（Pythonに内蔵）- 株式データ取得用
- インターネット接続（Yahoo Finance APIアクセス用）

### 必要なPythonパッケージ
```bash
pip install -r requirements.txt
```

主要パッケージ:
- `yfinance` - Yahoo Finance API（株式データ取得）
- `lxml` - HTMLパース（S&P500/NASDAQ100データ取得）
- `pandas` - データ処理（全システム共通）
- `numpy` - 数値計算（バックテスト）
- `matplotlib` - グラフ作成（バックテスト・ダッシュボード）
- `streamlit` - Webダッシュボード（ダッシュボード）
- `optuna` - パラメータ最適化（バックテスト）
- `requests` - HTTP通信（株式データ取得）

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. SQLiteデータベースに接続できない（株式データ取得）
```
Error: database is locked
```
**解決方法:**
- データベースファイルが他のプロセスで使用されていないことを確認
- `data/stock_data.db`ファイルの権限を確認
- 必要に応じてデータベースファイルを削除して再作成

#### 2. Yahoo Finance APIからデータを取得できない
```
Error: HTTPError 429 (Too Many Requests)
```
**解決方法:**
- リクエスト間隔を長くする
- バッチサイズを小さくする
- 時間をおいて再実行

#### 3. バックテスターのパスが通らない
```
ModuleNotFoundError: No module named 'backtester'
```
**解決方法:**
- プロジェクトルートディレクトリから実行
- PYTHONPATHが正しく設定されていることを確認

#### 4. ダッシュボードが起動しない
```
Error: streamlit command not found
```
**解決方法:**
- Streamlitがインストールされていることを確認: `pip install streamlit`
- 仮想環境が有効化されていることを確認

#### 5. 価格データファイルが見つからない
```
FileNotFoundError: pricedata/BITFLYER_BTCJPY_1D_c51ab.csv
```
**解決方法:**
- `pricedata/`フォルダに必要なCSVファイルが存在することを確認
- サンプルデータをダウンロードまたは生成

## 📈 パフォーマンス最適化

### 株式データ取得の最適化
- バッチサイズ: 10-20銘柄
- リクエスト間隔: 2-5秒
- 並列処理: 使用しない（API制限のため）
- キャッシュ: 有効化

### バックテストの最適化
- データ期間: 必要最小限に制限
- 戦略パラメータ: 適切な範囲設定
- 最適化試行回数: 50-100回程度
- 並列処理: CPUコア数に応じて調整

### ダッシュボードの最適化
- データ更新頻度: 適切な間隔設定
- キャッシュ活用: Streamlitキャッシュ機能
- 表示データ量: 必要最小限に制限

### メモリ使用量の最適化
- 大量データ処理時はバッチ処理を使用
- 不要なデータは定期的にクリーンアップ
- インデックスを適切に設定

## 🔗 関連ドキュメント

- [システム設計書](../docs/system_design.md)
- [API仕様書](../docs/api_specification.md)
- [データモデル仕様](../docs/data_models.md)
- [設定ファイルガイド](../docs/configuration.md)

## 💡 カスタマイズのヒント

### 株式データ取得のカスタマイズ
```python
# custom_symbols.py
CUSTOM_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

# exampleファイル内で使用
from custom_symbols import CUSTOM_SYMBOLS
results = data_fetcher.fetch_stock_data(CUSTOM_SYMBOLS)
```

### バックテスト戦略のカスタマイズ
```python
# 独自戦略の実装例
class CustomStrategy(BaseStrategy):
    def __init__(self, param1=10, param2=0.02):
        self.param1 = param1
        self.param2 = param2
    
    def should_buy(self, data, index):
        # 独自の買いロジック
        return your_buy_condition
    
    def should_sell(self, data, index):
        # 独自の売りロジック
        return your_sell_condition
```

### 設定のカスタマイズ
```yaml
# config.yaml
database:
  mongodb:
    host: "your-mongodb-host"
    port: 27017
    database: "your-database-name"

data_fetching:
  batch_size: 10
  request_delay: 2
  max_retries: 3

backtester:
  initial_capital: 1000000
  commission_rate: 0.001
  slippage: 0.001
```

## 🔄 システム間の連携

### データフロー
```
株式データ取得 → MongoDB → バックテスト → 結果分析 → ダッシュボード表示
```

### 連携例
```bash
# 1. データ取得
python examples/example_stockdatafetch_data_fetching.py

# 2. バックテスト実行
python examples/example_basktester_usage.py

# 3. ダッシュボードで結果確認
python examples/example_dashboard_run_dashboard.py
```

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：
- 実行したexampleファイル名
- エラーメッセージの全文
- Python・MongoDB・OSのバージョン
- 実行環境（ローカル・クラウド等）
- 使用しているシステム（株式データ取得・バックテスト・ダッシュボード）