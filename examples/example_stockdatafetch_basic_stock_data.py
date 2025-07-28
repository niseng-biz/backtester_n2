#!/usr/bin/env python3
"""
基本的な株式データ取得例 - ダッシュボード互換版

🎯 目的: 基本的なデータ取得パターンを学習
📊 機能: 個別銘柄データ取得、基本的なエラーハンドリング
🚀 実行方法: python examples/example_stockdatafetch_basic_stock_data.py
👥 対象者: 基本機能を理解したい開発者
"""

import os
import sqlite3
import sys
import time
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import yfinance as yf

from stock_database import setup_logger
from stock_database.config import get_config_manager


def create_dashboard_compatible_database(db_path):
    """ダッシュボード互換のデータベース構造を作成"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # company_info テーブル（ダッシュボード互換）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_info (
            symbol TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            exchange TEXT,
            market_cap REAL,
            employees INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # stock_data テーブル（ダッシュボード互換）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            adjusted_close REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    # financial_data テーブル（ダッシュボード互換）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            trailing_pe REAL,
            trailing_eps REAL,
            price_to_book REAL,
            return_on_equity REAL,
            debt_to_equity REAL,
            dividend_yield REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    conn.commit()
    conn.close()


def fetch_comprehensive_data(symbol, conn):
    """包括的なデータ取得（株価、企業情報、財務データ）"""
    try:
        ticker = yf.Ticker(symbol)
        success_count = 0
        cursor = conn.cursor()
        
        # 1. 株価データ取得（基本例では2年分）
        try:
            hist = ticker.history(period="2y")
            if not hist.empty:
                for date, row in hist.iterrows():
                    # NaNや無効な値をチェック
                    open_price = row.get('Open', 0)
                    high_price = row.get('High', 0)
                    low_price = row.get('Low', 0)
                    close_price = row.get('Close', 0)
                    volume = row.get('Volume', 0)
                    
                    # NaNをチェックして適切な値に置換
                    open_price = float(open_price) if pd.notna(open_price) else None
                    high_price = float(high_price) if pd.notna(high_price) else None
                    low_price = float(low_price) if pd.notna(low_price) else None
                    close_price = float(close_price) if pd.notna(close_price) else None
                    volume = int(volume) if pd.notna(volume) else None
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO stock_data 
                        (symbol, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        date.strftime('%Y-%m-%d'),
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                        close_price
                    ))
                
                success_count += 1
                print(f"    ✅ {len(hist)}件の株価データを保存")
        except Exception as e:
            print(f"    ⚠️  株価データ取得エラー: {e}")
        
        # 2. 企業情報取得
        try:
            info = ticker.info
            if info:
                # 企業情報を保存
                market_cap = info.get('marketCap')
                if market_cap is not None and pd.isna(market_cap):
                    market_cap = None
                
                employees = info.get('fullTimeEmployees')
                if employees is not None and pd.isna(employees):
                    employees = None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO company_info 
                    (symbol, company_name, sector, industry, exchange, market_cap, employees, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    info.get('longName', info.get('shortName', symbol)),
                    info.get('sector', ''),
                    info.get('industry', ''),
                    info.get('exchange', ''),
                    market_cap,
                    employees,
                    info.get('longBusinessSummary', '')
                ))
                
                print(f"    ✅ 企業情報を保存")
                success_count += 1
                
                # 3. 財務データ取得（基本例では簡略化）
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 各財務データをNaNチェック付きで取得
                def safe_get(key, default=None):
                    value = info.get(key, default)
                    if value is not None and pd.isna(value):
                        return None
                    return value
                
                # 配当利回りの正規化
                dividend_yield = safe_get('dividendYield')
                if dividend_yield is not None:
                    dividend_yield = dividend_yield / 100
                
                cursor.execute('''
                    INSERT OR REPLACE INTO financial_data 
                    (symbol, date, trailing_pe, trailing_eps, price_to_book, return_on_equity, debt_to_equity, dividend_yield)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    today,
                    safe_get('trailingPE'),
                    safe_get('trailingEps'),
                    safe_get('priceToBook'),
                    safe_get('returnOnEquity'),
                    safe_get('debtToEquity'),
                    dividend_yield
                ))
                
                print(f"    ✅ 財務データを保存")
                success_count += 1
        except Exception as e:
            print(f"    ⚠️  企業情報取得エラー: {e}")
        
        conn.commit()
        return success_count > 0
        
    except Exception as e:
        print(f"    ❌ 全体エラー: {e}")
        return False


def main():
    """メイン関数"""
    
    # ログ設定
    setup_logger()
    
    print("🚀 基本的な株式データ取得例")
    print("=" * 50)
    print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = None
    
    try:
        # 1. システム初期化
        print("\n🔧 システム初期化中...")
        config_manager = get_config_manager()
        
        # ダッシュボード互換のデータベース構造を作成
        db_path = "data/stock_data.db"
        create_dashboard_compatible_database(db_path)
        conn = sqlite3.connect(db_path)
        
        print("✅ システム初期化完了")
        
        # 2. テスト用銘柄でデータ取得
        print("\n📊 テスト用銘柄のデータ取得...")
        test_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        
        results = {}
        total_records = 0
        
        for symbol in test_symbols:
            print(f"  📈 {symbol} のデータを取得中...")
            try:
                # 包括的データ取得関数を使用
                success = fetch_comprehensive_data(symbol, conn)
                results[symbol] = success
                
                if success:
                    # 取得したレコード数を概算
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM stock_data WHERE symbol = ?", (symbol,))
                    count = cursor.fetchone()[0]
                    total_records += count
                else:
                    print(f"    ❌ データ取得失敗")
                    
            except Exception as e:
                print(f"    ❌ エラー: {e}")
                results[symbol] = False
            
            # API制限対策の待機
            time.sleep(2)
        
        # 3. 結果表示
        successful = sum(1 for success in results.values() if success)
        print(f"\n✅ {successful}/{len(test_symbols)} 銘柄のデータ取得完了")
        print(f"📊 総取得レコード数: {total_records:,}")
        
        # 4. データベース統計
        print(f"\n📊 データベース統計:")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        stock_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_data")
        stock_symbols = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM company_info")
        company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM financial_data")
        financial_count = cursor.fetchone()[0]
        
        print(f"  株価データ: {stock_count:,}件")
        print(f"  企業情報: {company_count:,}件")
        print(f"  財務データ: {financial_count:,}件")
        print(f"  利用可能銘柄数: {stock_symbols}")
        
        # 5. サンプルデータ表示
        print(f"\n📈 サンプルデータ:")
        for symbol in ['AAPL', 'GOOGL']:
            if results.get(symbol):
                cursor.execute("""
                    SELECT c.company_name, c.sector, s.close_price, s.date
                    FROM company_info c
                    JOIN stock_data s ON c.symbol = s.symbol
                    WHERE c.symbol = ?
                    ORDER BY s.date DESC
                    LIMIT 1
                """, (symbol,))
                
                data = cursor.fetchone()
                if data:
                    print(f"  {symbol}: {data[0]} ({data[1]}) - ${data[2]:.2f} ({data[3]})")
        
        print(f"\n📋 次のステップ:")
        print(f"  1. ダッシュボードでデータ確認: python examples/example_dashboard_run_dashboard.py")
        print(f"  2. より多くの銘柄を取得: python examples/example_stockdatafetch_data_fetching.py")
        print(f"  3. バックテストとの連携: python examples/example_basktester_usage.py")
        print(f"  4. データベースファイル: data/stock_data.db")
        
    except Exception as e:
        print(f"\n❌ データ取得中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        if conn:
            conn.close()
            print(f"\n🔌 データベース接続を切断しました")
        
        print(f"実行終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()