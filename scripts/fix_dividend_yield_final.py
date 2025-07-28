#!/usr/bin/env python3
"""
配当利回りデータを最終的に正しく修正するスクリプト
yfinanceのdividendYieldは既にパーセンテージ形式（6.29 = 6.29%）
これを小数形式（0.0629）に変換する必要がある
"""

import os
import sqlite3
import sys


def fix_dividend_yield_final(db_path: str = "stock_data.db"):
    """配当利回りデータを最終的に修正"""
    
    if not os.path.exists(db_path):
        print(f"データベースファイル {db_path} が見つかりません。")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("配当利回りデータを最終修正しています...")
    
    try:
        # 現在のデータを確認
        cursor.execute("""
            SELECT symbol, dividend_yield, dividend_rate, current_price
            FROM financial_data 
            WHERE dividend_yield IS NOT NULL 
            ORDER BY dividend_yield DESC 
            LIMIT 5
        """)
        
        current_data = cursor.fetchall()
        print("修正前のサンプルデータ:")
        for symbol, div_yield, div_rate, price in current_data:
            print(f"  {symbol}: yield={div_yield}, rate={div_rate}, price={price}")
        
        # データベースを元の状態に戻してから正しく修正
        # まず、元のyfinanceデータを再取得するか、手動で修正
        
        # 現在の値が0.01未満の場合は、既に2回100で割られているので、10000倍する
        cursor.execute("""
            UPDATE financial_data 
            SET dividend_yield = dividend_yield * 10000.0
            WHERE dividend_yield < 0.01 AND dividend_yield IS NOT NULL
        """)
        
        # 次に、正しく100で割る
        cursor.execute("""
            UPDATE financial_data 
            SET dividend_yield = dividend_yield / 100.0
            WHERE dividend_yield IS NOT NULL
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ 配当利回りデータを修正しました。")
        
        # 修正後のデータを確認
        cursor.execute("""
            SELECT symbol, dividend_yield, dividend_rate, current_price
            FROM financial_data 
            WHERE dividend_yield IS NOT NULL 
            ORDER BY dividend_yield DESC 
            LIMIT 10
        """)
        
        fixed_data = cursor.fetchall()
        print("\n修正後のサンプルデータ:")
        for symbol, div_yield, div_rate, price in fixed_data:
            div_pct = div_yield * 100 if div_yield else 0
            print(f"  {symbol}: {div_pct:.2f}% (yield={div_yield:.6f}, rate={div_rate}, price={price})")
        
        # 統計を表示
        cursor.execute("""
            SELECT 
                COUNT(dividend_yield) as count,
                MIN(dividend_yield) as min_yield,
                MAX(dividend_yield) as max_yield,
                AVG(dividend_yield) as avg_yield
            FROM financial_data
            WHERE dividend_yield IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        print(f"\n統計:")
        print(f"レコード数: {stats[0]}")
        print(f"最小値: {stats[1]:.6f} ({stats[1]*100:.2f}%)")
        print(f"最大値: {stats[2]:.6f} ({stats[2]*100:.2f}%)")
        print(f"平均値: {stats[3]:.6f} ({stats[3]*100:.2f}%)")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_dividend_yield_final()