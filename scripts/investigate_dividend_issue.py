#!/usr/bin/env python3
"""
配当利回りの問題をさらに詳しく調査するスクリプト
"""

import sqlite3

import pandas as pd
import yfinance as yf


def investigate_dividend_issue():
    """配当利回りの問題を調査"""
    
    # いくつかの銘柄でyfinanceから直接データを取得して比較
    test_symbols = ['AAPL', 'MSFT', 'WBA', 'AMAT', 'VZ']
    
    print("yfinanceから直接取得したデータ:")
    print("=" * 80)
    
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            dividend_yield = info.get('dividendYield')
            dividend_rate = info.get('dividendRate')
            current_price = info.get('currentPrice')
            
            print(f"\n{symbol}:")
            print(f"  dividendYield (raw): {dividend_yield}")
            print(f"  dividendRate: {dividend_rate}")
            print(f"  currentPrice: {current_price}")
            
            # 手動で配当利回りを計算
            if dividend_rate and current_price:
                calculated_yield = dividend_rate / current_price
                print(f"  calculated yield: {calculated_yield:.6f} ({calculated_yield*100:.2f}%)")
            
            # データベースの値と比較
            conn = sqlite3.connect("stock_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT dividend_yield, dividend_rate, current_price FROM financial_data WHERE symbol = ?", (symbol,))
            db_data = cursor.fetchone()
            conn.close()
            
            if db_data:
                print(f"  DB dividend_yield: {db_data[0]}")
                print(f"  DB dividend_rate: {db_data[1]}")
                print(f"  DB current_price: {db_data[2]}")
            
        except Exception as e:
            print(f"Error for {symbol}: {e}")

if __name__ == "__main__":
    investigate_dividend_issue()