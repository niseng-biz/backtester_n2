#!/usr/bin/env python3
"""
SQLiteデータベースの統計情報を確認するスクリプト
"""

import os
import sqlite3
from datetime import datetime


def check_database_stats(db_path: str = "data/stock_data.db"):
    """データベースの統計情報を表示"""
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("STOCK DATABASE STATISTICS")
    print("=" * 60)
    
    # 会社情報統計
    cursor.execute("SELECT COUNT(*) FROM company_info")
    company_count = cursor.fetchone()[0]
    print(f"Total Companies: {company_count:,}")
    
    # セクター別統計
    cursor.execute("""
        SELECT sector, COUNT(*) as count 
        FROM company_info 
        WHERE sector IS NOT NULL 
        GROUP BY sector 
        ORDER BY count DESC
    """)
    sectors = cursor.fetchall()
    
    print(f"\nSector Distribution:")
    print("-" * 40)
    for sector, count in sectors:
        print(f"{sector:<30} {count:>3} companies")
    
    # 株価データ統計
    cursor.execute("SELECT COUNT(*) FROM stock_data")
    stock_records = cursor.fetchone()[0]
    print(f"\nStock Price Records: {stock_records:,}")
    
    # 株価データの期間
    cursor.execute("SELECT MIN(date), MAX(date) FROM stock_data")
    min_date, max_date = cursor.fetchone()
    print(f"Date Range: {min_date} to {max_date}")
    
    # 銘柄別株価データ数（上位10銘柄）
    cursor.execute("""
        SELECT symbol, COUNT(*) as records 
        FROM stock_data 
        GROUP BY symbol 
        ORDER BY records DESC 
        LIMIT 10
    """)
    top_symbols = cursor.fetchall()
    
    print(f"\nTop 10 Symbols by Historical Data:")
    print("-" * 40)
    for symbol, records in top_symbols:
        print(f"{symbol:<10} {records:>6} records")
    
    # 財務データ統計
    cursor.execute("SELECT COUNT(*) FROM financial_data")
    financial_records = cursor.fetchone()[0]
    print(f"\nFinancial Data Records: {financial_records:,}")
    
    # 財務指標の統計（NULL以外の値を持つ銘柄数）
    financial_metrics = [
        'trailing_pe', 'forward_pe', 'trailing_eps', 'forward_eps',
        'price_to_book', 'return_on_equity', 'debt_to_equity',
        'dividend_yield', 'market_cap', 'beta'
    ]
    
    print(f"\nFinancial Metrics Coverage:")
    print("-" * 40)
    for metric in financial_metrics:
        cursor.execute(f"SELECT COUNT(*) FROM financial_data WHERE {metric} IS NOT NULL")
        count = cursor.fetchone()[0]
        coverage = (count / company_count * 100) if company_count > 0 else 0
        print(f"{metric:<20} {count:>3} symbols ({coverage:>5.1f}%)")
    
    # 高PER銘柄（上位10）
    cursor.execute("""
        SELECT c.symbol, c.company_name, f.trailing_pe
        FROM company_info c
        JOIN financial_data f ON c.symbol = f.symbol
        WHERE f.trailing_pe IS NOT NULL AND f.trailing_pe > 0
        ORDER BY f.trailing_pe DESC
        LIMIT 10
    """)
    high_pe_stocks = cursor.fetchall()
    
    print(f"\nTop 10 Highest P/E Ratios:")
    print("-" * 60)
    for symbol, name, pe in high_pe_stocks:
        print(f"{symbol:<6} {name[:30]:<30} P/E: {pe:>8.2f}")
    
    # 高配当利回り銘柄（上位10）
    cursor.execute("""
        SELECT c.symbol, c.company_name, f.dividend_yield
        FROM company_info c
        JOIN financial_data f ON c.symbol = f.symbol
        WHERE f.dividend_yield IS NOT NULL AND f.dividend_yield > 0
        ORDER BY f.dividend_yield DESC
        LIMIT 10
    """)
    high_dividend_stocks = cursor.fetchall()
    
    print(f"\nTop 10 Highest Dividend Yields:")
    print("-" * 60)
    for symbol, name, dividend_yield in high_dividend_stocks:
        dividend_pct = dividend_yield * 100
        print(f"{symbol:<6} {name[:30]:<30} Yield: {dividend_pct:>7.2f}%")
    
    # 時価総額上位10銘柄
    cursor.execute("""
        SELECT c.symbol, c.company_name, f.market_cap
        FROM company_info c
        JOIN financial_data f ON c.symbol = f.symbol
        WHERE f.market_cap IS NOT NULL
        ORDER BY f.market_cap DESC
        LIMIT 10
    """)
    large_cap_stocks = cursor.fetchall()
    
    print(f"\nTop 10 Largest Market Cap:")
    print("-" * 60)
    for symbol, name, market_cap in large_cap_stocks:
        market_cap_b = market_cap / 1e9  # Convert to billions
        print(f"{symbol:<6} {name[:30]:<30} ${market_cap_b:>8.1f}B")
    
    # データベースファイルサイズ
    file_size = os.path.getsize(db_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"\nDatabase File Size: {file_size_mb:.1f} MB")
    
    conn.close()
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check SQLite database statistics')
    parser.add_argument('--db-path', type=str, default='data/stock_data.db', help='SQLite database file path')
    
    args = parser.parse_args()
    check_database_stats(args.db_path)