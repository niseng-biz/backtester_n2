"""
yfinanceから実際に取得できるフィールドを確認するスクリプト
"""

import json
from pprint import pprint

import yfinance as yf


def check_company_info_fields():
    """Company infoで取得できるフィールドを確認"""
    print("=== Company Info Fields ===")
    
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        print("Available fields in ticker.info:")
        print(f"Total fields: {len(info)}")
        
        # 主要なフィールドを抽出
        company_fields = {}
        for key, value in info.items():
            if any(keyword in key.lower() for keyword in [
                'name', 'sector', 'industry', 'market', 'cap', 'country', 
                'currency', 'exchange', 'website', 'business', 'summary',
                'employees', 'city', 'state', 'zip', 'phone', 'address'
            ]):
                company_fields[key] = value
        
        print("\nCompany-related fields:")
        for key, value in sorted(company_fields.items()):
            print(f"  {key}: {value}")
            
        return company_fields
        
    except Exception as e:
        print(f"Error: {e}")
        return {}

def check_financial_data_fields():
    """Financial dataで取得できるフィールドを確認"""
    print("\n=== Financial Data Fields ===")
    
    try:
        ticker = yf.Ticker("AAPL")
        
        # Quarterly financials
        print("\nQuarterly Financials:")
        quarterly = ticker.quarterly_financials
        if not quarterly.empty:
            print("Available quarterly financial metrics:")
            for index in quarterly.index:
                print(f"  {index}")
        
        # Annual financials
        print("\nAnnual Financials:")
        annual = ticker.financials
        if not annual.empty:
            print("Available annual financial metrics:")
            for index in annual.index:
                print(f"  {index}")
        
        # Balance sheet
        print("\nBalance Sheet:")
        balance_sheet = ticker.balance_sheet
        if not balance_sheet.empty:
            print("Available balance sheet metrics:")
            for index in balance_sheet.index:
                print(f"  {index}")
        
        # Cash flow
        print("\nCash Flow:")
        cashflow = ticker.cashflow
        if not cashflow.empty:
            print("Available cash flow metrics:")
            for index in cashflow.index:
                print(f"  {index}")
        
        # Key financial ratios from info
        info = ticker.info
        financial_ratios = {}
        for key, value in info.items():
            if any(keyword in key.lower() for keyword in [
                'ratio', 'margin', 'return', 'yield', 'eps', 'pe', 'pb', 
                'revenue', 'profit', 'income', 'earnings', 'debt', 'equity'
            ]):
                financial_ratios[key] = value
        
        print("\nFinancial ratios from info:")
        for key, value in sorted(financial_ratios.items()):
            print(f"  {key}: {value}")
            
        return {
            'quarterly': quarterly.index.tolist() if not quarterly.empty else [],
            'annual': annual.index.tolist() if not annual.empty else [],
            'balance_sheet': balance_sheet.index.tolist() if not balance_sheet.empty else [],
            'cashflow': cashflow.index.tolist() if not cashflow.empty else [],
            'ratios': financial_ratios
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {}

def main():
    print("Checking yfinance available fields...")
    
    company_fields = check_company_info_fields()
    financial_fields = check_financial_data_fields()
    
    # Save to JSON for reference
    with open('yfinance_fields.json', 'w') as f:
        json.dump({
            'company_fields': company_fields,
            'financial_fields': financial_fields
        }, f, indent=2, default=str)
    
    print(f"\nResults saved to yfinance_fields.json")

if __name__ == "__main__":
    main()