#!/usr/bin/env python3
"""
株式データダッシュボードを起動するスクリプト
"""

import os
import subprocess
import sys


def main():
    """ダッシュボードを起動"""
    
    # データベースファイルの存在確認
    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        print(f"❌ データベースファイル '{db_path}' が見つかりません。")
        print("📥 まず以下のコマンドでデータを取得してください:")
        print("   python scripts/fetch_sp500_nasdaq100_sqlite.py")
        return
    
    print("🚀 株式データダッシュボードを起動しています...")
    print("🌐 ブラウザで http://localhost:8501 が開きます")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 50)
    
    try:
        # Streamlitアプリを起動
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "examples/example_dashboard_advanced_stock_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n✅ ダッシュボードを停止しました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()