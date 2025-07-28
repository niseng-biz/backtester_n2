#!/usr/bin/env python3
"""
データベース内の配当利回りデータを修正するスクリプト
"""

import os
import sqlite3
import sys


def fix_dividend_yield(db_path: str = "stock_data.db"):
    """配当利回りデータを修正"""
    
    if not os.path.exists(db_path):
        print(f"データベースファイル {db_path} が見つかりません。")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("配当利回りデータを修正しています...")
    
    try:
        # 1より大きい配当利回り値を100で割る
        cursor.execute("""
            UPDATE financial_data 
            SET dividend_yield = dividend_yield / 100.0
            WHERE dividend_yield > 1
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ {affected_rows} レコードの配当利回りを修正しました。")
        
        # 修正後の統計を表示
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(dividend_yield) as non_null_records,
                MIN(dividend_yield) as min_yield,
                MAX(dividend_yield) as max_yield,
                AVG(dividend_yield) as avg_yield
            FROM financial_data
            WHERE dividend_yield IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        print("\n修正後の統計:")
        print(f"総レコード数: {stats[0]}")
        print(f"非NULL数: {stats[1]}")
        print(f"最小値: {stats[2]:.6f} ({stats[2]*100:.2f}%)")
        print(f"最大値: {stats[3]:.6f} ({stats[3]*100:.2f}%)")
        print(f"平均値: {stats[4]:.6f} ({stats[4]*100:.2f}%)")
        
        # 修正後の高配当利回り銘柄を確認
        cursor.execute("""
            SELECT 
                c.symbol, 
                c.company_name, 
                f.dividend_yield
            FROM company_info c
            JOIN financial_data f ON c.symbol = f.symbol
            WHERE f.dividend_yield > 0.05  -- 5%以上
            ORDER BY f.dividend_yield DESC
            LIMIT 10
        """)
        
        high_yield_stocks = cursor.fetchall()
        
        print("\n修正後の高配当利回り銘柄（5%以上）:")
        print("-" * 60)
        for symbol, company_name, dividend_yield in high_yield_stocks:
            dividend_pct = dividend_yield * 100
            print(f"{symbol:<6} {company_name[:30]:<30} {dividend_pct:>7.2f}%")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_dividend_yield()