# Tests - テストスイート

このフォルダには、株式取引バックテスターと株式データ管理システムの包括的なテストが含まれています。

## 📋 テスト構成

### 🧪 Unit Tests (`tests/unit/`)
個別コンポーネントの単体テスト

#### バックテスター関連
- `test_backtester.py` - メインバックテストエンジン
- `test_strategy.py` - 取引戦略
- `test_portfolio.py` - ポートフォリオ管理
- `test_analytics.py` - パフォーマンス分析
- `test_order_manager.py` - 注文管理
- `test_models.py` - データモデル
- `test_lot_functionality.py` - LOTベース機能
- `test_data_reader.py` - データ読み込み
- `test_visualization.py` - 可視化機能

#### 株式データベース関連
- `test_data_access_api.py` - データアクセスAPI
- `test_repositories.py` - データリポジトリ
- `test_database.py` - データベース操作
- `test_data_fetcher.py` - データ取得
- `test_yfinance_symbol_source.py` - yfinanceシンボルソース
- `test_yahoo_finance_client.py` - Yahoo Finance クライアント
- `test_curl_client.py` - curl_cffi クライアント
- `test_curl_transformer.py` - データ変換
- `test_transformer.py` - データ変換
- `test_validation.py` - データ検証

#### 設定・初期化関連
- `test_config_setup.py` - 設定とログ設定テスト
- `test_initialization.py` - 初期化テスト
- `test_yfinance_fields.py` - yfinanceフィールドテスト

#### バックテスター統合
- `test_backtester_adapter.py` - バックテスター統合アダプター

---

### 🔗 Integration Tests (`tests/integration/`)
システム間の統合テスト

#### バックテスター統合
- `test_multiple_positions.py` - 複数ポジション管理

#### 株式データベース統合 (`tests/integration/stock_database/`)
- `test_apple_data_flow.py` - Apple株価データの完全フロー
- `test_apple_data_flow_fixed.py` - Apple株価データフロー（修正版）
- `test_complete_data_flow.py` - 包括的データフロー（SQLite版）
- `test_sqlite_data_flow.py` - SQLiteデータフロー
- `test_financial_company_data.py` - 財務・会社データ
- `test_financial_company_data_with_samples.py` - サンプル付き財務データ
- `test_manual_data_insertion.py` - 手動データ挿入
- `test_simple_data_insertion.py` - シンプルデータ挿入
- `test_mongodb_atlas_connection.py` - MongoDB Atlas接続

---

### 📚 Example Tests (`tests/examples/`)
使用例のテスト

- `demo_lot_modes.py` - LOTモードのデモ
- `demo_lot_trading.py` - LOT取引のデモ

---

## 🚀 テスト実行方法

### 全テスト実行
```bash
# 全テスト実行
pytest

# 詳細出力付き
pytest -v

# カバレッジ付き実行
pytest --cov=backtester --cov=stock_database

# カバレッジレポート生成
pytest --cov=backtester --cov=stock_database --cov-report=html
```

### カテゴリ別テスト実行
```bash
# ユニットテストのみ
pytest tests/unit/

# 統合テストのみ
pytest tests/integration/

# 株式データベース統合テストのみ
pytest tests/integration/stock_database/

# 例題テストのみ
pytest tests/examples/
```

### 特定テスト実行
```bash
# 特定ファイル
pytest tests/unit/test_backtester.py

# 特定テストクラス
pytest tests/unit/test_backtester.py::TestBacktester

# 特定テストメソッド
pytest tests/unit/test_backtester.py::TestBacktester::test_basic_backtest
```

### パフォーマンステスト
```bash
# 実行時間測定
pytest --durations=10

# 並列実行（pytest-xdist必要）
pytest -n auto
```

---

## 🔧 テスト設定

### pytest設定 (`conftest.py`)
- テストフィクスチャの定義
- サンプルデータの生成
- モック設定
- テスト環境の初期化

### 主要フィクスチャ
- `sample_market_data` - サンプル市場データ
- `mock_db_manager` - モックデータベースマネージャー
- `test_config` - テスト用設定

---

## 📊 テストカバレッジ

### 目標カバレッジ
- **ユニットテスト**: 90%以上
- **統合テスト**: 主要フロー100%
- **全体**: 85%以上

### カバレッジレポート確認
```bash
# HTMLレポート生成
pytest --cov=backtester --cov=stock_database --cov-report=html

# ブラウザで確認
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

---

## 🐛 テストデバッグ

### デバッグオプション
```bash
# 詳細ログ出力
pytest -v -s

# 最初の失敗で停止
pytest -x

# 失敗したテストのみ再実行
pytest --lf

# PDB デバッガー起動
pytest --pdb
```

### ログレベル設定
```bash
# DEBUGレベルログ
pytest --log-level=DEBUG

# 特定ロガーのみ
pytest --log-cli-level=INFO --log-cli-format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
```

---

## 📝 テスト作成ガイドライン

### ユニットテスト
1. **単一責任**: 1つのテストで1つの機能をテスト
2. **独立性**: テスト間の依存関係を避ける
3. **再現性**: 常に同じ結果を返す
4. **高速性**: 迅速な実行
5. **明確性**: テスト名で意図を明確に

### 統合テスト
1. **実際のデータ**: 可能な限り実際のデータを使用
2. **エンドツーエンド**: 完全なワークフローをテスト
3. **エラーケース**: 異常系も含める
4. **クリーンアップ**: テスト後のリソース清理

### テスト命名規則
```python
def test_[機能]_[条件]_[期待結果]():
    # 例: test_backtester_with_valid_data_returns_results()
    pass
```

---

## 🔍 継続的インテグレーション

### GitHub Actions設定例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements/requirements-dev.txt
      - name: Run tests
        run: pytest --cov=backtester --cov=stock_database
```

---

## 📞 サポート

### テスト関連の問題
1. **依存関係エラー**: `pip install -r requirements/requirements-dev.txt`
2. **パス問題**: プロジェクトルートから実行
3. **データベース問題**: テスト用データベースの設定確認
4. **モック問題**: フィクスチャの設定確認

### 新しいテストの追加
1. 適切なカテゴリ（unit/integration/examples）を選択
2. 既存のテストパターンに従う
3. 必要なフィクスチャを追加
4. ドキュメントを更新

---

**最終更新**: 2025年7月27日  
**管理者**: Stock Trading Backtester Team