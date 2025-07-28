#!/usr/bin/env python3
"""
データベースセットアップ例 - ダッシュボード互換版

🎯 目的: データベースの初期セットアップと基本設定
📊 機能: テーブル作成、初期データ投入、設定確認
🚀 実行方法: python examples/example_stockdatafetch_database_setup_example.py
👥 対象者: システム管理者、初期セットアップを行う開発者
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
from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source


def create_dashboard_compatible_database(db_path):
    """ダッシュボード互換のデータベース構造を作成"""
    print("🗄️  データベーステーブルを作成中...")
    
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
    print("  ✅ company_info テーブル作成完了")
    
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
    print("  ✅ stock_data テーブル作成完了")
    
    # financial_data テーブル（ダッシュボード互換）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            market_cap REAL,
            enterprise_value REAL,
            trailing_pe REAL,
            forward_pe REAL,
            peg_ratio REAL,
            price_to_book REAL,
            price_to_sales REAL,
            enterprise_to_revenue REAL,
            enterprise_to_ebitda REAL,
            trailing_eps REAL,
            forward_eps REAL,
            book_value REAL,
            return_on_assets REAL,
            return_on_equity REAL,
            revenue_per_share REAL,
            profit_margins REAL,
            operating_margins REAL,
            ebitda_margins REAL,
            gross_margins REAL,
            dividend_rate REAL,
            dividend_yield REAL,
            payout_ratio REAL,
            beta REAL,
            week_52_high REAL,
            week_52_low REAL,
            current_price REAL,
            target_high_price REAL,
            target_low_price REAL,
            target_mean_price REAL,
            recommendation_mean REAL,
            number_of_analyst_opinions INTEGER,
            total_cash REAL,
            total_cash_per_share REAL,
            ebitda REAL,
            total_debt REAL,
            quick_ratio REAL,
            current_ratio REAL,
            total_revenue REAL,
            debt_to_equity REAL,
            revenue_growth REAL,
            earnings_growth REAL,
            free_cashflow REAL,
            operating_cashflow REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    print("  ✅ financial_data テーブル作成完了")
    
    conn.commit()
    conn.close()
    print("✅ データベース構造作成完了")


def get_target_symbols():
    """対象シンボルを取得"""
    print("📊 対象シンボルを取得中...")
    
    try:
        # S&P 500とNASDAQ 100のシンボルを取得
        source = SP500Nasdaq100Source()
        symbol_infos = source.fetch_symbols()
        
        # SymbolInfoオブジェクトからシンボル文字列を抽出
        symbols = [info.symbol for info in symbol_infos]
        
        print(f"  ✅ {len(symbols)}個のシンボルを取得")
        return symbols
        
    except Exception as e:
        print(f"  ⚠️  シンボル取得エラー、フォールバックを使用: {e}")
        # フォールバック: 主要銘柄
        fallback = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS'
        ]
        return fallback


def setup_initial_data(conn, symbols):
    """初期データのセットアップ"""
    print("\n🔧 初期データを投入中...")
    
    cursor = conn.cursor()
    
    # サンプル銘柄のデータを取得
    sample_symbols = symbols[:3]  # 最初の3銘柄のみ（セットアップなので軽量化）
    for symbol in sample_symbols:
        try:
            print(f"  📈 {symbol} の企業情報を取得中...")
            ticker = yf.Ticker(symbol)
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
                
                print(f"    ✅ {symbol} の企業情報を保存")
                
                # 財務データも保存
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
                    (symbol, date, market_cap, enterprise_value, trailing_pe, forward_pe, peg_ratio, price_to_book, 
                     price_to_sales, enterprise_to_revenue, enterprise_to_ebitda, trailing_eps, forward_eps, book_value,
                     return_on_assets, return_on_equity, revenue_per_share, profit_margins, operating_margins, 
                     ebitda_margins, gross_margins, dividend_rate, dividend_yield, payout_ratio, beta, 
                     week_52_high, week_52_low, current_price, target_high_price, target_low_price, target_mean_price,
                     recommendation_mean, number_of_analyst_opinions, total_cash, total_cash_per_share, ebitda,
                     total_debt, quick_ratio, current_ratio, total_revenue, debt_to_equity, revenue_growth,
                     earnings_growth, free_cashflow, operating_cashflow)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    today,
                    safe_get('marketCap'),
                    safe_get('enterpriseValue'),
                    safe_get('trailingPE'),
                    safe_get('forwardPE'),
                    safe_get('pegRatio'),
                    safe_get('priceToBook'),
                    safe_get('priceToSalesTrailing12Months'),
                    safe_get('enterpriseToRevenue'),
                    safe_get('enterpriseToEbitda'),
                    safe_get('trailingEps'),
                    safe_get('forwardEps'),
                    safe_get('bookValue'),
                    safe_get('returnOnAssets'),
                    safe_get('returnOnEquity'),
                    safe_get('revenuePerShare'),
                    safe_get('profitMargins'),
                    safe_get('operatingMargins'),
                    safe_get('ebitdaMargins'),
                    safe_get('grossMargins'),
                    safe_get('dividendRate'),
                    dividend_yield,
                    safe_get('payoutRatio'),
                    safe_get('beta'),
                    safe_get('fiftyTwoWeekHigh'),
                    safe_get('fiftyTwoWeekLow'),
                    safe_get('currentPrice'),
                    safe_get('targetHighPrice'),
                    safe_get('targetLowPrice'),
                    safe_get('targetMeanPrice'),
                    safe_get('recommendationMean'),
                    safe_get('numberOfAnalystOpinions'),
                    safe_get('totalCash'),
                    safe_get('totalCashPerShare'),
                    safe_get('ebitda'),
                    safe_get('totalDebt'),
                    safe_get('quickRatio'),
                    safe_get('currentRatio'),
                    safe_get('totalRevenue'),
                    safe_get('debtToEquity'),
                    safe_get('revenueGrowth'),
                    safe_get('earningsGrowth'),
                    safe_get('freeCashflow'),
                    safe_get('operatingCashflow')
                ))
                
                print(f"    ✅ {symbol} の財務データを保存")
                
        except Exception as e:
            print(f"    ⚠️  {symbol} のデータ取得をスキップ: {e}")
        
        # API制限対策
        time.sleep(2)
    
    conn.commit()
    print("  ✅ 初期データ投入完了")


def verify_setup(conn):
    """セットアップの確認"""
    print("\n🔍 セットアップ確認中...")
    
    cursor = conn.cursor()
    
    # テーブル存在確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['company_info', 'stock_data', 'financial_data']
    for table in expected_tables:
        if table in tables:
            print(f"  ✅ {table} テーブル: 存在")
        else:
            print(f"  ❌ {table} テーブル: 存在しない")
    
    # データ確認
    cursor.execute("SELECT COUNT(*) FROM company_info")
    company_count = cursor.fetchone()[0]
    print(f"  📊 企業情報: {company_count}件")
    
    cursor.execute("SELECT COUNT(*) FROM financial_data")
    financial_count = cursor.fetchone()[0]
    print(f"  📊 財務データ: {financial_count}件")
    
    cursor.execute("SELECT COUNT(*) FROM stock_data")
    stock_count = cursor.fetchone()[0]
    print(f"  📊 株価データ: {stock_count}件")
    
    # サンプルデータ表示
    if company_count > 0:
        print(f"\n📈 サンプル企業情報:")
        cursor.execute("SELECT symbol, company_name, sector FROM company_info LIMIT 3")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} ({row[2]})")


def show_next_steps():
    """次のステップの案内"""
    print(f"\n🎉 データベースセットアップ完了!")
    print(f"\n📋 次のステップ:")
    print(f"  1. 株価データを取得:")
    print(f"     python examples/example_stockdatafetch_data_fetching.py")
    print(f"  2. クイックスタートを試す:")
    print(f"     python examples/example_stockdatafetch_quick_start.py")
    print(f"  3. ダッシュボードでデータ確認:")
    print(f"     python examples/example_dashboard_run_dashboard.py")
    print(f"  4. バックテストとの連携:")
    print(f"     python examples/example_basktester_usage.py")
    
    print(f"\n💡 重要な情報:")
    print(f"  - データベースファイル: data/stock_data.db")
    print(f"  - ダッシュボード互換の構造で作成されています")
    print(f"  - 企業情報、株価データ、財務データの3つのテーブルがあります")
    print(f"  - 増分更新に対応しています")


def main():
    """メイン関数"""
    
    # ログ設定
    setup_logger()
    
    print("🚀 データベースセットアップ例")
    print("=" * 50)
    print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = None
    
    try:
        # 1. 設定管理システム初期化
        print("\n🔧 設定管理システム初期化中...")
        config_manager = get_config_manager()
        print("✅ 設定管理システム初期化完了")
        
        # 2. データベース作成
        db_path = "data/stock_data.db"
        create_dashboard_compatible_database(db_path)
        conn = sqlite3.connect(db_path)
        
        # 3. 対象シンボル取得
        symbols = get_target_symbols()
        
        # 4. 初期データの投入（サンプル）
        setup_initial_data(conn, symbols)
        
        # 5. セットアップ確認
        verify_setup(conn)
        
        # 6. 次のステップ案内
        show_next_steps()
        
    except Exception as e:
        print(f"\n❌ セットアップ中にエラーが発生しました: {e}")
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