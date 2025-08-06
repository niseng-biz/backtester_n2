#!/usr/bin/env python3
"""
配当利回りデータの問題を調査するスクリプト
"""

import os
import sqlite3

import pandas as pd


def debug_dividend_yield(db_path: str = "stock_data.db"):
    """配当利回りデータを調査"""
    
    if not os.path.exists(db_path):
        print(f"データベースファイル {db_path} が見つかりません。")
        return
    
    conn = sqlite3.connect(db_path)
    
    print("=" * 60)
    print("配当利回りデータの調査")
    print("=" * 60)
    
    # 配当利回りの統計
    query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(dividend_yield) as non_null_records,
            MIN(dividend_yield) as min_yield,
            MAX(dividend_yield) as max_yield,
            AVG(dividend_yield) as avg_yield,
            MEDIAN(dividend_yield) as median_yield
        FROM financial_data
        WHERE dividend_yield IS NOT NULL
    """
    
    try:
        df_stats = pd.read_sql_query(query, conn)
        print("配当利回り統計:")
        print(f"総レコード数: {df_stats.iloc[0]['total_records']}")
        print(f"非NULL数: {df_stats.iloc[0]['non_null_records']}")
        print(f"最小値: {df_stats.iloc[0]['min_yield']:.6f}")
        print(f"最大値: {df_stats.iloc[0]['max_yield']:.6f}")
        print(f"平均値: {df_stats.iloc[0]['avg_yield']:.6f}")
        print(f"中央値: {df_stats.iloc[0]['median_yield']:.6f}")
    except Exception as e:
        print(f"統計取得エラー: {e}")
    
    print("\n" + "=" * 60)
    
    # 異常に高い配当利回りの銘柄を確認
    query_high = """
        SELECT 
            c.symbol, 
            c.company_name, 
            f.dividend_yield,
            f.dividend_rate,
            f.current_price
        FROM company_info c
        JOIN financial_data f ON c.symbol = f.symbol
        WHERE f.dividend_yield > 0.1  -- 10%以上
        ORDER BY f.dividend_yield DESC
        LIMIT 20
    """
    
    df_high = pd.read_sql_query(query_high, conn)
    
    print("異常に高い配当利回り（10%以上）の銘柄:")
    print("-" * 60)
    for _, row in df_high.iterrows():
        dividend_pct = row['dividend_yield'] * 100 if row['dividend_yield'] else 0
        print(f"{row['symbol']:<6} {row['company_name'][:30]:<30} "
              f"利回り: {dividend_pct:>7.2f}% "
              f"配当: ${row['dividend_rate'] or 0:.2f} "
              f"価格: ${row['current_price'] or 0:.2f}")
    
    print("\n" + "=" * 60)
    
    # 正常範囲の配当利回りの銘柄を確認
    query_normal = """
        SELECT 
            c.symbol, 
            c.company_name, 
            f.dividend_yield,
            f.dividend_rate,
            f.current_price
        FROM company_info c
        JOIN financial_data f ON c.symbol = f.symbol
        WHERE f.dividend_yield > 0 AND f.dividend_yield <= 0.1  -- 0-10%
        ORDER BY f.dividend_yield DESC
        LIMIT 10
    """
    
    df_normal = pd.read_sql_query(query_normal, conn)
    
    print("正常範囲の配当利回り（0-10%）の銘柄:")
    print("-" * 60)
    for _, row in df_normal.iterrows():
        dividend_pct = row['dividend_yield'] * 100 if row['dividend_yield'] else 0
        print(f"{row['symbol']:<6} {row['company_name'][:30]:<30} "
              f"利回り: {dividend_pct:>7.2f}% "
              f"配当: ${row['dividend_rate'] or 0:.2f} "
              f"価格: ${row['current_price'] or 0:.2f}")
    
    print("\n" + "=" * 60)
    
    # yfinanceから取得した生データを確認
    print("yfinanceデータの形式確認:")
    query_raw = """
        SELECT 
            symbol,
            dividend_yield,
            dividend_rate,
            current_price
        FROM financial_data
        WHERE dividend_yield IS NOT NULL
        LIMIT 5
    """
    
    df_raw = pd.read_sql_query(query_raw, conn)
    print("生データサンプル:")
    for _, row in df_raw.iterrows():
        print(f"Symbol: {row['symbol']}")
        print(f"  dividend_yield (raw): {row['dividend_yield']}")
        print(f"  dividend_rate: {row['dividend_rate']}")
        print(f"  current_price: {row['current_price']}")
        print()
    
    conn.close()

if __name__ == "__main__":
    debug_dividend_yield()