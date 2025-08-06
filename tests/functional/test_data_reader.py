#!/usr/bin/env python3
"""
Test script for data reader functionality
"""

import os
import sys
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backtester import CryptoDataReader

def test_data_reader():
    """Test the data reader functionality"""
    print("🧪 Testing Data Reader Functionality")
    print("=" * 50)
    
    # Test CryptoDataReader
    data_reader = CryptoDataReader()
    data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'pricedata', 'BITFLYER_BTCJPY_1D_c51ab.csv')
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return False
    
    try:
        print(f"📈 Loading data from: {data_file}")
        market_data = data_reader.load_data(data_file)
        
        print(f"✅ Successfully loaded {len(market_data)} data points")
        
        # Display first few data points
        print("\n📊 First 5 data points:")
        for i, data in enumerate(market_data[:5]):
            print(f"  {i+1}. {data.timestamp}: O={data.open}, H={data.high}, L={data.low}, C={data.close}, V={data.volume}")
        
        # Display last few data points
        print("\n📊 Last 5 data points:")
        for i, data in enumerate(market_data[-5:]):
            print(f"  {len(market_data)-4+i}. {data.timestamp}: O={data.open}, H={data.high}, L={data.low}, C={data.close}, V={data.volume}")
        
        # Validate data integrity
        print("\n🔍 Data validation:")
        print(f"  - Date range: {market_data[0].timestamp} to {market_data[-1].timestamp}")
        print(f"  - All prices positive: {all(d.open > 0 and d.high > 0 and d.low > 0 and d.close > 0 for d in market_data)}")
        print(f"  - High >= Low: {all(d.high >= d.low for d in market_data)}")
        print(f"  - Volume non-negative: {all(d.volume >= 0 for d in market_data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data reader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_reader()
    if success:
        print("\n✅ Data reader functionality test PASSED")
    else:
        print("\n❌ Data reader functionality test FAILED")
        sys.exit(1)