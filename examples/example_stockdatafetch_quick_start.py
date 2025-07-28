#!/usr/bin/env python3
"""
クイックスタートガイド - ダッシュボード互換版

🎯 目的: 最短時間で株式データ取得システムを試す
📊 機能: 最小限の設定で基本機能を体験
🚀 実行方法: python examples/example_stockdatafetch_quick_start.py
👥 対象者: 初心者、システムを素早く試したい人
⏱️  実行時間: 約2-3分
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


def quick_setup():
    """クイックセットアップ"""
    print("⚡ クイックセットアップ中...")
    
    # ログ設定（簡易版）
    setup_logger()
    
    # ダッシュボード互換のデータベース構造を作成
    db_path = "data/stock_data.db"
    create_dashboard_compatible_database(db_path)
    conn = sqlite3.connect(db_path)
    
    print("✅ セットアップ完了!")
    return conn


def fetch_comprehensive_data(symbol, conn):
    """包括的なデータ取得（株価、企業情報、財務データ）"""
    try:
        ticker = yf.Ticker(symbol)
        success_count = 0
        cursor = conn.cursor()
        
        # 1. 株価データ取得（クイックスタートでは1年分）
        try:
            hist = ticker.history(period="1y")
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
                print(f"    ✅ 株価データ: {len(hist)}件")
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
                
                success_count += 1
                print(f"    ✅ 企業情報: 保存完了")
                
                # 3. 財務データ取得
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
                
                success_count += 1
                print(f"    ✅ 財務データ: 保存完了")
        except Exception as e:
            print(f"    ⚠️  企業情報取得エラー: {e}")
        
        conn.commit()
        return success_count > 0
        
    except Exception as e:
        print(f"    ❌ 全体エラー: {e}")
        return False


def fetch_sample_data(conn):
    """サンプルデータの取得"""
    print("\n📊 サンプルデータを取得中...")
    
    # 有名な銘柄を少数取得（高速化のため）
    sample_symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    print(f"対象銘柄: {', '.join(sample_symbols)}")
    print("⏳ 包括的データ取得中... (約1-2分)")
    
    # データ取得実行
    results = {}
    for symbol in sample_symbols:
        print(f"  📈 {symbol} のデータを取得中...")
        try:
            # 包括的データ取得関数を使用
            success = fetch_comprehensive_data(symbol, conn)
            results[symbol] = success
            
            if not success:
                print(f"    ❌ データ取得失敗")
                
        except Exception as e:
            print(f"    ❌ エラー: {e}")
            results[symbol] = False
        
        # API制限対策の待機
        time.sleep(2)
    
    # 結果表示
    successful = sum(1 for success in results.values() if success)
    print(f"✅ {successful}/{len(sample_symbols)} 銘柄のデータ取得完了")
    
    return results


def show_sample_analysis(conn):
    """簡単なデータ分析例"""
    print("\n📈 取得したデータの簡単な分析:")
    
    cursor = conn.cursor()
    
    # 利用可能な銘柄を取得
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    for symbol in symbols:
        print(f"\n📊 {symbol}:")
        
        # 企業情報
        cursor.execute("SELECT company_name, sector FROM company_info WHERE symbol = ?", (symbol,))
        company_info = cursor.fetchone()
        if company_info:
            print(f"  企業名: {company_info[0]}")
            print(f"  セクター: {company_info[1]}")
        
        # 最新の株価データ
        cursor.execute("""
            SELECT date, close_price, volume 
            FROM stock_data 
            WHERE symbol = ? 
            ORDER BY date DESC 
            LIMIT 2
        """, (symbol,))
        recent_data = cursor.fetchall()
        
        if recent_data:
            latest = recent_data[0]
            print(f"  最新価格: ${latest[1]:.2f}")
            print(f"  最新日付: {latest[0]}")
            print(f"  出来高: {latest[2]:,}")
            
            # 簡単な分析
            if len(recent_data) >= 2:
                prev_close = recent_data[1][1]
                change = latest[1] - prev_close
                change_pct = (change / prev_close) * 100
                print(f"  前日比: ${change:+.2f} ({change_pct:+.2f}%)")
        
        # 財務データ
        cursor.execute("""
            SELECT trailing_pe, dividend_yield 
            FROM financial_data 
            WHERE symbol = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (symbol,))
        financial_data = cursor.fetchone()
        
        if financial_data:
            if financial_data[0]:
                print(f"  PER: {financial_data[0]:.2f}")
            if financial_data[1]:
                dividend_yield = financial_data[1]
                if dividend_yield <= 1:
                    dividend_pct = dividend_yield * 100
                else:
                    dividend_pct = dividend_yield
                print(f"  配当利回り: {dividend_pct:.2f}%")


def show_next_steps():
    """次のステップの案内"""
    print(f"\n🎉 クイックスタート完了!")
    print(f"\n📋 次に試せること:")
    print(f"  1. ダッシュボードでデータ確認:")
    print(f"     python examples/example_dashboard_run_dashboard.py")
    print(f"  2. より多くの銘柄を取得:")
    print(f"     python examples/example_stockdatafetch_data_fetching.py")
    print(f"  3. 基本的な使用方法を学習:")
    print(f"     python examples/example_stockdatafetch_basic_stock_data.py")
    print(f"  4. バックテストとの連携:")
    print(f"     python examples/example_basktester_usage.py")
    
    print(f"\n💡 ヒント:")
    print(f"  - データは自動的にdata/stock_data.dbに保存されます")
    print(f"  - 同じスクリプトを再実行すると増分更新されます")
    print(f"  - SQLiteデータベースなので軽量で高速です")
    print(f"  - ダッシュボードで視覚的にデータを確認できます")


def main():
    """メイン関数"""
    
    print("🚀 株式データ取得システム - クイックスタート")
    print("=" * 60)
    print("このスクリプトは最短時間でシステムを体験できます")
    print("実行時間: 約2-3分")
    print()
    
    conn = None
    
    try:
        # 1. クイックセットアップ
        conn = quick_setup()
        
        # 2. サンプルデータ取得
        results = fetch_sample_data(conn)
        
        # 3. 簡単な分析表示
        show_sample_analysis(conn)
        
        # 4. 次のステップ案内
        show_next_steps()
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"\n🔧 トラブルシューティング:")
        print(f"  1. インターネット接続を確認")
        print(f"  2. data/フォルダが存在することを確認")
        print(f"  3. 必要なパッケージがインストールされていることを確認:")
        print(f"     pip install -r requirements.txt")
        
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        if conn:
            conn.close()
            print(f"\n🔌 データベース接続を切断しました")


if __name__ == "__main__":
    main()