"""
Data transformation utilities for converting curl_cffi Yahoo Finance data to internal models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .company_info import CompanyInfo
from .financial_data import FinancialData
from .stock_data import StockData


class CurlDataTransformer:
    """
    Transforms Yahoo Finance data from curl_cffi client into internal data models.
    """
    
    @staticmethod
    def transform_financial_data_curl(financial_dict: Dict[str, Any]) -> List[FinancialData]:
        """
        Transform financial data dictionary from curl_cffi Yahoo Finance client to list of FinancialData objects.
        
        Args:
            financial_dict: Dictionary containing financial data from Yahoo Finance curl client
            
        Returns:
            List[FinancialData]: List of validated FinancialData objects
        """
        financial_data_list = []
        symbol = financial_dict.get('symbol', '').upper()
        
        if not symbol:
            raise ValueError("Symbol is required in financial_dict")
        
        # Extract data from different sections
        income_statements = financial_dict.get('income_statements', {}).get('incomeStatementHistory', [])
        balance_sheets = financial_dict.get('balance_sheets', {}).get('balanceSheetHistory', [])
        cash_flows = financial_dict.get('cash_flows', {}).get('cashFlowStatementHistory', [])
        key_stats = financial_dict.get('key_statistics', {})
        financial_data = financial_dict.get('financial_data', {})
        
        # Process annual data from income statements
        for statement in income_statements:
            try:
                # Extract fiscal year from endDate
                end_date = statement.get('endDate', {})
                if isinstance(end_date, dict) and 'raw' in end_date:
                    fiscal_year = datetime.fromtimestamp(end_date['raw']).year
                else:
                    continue
                
                # Find corresponding balance sheet and cash flow data
                balance_sheet = CurlDataTransformer._find_matching_statement(balance_sheets, end_date)
                cash_flow = CurlDataTransformer._find_matching_statement(cash_flows, end_date)
                
                financial_obj = FinancialData(
                    symbol=symbol,
                    fiscal_year=fiscal_year,
                    # Income statement data
                    revenue=CurlDataTransformer._safe_get_value(statement, 'totalRevenue'),
                    gross_profit=CurlDataTransformer._safe_get_value(statement, 'grossProfit'),
                    operating_income=CurlDataTransformer._safe_get_value(statement, 'operatingIncome'),
                    net_income=CurlDataTransformer._safe_get_value(statement, 'netIncome'),
                    # Balance sheet data
                    total_assets=CurlDataTransformer._safe_get_value(balance_sheet, 'totalAssets') if balance_sheet else None,
                    total_liabilities=CurlDataTransformer._safe_get_value(balance_sheet, 'totalLiab') if balance_sheet else None,
                    shareholders_equity=CurlDataTransformer._safe_get_value(balance_sheet, 'totalStockholderEquity') if balance_sheet else None,
                    # Cash flow data
                    operating_cash_flow=CurlDataTransformer._safe_get_value(cash_flow, 'totalCashFromOperatingActivities') if cash_flow else None,
                    free_cash_flow=CurlDataTransformer._safe_get_value(cash_flow, 'freeCashFlow') if cash_flow else None,
                    # Key statistics (current year only)
                    eps=CurlDataTransformer._safe_get_value(key_stats, 'trailingEps') if fiscal_year == datetime.now().year else None,
                    per=CurlDataTransformer._safe_get_value(key_stats, 'trailingPE') if fiscal_year == datetime.now().year else None,
                    pbr=CurlDataTransformer._safe_get_value(key_stats, 'priceToBook') if fiscal_year == datetime.now().year else None,
                    # Financial ratios from financial_data
                    roe=CurlDataTransformer._safe_get_value(financial_data, 'returnOnEquity') if fiscal_year == datetime.now().year else None,
                    roa=CurlDataTransformer._safe_get_value(financial_data, 'returnOnAssets') if fiscal_year == datetime.now().year else None,
                    debt_to_equity=CurlDataTransformer._safe_get_value(financial_data, 'debtToEquity') if fiscal_year == datetime.now().year else None,
                    current_ratio=CurlDataTransformer._safe_get_value(financial_data, 'currentRatio') if fiscal_year == datetime.now().year else None
                )
                
                # Calculate additional ratios if we have the data
                if financial_obj.net_income and financial_obj.shareholders_equity:
                    financial_obj.roe = financial_obj.net_income / financial_obj.shareholders_equity
                
                if financial_obj.net_income and financial_obj.total_assets:
                    financial_obj.roa = financial_obj.net_income / financial_obj.total_assets
                
                # Validate the data using built-in validation
                if financial_obj.validate():
                    financial_data_list.append(financial_obj)
                else:
                    print(f"Warning: Invalid financial data for {symbol} year {fiscal_year}")
                    
            except Exception as e:
                print(f"Error transforming financial data for {symbol}: {e}")
        
        return financial_data_list
    
    @staticmethod
    def transform_company_info_curl(company_dict: Dict[str, Any]) -> CompanyInfo:
        """
        Transform company info dictionary from curl_cffi Yahoo Finance client to CompanyInfo object.
        
        Args:
            company_dict: Dictionary containing company info from Yahoo Finance curl client
            
        Returns:
            CompanyInfo: Validated CompanyInfo object
        """
        symbol = company_dict.get('symbol', '').upper()
        
        if not symbol:
            raise ValueError("Symbol is required in company_dict")
        
        profile = company_dict.get('profile', {})
        price = company_dict.get('price', {})
        statistics = company_dict.get('statistics', {})
        
        company_info = CompanyInfo(
            symbol=symbol,
            company_name=profile.get('longName') or price.get('longName') or symbol,
            sector=profile.get('sector'),
            industry=profile.get('industry'),
            market_cap=CurlDataTransformer._safe_get_value(price, 'marketCap') or CurlDataTransformer._safe_get_value(statistics, 'marketCap'),
            country=profile.get('country'),
            currency=price.get('currency'),
            exchange=price.get('exchangeName')
        )
        
        # Validate the data using built-in validation
        if not company_info.validate():
            print(f"Warning: Invalid company info for {symbol}")
        
        return company_info
    
    @staticmethod
    def _find_matching_statement(statements: List[Dict], target_end_date: Dict) -> Optional[Dict]:
        """
        Find a financial statement that matches the target end date.
        
        Args:
            statements: List of financial statements
            target_end_date: Target end date to match
            
        Returns:
            Optional[Dict]: Matching statement or None
        """
        if not statements or not target_end_date:
            return None
        
        target_timestamp = target_end_date.get('raw')
        if not target_timestamp:
            return None
        
        for statement in statements:
            end_date = statement.get('endDate', {})
            if isinstance(end_date, dict) and end_date.get('raw') == target_timestamp:
                return statement
        
        return None
    
    @staticmethod
    def _safe_get_value(data: Optional[Dict], key: str) -> Optional[float]:
        """
        Safely get a numeric value from Yahoo Finance data structure.
        
        Args:
            data: Data dictionary
            key: Key to look for
            
        Returns:
            Optional[float]: Numeric value or None if not found/invalid
        """
        if not data or key not in data:
            return None
        
        value = data[key]
        
        # Handle Yahoo Finance's nested value structure
        if isinstance(value, dict):
            if 'raw' in value:
                raw_value = value['raw']
                try:
                    return float(raw_value) if raw_value is not None else None
                except (ValueError, TypeError):
                    return None
            elif 'fmt' in value:
                # Try to parse formatted value
                fmt_value = value['fmt']
                if isinstance(fmt_value, str):
                    # Remove common formatting characters
                    clean_value = fmt_value.replace(',', '').replace('%', '').replace('$', '')
                    try:
                        return float(clean_value)
                    except (ValueError, TypeError):
                        return None
        
        # Handle direct numeric values
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def batch_transform_financial_data_curl(data_dict: Dict[str, Dict[str, Any]]) -> Dict[str, List[FinancialData]]:
        """
        Transform multiple symbols' financial data in batch.
        
        Args:
            data_dict: Dictionary mapping symbols to their financial data dictionaries
            
        Returns:
            Dict[str, List[FinancialData]]: Dictionary mapping symbols to their FinancialData lists
        """
        results = {}
        
        for symbol, financial_dict in data_dict.items():
            try:
                financial_data_list = CurlDataTransformer.transform_financial_data_curl(financial_dict)
                results[symbol] = financial_data_list
            except Exception as e:
                print(f"Error transforming financial data for {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    @staticmethod
    def batch_transform_company_info_curl(data_dict: Dict[str, Dict[str, Any]]) -> Dict[str, CompanyInfo]:
        """
        Transform multiple symbols' company info in batch.
        
        Args:
            data_dict: Dictionary mapping symbols to their company info dictionaries
            
        Returns:
            Dict[str, CompanyInfo]: Dictionary mapping symbols to their CompanyInfo objects
        """
        results = {}
        
        for symbol, company_dict in data_dict.items():
            try:
                company_info = CurlDataTransformer.transform_company_info_curl(company_dict)
                results[symbol] = company_info
            except Exception as e:
                print(f"Error transforming company info for {symbol}: {e}")
                results[symbol] = None
        
        return results