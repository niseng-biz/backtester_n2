#!/usr/bin/env python3
"""
完全なシンボル取得テスト
"""

import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source

def test_full_fetch():
    """完全なシンボル取得テスト"""
    print("🚀 完全なシンボル取得テスト")
    print("=" * 50)
    
    source = SP500Nasdaq100Source()
    
    # 制限なしで全銘柄を取得
    print("📊 全銘柄を取得中...")
    symbols = source.fetch_symbols()
    
    print(f"✅ 取得した総銘柄数: {len(symbols)}")
    
    # セクター別集計
    sectors = {}
    exchanges = {}
    
    for symbol in symbols:
        sector = symbol.sector or "Unknown"
        sectors[sector] = sectors.get(sector, 0) + 1
        
        exchange = symbol.exchange or "Unknown"
        exchanges[exchange] = exchanges.get(exchange, 0) + 1
    
    print(f"\n📊 セクター別銘柄数:")
    for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
        print(f"  {sector}: {count}")
    
    print(f"\n📊 取引所別銘柄数:")
    for exchange, count in sorted(exchanges.items(), key=lambda x: x[1], reverse=True):
        print(f"  {exchange}: {count}")
    
    # 最初の20銘柄を表示
    print(f"\n📋 最初の20銘柄:")
    for i, symbol in enumerate(symbols[:20]):
        print(f"  {i+1:2d}. {symbol.symbol:6s} - {symbol.company_name[:40]:40s} ({symbol.sector})")
    
    # 制限付きテスト
    print(f"\n📊 制限付きテスト (limit=600):")
    limited_symbols = source.fetch_symbols(limit=600)
    print(f"✅ 制限付き取得銘柄数: {len(limited_symbols)}")
    
    return len(symbols)

if __name__ == "__main__":
    total_symbols = test_full_fetch()
    
    if total_symbols > 500:
        print(f"\n🎉 成功！{total_symbols}銘柄を取得しました。")
        print("これで example_dashboard_advanced_stock_dashboard.py で")
        print("600銘柄程度のデータが利用できるようになります。")
    else:
        print(f"\n⚠️  取得銘柄数が少ないです: {total_symbols}")
        print("lxmlライブラリが正しくインストールされているか確認してください。")