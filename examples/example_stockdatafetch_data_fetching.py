#!/usr/bin/env python3
"""
実践的なデータ取得例 - ダッシュボード互換版

🎯 目的: ダッシュボードで表示可能な形式でデータを取得
📊 機能: 大量データ取得、増分更新、エラーハンドリング、進捗表示
🚀 実行方法: python examples/example_stockdatafetch_data_fetching.py
👥 対象者: 実際にシステムを運用する開発者
"""

import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import yfinance as yf

from stock_database import setup_logger
from stock_database.config import get_config_manager
from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source


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
    
    # インデックス作成（パフォーマンス向上のため）
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_data(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_data(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_symbol ON financial_data(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_data(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_sector ON company_info(sector)")
    
    conn.commit()
    conn.close()


def fetch_comprehensive_data(symbol, conn):
    """包括的なデータ取得（株価、企業情報、財務データ）"""
    try:
        ticker = yf.Ticker(symbol)
        success_count = 0
        cursor = conn.cursor()
        info = None  # infoを事前に初期化
        
        # 1. 株価データ取得
        try:
            hist = ticker.history(period="max")
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
        
        # 2. 企業情報と財務データ取得（infoを一度だけ取得）
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
                
                # 財務データを保存
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 各財務データをNaNチェック付きで取得
                def safe_get(key, default=None):
                    value = info.get(key, default)
                    if value is not None and pd.isna(value):
                        return None
                    return value
                
                # 配当利回りの正規化（yfinanceの値は既にパーセンテージ形式なので100で割る）
                dividend_yield = safe_get('dividendYield')
                if dividend_yield is not None:
                    # yfinanceのdividendYieldは既にパーセンテージ形式（6.29 = 6.29%）
                    # 小数形式に変換（6.29 -> 0.0629）
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
                
                success_count += 1
                print(f"    ✅ 財務データ: 保存完了")
                
        except Exception as e:
            print(f"    ⚠️  企業情報・財務データ取得エラー: {e}")
        
        conn.commit()
        return success_count > 0
        
    except Exception as e:
        print(f"    ❌ 全体エラー: {e}")
        return False


def get_target_symbols(limit=None):
    """取得対象のシンボルリストを取得"""
    print("📊 取得対象シンボルを準備中...")
    
    try:
        # S&P 500とNASDAQ 100のシンボルを取得
        source = SP500Nasdaq100Source()
        symbol_infos = source.fetch_symbols()
        
        # SymbolInfoオブジェクトからシンボル文字列を抽出
        all_symbols = [info.symbol for info in symbol_infos]
        
        # 制限がある場合は先頭から取得
        if limit:
            all_symbols = all_symbols[:limit]
        
        print(f"  ✅ 対象シンボル数: {len(all_symbols)}")
        return all_symbols
        
    except Exception as e:
        print(f"  ⚠️  シンボル取得エラー、フォールバックを使用: {e}")
        # フォールバック: 主要銘柄
        fallback = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS',
            'PYPL', 'BAC', 'NFLX', 'ADBE', 'CRM', 'CMCSA', 'XOM'
        ]
        return fallback[:limit] if limit else fallback


def batch_data_fetching(conn, symbols, batch_size=5):
    """バッチ処理でデータを取得"""
    print(f"\n📈 バッチ処理でデータ取得開始 (バッチサイズ: {batch_size})")
    
    total_symbols = len(symbols)
    successful_symbols = []
    failed_symbols = []
    
    # バッチに分割して処理
    for i in range(0, total_symbols, batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_symbols + batch_size - 1) // batch_size
        
        print(f"\n🔄 バッチ {batch_num}/{total_batches} 処理中...")
        print(f"  対象銘柄: {', '.join(batch)}")
        
        try:
            # バッチ処理実行
            start_time = time.time()
            batch_successful = []
            batch_failed = []
            
            for symbol in batch:
                print(f"  📈 {symbol} のデータを取得中...")
                try:
                    success = fetch_comprehensive_data(symbol, conn)
                    if success:
                        batch_successful.append(symbol)
                    else:
                        batch_failed.append(symbol)
                        
                except Exception as e:
                    print(f"    ❌ {symbol}: {e}")
                    batch_failed.append(symbol)
                
                # API制限対策の待機
                time.sleep(1)
            
            duration = time.time() - start_time
            
            successful_symbols.extend(batch_successful)
            failed_symbols.extend(batch_failed)
            
            # バッチ結果表示
            print(f"  ✅ 成功: {len(batch_successful)}/{len(batch)}")
            print(f"  ❌ 失敗: {len(batch_failed)}/{len(batch)}")
            print(f"  ⏱️  処理時間: {duration:.2f}秒")
            
            # バッチ間の待機（API制限対策）
            if i + batch_size < total_symbols:
                print("  ⏳ 次のバッチまで待機中...")
                time.sleep(3)  # 3秒待機
                
        except Exception as e:
            print(f"  ❌ バッチ処理エラー: {e}")
            failed_symbols.extend(batch)
    
    return successful_symbols, failed_symbols


def retry_failed_symbols(conn, failed_symbols, max_retries=3):
    """失敗したシンボルの再試行"""
    if not failed_symbols:
        return []
    
    print(f"\n🔄 失敗した{len(failed_symbols)}銘柄の再試行...")
    
    current_failed = failed_symbols.copy()
    
    for retry in range(max_retries):
        if not current_failed:
            break
            
        print(f"\n  🔄 再試行 {retry + 1}/{max_retries}")
        print(f"  対象: {', '.join(current_failed)}")
        
        try:
            successful = []
            still_failed = []
            
            for symbol in current_failed:
                try:
                    success = fetch_comprehensive_data(symbol, conn)
                    if success:
                        successful.append(symbol)
                    else:
                        still_failed.append(symbol)
                        
                except Exception as e:
                    print(f"    ❌ {symbol}: {e}")
                    still_failed.append(symbol)
                
                # 再試行時の待機
                time.sleep(2)
            
            print(f"    ✅ 成功: {len(successful)}")
            print(f"    ❌ 依然失敗: {len(still_failed)}")
            
            current_failed = still_failed
            
            # 再試行間の待機
            if current_failed and retry < max_retries - 1:
                time.sleep(10)  # 10秒待機
                
        except Exception as e:
            print(f"    ❌ 再試行エラー: {e}")
    
    return current_failed


def display_final_statistics(conn, successful_symbols, failed_symbols):
    """最終統計の表示"""
    print(f"\n📊 最終統計情報")
    print("=" * 40)
    
    try:
        # データ取得統計
        total_symbols = len(successful_symbols) + len(failed_symbols)
        print(f"データ取得統計:")
        print(f"  処理銘柄数: {total_symbols}")
        print(f"  成功銘柄数: {len(successful_symbols)}")
        print(f"  失敗銘柄数: {len(failed_symbols)}")
        
        # データベース統計
        cursor = conn.cursor()
        
        # 株価データ統計
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        stock_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_data")
        stock_symbols = cursor.fetchone()[0]
        
        # 企業情報統計
        cursor.execute("SELECT COUNT(*) FROM company_info")
        company_count = cursor.fetchone()[0]
        
        # 財務データ統計
        cursor.execute("SELECT COUNT(*) FROM financial_data")
        financial_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM financial_data")
        financial_symbols = cursor.fetchone()[0]
        
        print(f"\nデータベース統計:")
        print(f"  株価データ: {stock_count:,}件")
        print(f"  企業情報: {company_count:,}件")
        print(f"  財務データ: {financial_count:,}件")
        print(f"  株価データ銘柄数: {stock_symbols}")
        print(f"  財務データ銘柄数: {financial_symbols}")
        
        # 最新データの確認
        if successful_symbols:
            sample_symbol = successful_symbols[0]
            cursor.execute("SELECT MAX(date) FROM stock_data WHERE symbol = ?", (sample_symbol,))
            latest_date = cursor.fetchone()[0]
            print(f"  最新データ日付: {latest_date}")
        
    except Exception as e:
        print(f"統計情報取得エラー: {e}")


def main():
    """メイン関数"""
    
    # ログ設定
    setup_logger()
    
    print("🚀 実践的なデータ取得例 - ダッシュボード互換版")
    print("=" * 50)
    print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = None
    
    try:
        # 1. システム初期化
        print("\n🔧 システム初期化中...")
        db_path = "data/stock_data.db"
        
        # ダッシュボード互換のデータベース構造を作成
        create_dashboard_compatible_database(db_path)
        conn = sqlite3.connect(db_path)
        
        print("✅ システム初期化完了")
        
        # 2. 対象シンボル取得
        # 実際の運用では制限を外すか、より大きな値を設定
        symbols = get_target_symbols(limit=5000)  # デモ用に50銘柄に制限
        
        # 3. バッチ処理でデータ取得
        successful_symbols, failed_symbols = batch_data_fetching(
            conn, symbols, batch_size=5  # API制限を考慮してバッチサイズを小さく
        )
        
        # 4. 失敗したシンボルの再試行
        permanently_failed = retry_failed_symbols(conn, failed_symbols)
        
        # 5. 最終統計表示
        display_final_statistics(conn, successful_symbols, permanently_failed)
        
        # 6. 結果サマリー
        print(f"\n🎉 包括的データ取得完了!")
        print(f"✅ 成功: {len(successful_symbols)}/{len(symbols)} 銘柄")
        if permanently_failed:
            print(f"❌ 最終的に失敗: {len(permanently_failed)} 銘柄")
            print(f"   失敗銘柄: {', '.join(permanently_failed[:10])}{'...' if len(permanently_failed) > 10 else ''}")
        
        print(f"\n📋 取得データ種類:")
        print(f"  📈 株価データ（日次）")
        print(f"  🏢 企業情報")
        print(f"  💰 財務データ（年次）")
        
        print(f"\n📋 次のステップ:")
        print(f"  1. ダッシュボードでデータ確認: python examples/example_dashboard_run_dashboard.py")
        print(f"  2. バックテストシステムとの連携: python examples/example_basktester_usage.py")
        print(f"  3. 定期的な増分更新スケジュールの設定")
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