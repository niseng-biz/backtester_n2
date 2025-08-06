#!/usr/bin/env python3
"""
SP500Nasdaq100Source のデバッグスクリプト
"""

import os
import sys
import pandas as pd
import requests

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source

def test_wikipedia_access():
    """Wikipediaへのアクセステスト"""
    print("🔍 Wikipediaアクセステスト")
    print("-" * 40)
    
    # S&P 500のテスト
    try:
        print("📊 S&P 500データの取得テスト...")
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        print(f"✅ S&P 500: {len(tables)}個のテーブルを取得")
        
        if tables:
            sp500_table = tables[0]
            print(f"✅ S&P 500テーブル: {len(sp500_table)}行")
            print(f"✅ カラム: {list(sp500_table.columns)}")
            print("\n最初の5行:")
            print(sp500_table.head())
        
    except Exception as e:
        print(f"❌ S&P 500取得エラー: {e}")
    
    print("\n" + "-" * 40)
    
    # NASDAQ 100のテスト
    try:
        print("📊 NASDAQ 100データの取得テスト...")
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        tables = pd.read_html(url)
        print(f"✅ NASDAQ 100: {len(tables)}個のテーブルを取得")
        
        for i, table in enumerate(tables):
            print(f"テーブル {i}: {list(table.columns)}")
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                print(f"✅ NASDAQ 100テーブル {i}: {len(table)}行")
                print("\n最初の5行:")
                print(table.head())
                break
        
    except Exception as e:
        print(f"❌ NASDAQ 100取得エラー: {e}")

def test_source_implementation():
    """SP500Nasdaq100Sourceの実装テスト"""
    print("\n🔍 SP500Nasdaq100Source実装テスト")
    print("-" * 40)
    
    source = SP500Nasdaq100Source()
    
    # 可用性チェック
    print("📡 可用性チェック...")
    is_available = source.is_available()
    print(f"✅ 可用性: {is_available}")
    
    # シンボル取得テスト
    print("\n📊 シンボル取得テスト...")
    try:
        symbols = source.fetch_symbols(limit=100)  # 最初の100個をテスト
        print(f"✅ 取得した銘柄数: {len(symbols)}")
        
        if symbols:
            print("\n最初の10銘柄:")
            for i, symbol in enumerate(symbols[:10]):
                print(f"  {i+1}. {symbol.symbol} - {symbol.company_name} ({symbol.sector})")
        
        # セクター別集計
        sectors = {}
        for symbol in symbols:
            sector = symbol.sector or "Unknown"
            sectors[sector] = sectors.get(sector, 0) + 1
        
        print(f"\nセクター別銘柄数:")
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector}: {count}")
        
    except Exception as e:
        print(f"❌ シンボル取得エラー: {e}")
        import traceback
        traceback.print_exc()

def test_individual_methods():
    """個別メソッドのテスト"""
    print("\n🔍 個別メソッドテスト")
    print("-" * 40)
    
    source = SP500Nasdaq100Source()
    
    # S&P 500のテスト
    try:
        print("📊 S&P 500メソッドテスト...")
        sp500_symbols = source._fetch_sp500_symbols()
        print(f"✅ S&P 500銘柄数: {len(sp500_symbols)}")
        
        if sp500_symbols:
            print("最初の5銘柄:")
            for symbol in sp500_symbols[:5]:
                print(f"  {symbol.symbol} - {symbol.company_name}")
    
    except Exception as e:
        print(f"❌ S&P 500メソッドエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # NASDAQ 100のテスト
    try:
        print("📊 NASDAQ 100メソッドテスト...")
        nasdaq100_symbols = source._fetch_nasdaq100_symbols()
        print(f"✅ NASDAQ 100銘柄数: {len(nasdaq100_symbols)}")
        
        if nasdaq100_symbols:
            print("最初の5銘柄:")
            for symbol in nasdaq100_symbols[:5]:
                print(f"  {symbol.symbol} - {symbol.company_name}")
    
    except Exception as e:
        print(f"❌ NASDAQ 100メソッドエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 静的リストのテスト
    try:
        print("📊 静的リストテスト...")
        static_symbols = source._get_static_symbols()
        print(f"✅ 静的リスト銘柄数: {len(static_symbols)}")
        
        if static_symbols:
            print("最初の5銘柄:")
            for symbol in static_symbols[:5]:
                print(f"  {symbol.symbol} - {symbol.company_name}")
    
    except Exception as e:
        print(f"❌ 静的リストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 SP500Nasdaq100Source デバッグ")
    print("=" * 50)
    
    # Wikipediaアクセステスト
    test_wikipedia_access()
    
    # 実装テスト
    test_source_implementation()
    
    # 個別メソッドテスト
    test_individual_methods()
    
    print("\n" + "=" * 50)
    print("✅ デバッグ完了")

if __name__ == "__main__":
    main()