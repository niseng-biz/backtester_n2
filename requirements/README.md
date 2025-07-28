# Requirements Management

このフォルダには、プロジェクトの様々な環境や用途に応じた依存関係ファイルが含まれています。

## 📋 ファイル一覧

### 🔧 開発環境用

#### `requirements-dev.txt`
**用途**: 開発環境での完全なセットアップ
**内容**: 
- プロダクション依存関係（requirements.txtを継承）
- テストツール（pytest, pytest-cov, pytest-mock）
- コード品質ツール（black, flake8, isort, mypy）
- 開発ツール（jupyter, pre-commit）
- パフォーマンス分析ツール（memory-profiler, line-profiler）

**使用方法**:
```bash
pip install -r requirements/requirements-dev.txt
```

**対象者**: 開発者、コントリビューター

---

### 🚀 軽量環境用

#### `requirements-minimal.txt`
**用途**: 最小限の依存関係での実行
**内容**:
- コア依存関係のみ（pandas, numpy, matplotlib等）
- TA-Libを除外（インストールが困難な環境向け）
- 基本的な可視化ツール

**使用方法**:
```bash
pip install -r requirements/requirements-minimal.txt
```

**対象者**: 
- TA-Libのインストールが困難な環境
- 軽量なデプロイメント
- 基本機能のみ必要なユーザー

---

### 📊 株式データモジュール専用

#### `stock_data_requirements.txt`
**用途**: stock_dataモジュールの単体使用
**内容**:
- データ処理（pandas, numpy）
- 設定管理（PyYAML, python-dotenv）
- データ取得（yfinance, curl-cffi）
- Webスクレイピング（requests, beautifulsoup4, lxml）
- データベース（pymongo）
- ダッシュボード（streamlit, plotly）

**使用方法**:
```bash
pip install -r requirements/stock_data_requirements.txt
```

**対象者**:
- stock_dataモジュールのみを使用したいユーザー
- 株式データ取得・管理機能のみ必要な場合
- 他のプロジェクトでstock_dataを利用する場合

---

## 🎯 使用シナリオ別ガイド

### 新規開発者のセットアップ
```bash
# 1. 開発環境の完全セットアップ
pip install -r requirements/requirements-dev.txt

# 2. pre-commitフックの設定
pre-commit install
```

### プロダクション環境
```bash
# メインのrequirements.txtを使用
pip install -r requirements.txt
```

### CI/CD環境
```bash
# テスト実行用
pip install -r requirements/requirements-dev.txt
```

### 軽量デプロイメント
```bash
# TA-Libなしの軽量版
pip install -r requirements/requirements-minimal.txt
```

### 株式データ機能のみ使用
```bash
# stock_dataモジュール専用
pip install -r requirements/stock_data_requirements.txt
```

---

## 📝 ファイル管理ルール

### 依存関係の追加
1. **プロダクション依存関係**: メインの`requirements.txt`に追加
2. **開発ツール**: `requirements-dev.txt`に追加
3. **stock_data専用**: `stock_data_requirements.txt`に追加

### バージョン管理
- セマンティックバージョニングを使用
- 互換性のある範囲でバージョンを指定
- 例: `pandas>=1.3.0,<3.0.0`

### 更新手順
1. 依存関係を追加/更新
2. 各環境でテスト実行
3. 互換性を確認
4. ドキュメントを更新

---

## 🔍 トラブルシューティング

### よくある問題

#### TA-Libのインストールエラー
```bash
# 解決策: 軽量版を使用
pip install -r requirements/requirements-minimal.txt
```

#### 依存関係の競合
```bash
# 仮想環境を再作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/requirements-dev.txt
```

#### 古いパッケージバージョン
```bash
# パッケージを最新に更新
pip install --upgrade -r requirements.txt
```

---

## 📊 依存関係マップ

```
requirements.txt (メイン)
├── バックテスター機能
├── 株式データ機能
├── 可視化機能
└── 設定管理

requirements-dev.txt
├── requirements.txt (継承)
├── テストツール
├── コード品質ツール
└── 開発支援ツール

requirements-minimal.txt
├── コア機能のみ
└── TA-Lib除外

stock_data_requirements.txt
├── データ取得・処理
├── データベース管理
└── ダッシュボード機能
```

---

## 🚀 今後の拡張

### 予定されている追加
- [ ] GPU加速用パッケージ（cupy, rapids）
- [ ] 機械学習ライブラリ（scikit-learn, tensorflow）
- [ ] 高速データ処理（polars, dask）
- [ ] クラウド統合（boto3, azure-storage）

### 新しい環境ファイル
- [ ] `requirements-gpu.txt` - GPU加速環境用
- [ ] `requirements-ml.txt` - 機械学習機能用
- [ ] `requirements-cloud.txt` - クラウド統合用

---

## 📞 サポート

依存関係に関する問題や質問がある場合：

1. **GitHub Issues**: プロジェクトのIssueを作成
2. **ドキュメント**: メインREADMEを参照
3. **コミュニティ**: 開発者コミュニティで質問

---

**最終更新**: 2025年7月27日  
**管理者**: Stock Trading Backtester Team