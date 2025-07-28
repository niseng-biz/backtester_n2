"""
Unit tests for the CurlDataTransformer class.
"""

import unittest
from datetime import datetime

from stock_database.models.company_info import CompanyInfo
from stock_database.models.curl_transformer import CurlDataTransformer
from stock_database.models.financial_data import FinancialData


class TestCurlDataTransformer(unittest.TestCase):
    """Test cases for CurlDataTransformer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transformer = CurlDataTransformer()
    
    def test_safe_get_value_with_raw(self):
        """Test _safe_get_value with raw value structure."""
        data = {
            'revenue': {'raw': 1000000000, 'fmt': '1.00B'}
        }
        
        result = CurlDataTransformer._safe_get_value(data, 'revenue')
        self.assertEqual(result, 1000000000.0)
    
    def test_safe_get_value_with_fmt(self):
        """Test _safe_get_value with formatted value."""
        data = {
            'percentage': {'fmt': '15.5%'}
        }
        
        result = CurlDataTransformer._safe_get_value(data, 'percentage')
        self.assertEqual(result, 15.5)
    
    def test_safe_get_value_with_direct_number(self):
        """Test _safe_get_value with direct numeric value."""
        data = {
            'simple_value': 123.45
        }
        
        result = CurlDataTransformer._safe_get_value(data, 'simple_value')
        self.assertEqual(result, 123.45)
    
    def test_safe_get_value_missing_key(self):
        """Test _safe_get_value with missing key."""
        data = {'other_key': 123}
        
        result = CurlDataTransformer._safe_get_value(data, 'missing_key')
        self.assertIsNone(result)
    
    def test_safe_get_value_none_data(self):
        """Test _safe_get_value with None data."""
        result = CurlDataTransformer._safe_get_value(None, 'any_key')
        self.assertIsNone(result)
    
    def test_find_matching_statement(self):
        """Test _find_matching_statement functionality."""
        statements = [
            {'endDate': {'raw': 1640995200}},  # 2022-01-01
            {'endDate': {'raw': 1672531200}}   # 2023-01-01
        ]
        
        target_end_date = {'raw': 1640995200}
        
        result = CurlDataTransformer._find_matching_statement(statements, target_end_date)
        self.assertIsNotNone(result)
        self.assertEqual(result['endDate']['raw'], 1640995200)
    
    def test_find_matching_statement_no_match(self):
        """Test _find_matching_statement with no matching statement."""
        statements = [
            {'endDate': {'raw': 1640995200}}
        ]
        
        target_end_date = {'raw': 1672531200}  # Different date
        
        result = CurlDataTransformer._find_matching_statement(statements, target_end_date)
        self.assertIsNone(result)
    
    def test_transform_financial_data_curl(self):
        """Test financial data transformation from curl client."""
        financial_dict = {
            'symbol': 'AAPL',
            'income_statements': {
                'incomeStatementHistory': [{
                    'endDate': {'raw': 1640995200},  # 2022-01-01
                    'totalRevenue': {'raw': 1000000000},
                    'grossProfit': {'raw': 400000000},
                    'operatingIncome': {'raw': 300000000},
                    'netIncome': {'raw': 200000000}
                }]
            },
            'balance_sheets': {
                'balanceSheetHistory': [{
                    'endDate': {'raw': 1640995200},
                    'totalAssets': {'raw': 5000000000},
                    'totalLiab': {'raw': 2000000000},
                    'totalStockholderEquity': {'raw': 3000000000}
                }]
            },
            'cash_flows': {
                'cashFlowStatementHistory': [{
                    'endDate': {'raw': 1640995200},
                    'totalCashFromOperatingActivities': {'raw': 250000000},
                    'freeCashFlow': {'raw': 150000000}
                }]
            },
            'key_statistics': {
                'trailingEps': {'raw': 5.0},
                'trailingPE': {'raw': 25.0}
            },
            'financial_data': {
                'returnOnEquity': {'raw': 0.15},
                'returnOnAssets': {'raw': 0.08}
            }
        }
        
        result = CurlDataTransformer.transform_financial_data_curl(financial_dict)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        financial_data = result[0]
        self.assertIsInstance(financial_data, FinancialData)
        self.assertEqual(financial_data.symbol, 'AAPL')
        self.assertEqual(financial_data.fiscal_year, 2022)
        self.assertEqual(financial_data.revenue, 1000000000.0)
        self.assertEqual(financial_data.net_income, 200000000.0)
        self.assertEqual(financial_data.total_assets, 5000000000.0)
    
    def test_transform_financial_data_curl_missing_symbol(self):
        """Test financial data transformation with missing symbol."""
        financial_dict = {
            'income_statements': {'incomeStatementHistory': []}
        }
        
        with self.assertRaises(ValueError):
            CurlDataTransformer.transform_financial_data_curl(financial_dict)
    
    def test_transform_company_info_curl(self):
        """Test company info transformation from curl client."""
        company_dict = {
            'symbol': 'AAPL',
            'profile': {
                'longName': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'country': 'United States'
            },
            'price': {
                'marketCap': {'raw': 3000000000000},
                'currency': 'USD',
                'exchangeName': 'NASDAQ'
            },
            'statistics': {
                'marketCap': {'raw': 3000000000000}
            }
        }
        
        result = CurlDataTransformer.transform_company_info_curl(company_dict)
        
        self.assertIsInstance(result, CompanyInfo)
        self.assertEqual(result.symbol, 'AAPL')
        self.assertEqual(result.company_name, 'Apple Inc.')
        self.assertEqual(result.sector, 'Technology')
        self.assertEqual(result.industry, 'Consumer Electronics')
        self.assertEqual(result.market_cap, 3000000000000.0)
        self.assertEqual(result.country, 'United States')
        self.assertEqual(result.currency, 'USD')
        self.assertEqual(result.exchange, 'NASDAQ')
    
    def test_transform_company_info_curl_missing_symbol(self):
        """Test company info transformation with missing symbol."""
        company_dict = {
            'profile': {'longName': 'Test Company'}
        }
        
        with self.assertRaises(ValueError):
            CurlDataTransformer.transform_company_info_curl(company_dict)
    
    def test_batch_transform_financial_data_curl(self):
        """Test batch financial data transformation."""
        data_dict = {
            'AAPL': {
                'symbol': 'AAPL',
                'income_statements': {
                    'incomeStatementHistory': [{
                        'endDate': {'raw': 1640995200},
                        'totalRevenue': {'raw': 1000000000}
                    }]
                },
                'balance_sheets': {'balanceSheetHistory': []},
                'cash_flows': {'cashFlowStatementHistory': []},
                'key_statistics': {},
                'financial_data': {}
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'income_statements': {
                    'incomeStatementHistory': [{
                        'endDate': {'raw': 1640995200},
                        'totalRevenue': {'raw': 2000000000}
                    }]
                },
                'balance_sheets': {'balanceSheetHistory': []},
                'cash_flows': {'cashFlowStatementHistory': []},
                'key_statistics': {},
                'financial_data': {}
            }
        }
        
        results = CurlDataTransformer.batch_transform_financial_data_curl(data_dict)
        
        self.assertEqual(len(results), 2)
        self.assertIn('AAPL', results)
        self.assertIn('GOOGL', results)
        self.assertIsInstance(results['AAPL'], list)
        self.assertIsInstance(results['GOOGL'], list)
    
    def test_batch_transform_company_info_curl(self):
        """Test batch company info transformation."""
        data_dict = {
            'AAPL': {
                'symbol': 'AAPL',
                'profile': {'longName': 'Apple Inc.'},
                'price': {},
                'statistics': {}
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'profile': {'longName': 'Alphabet Inc.'},
                'price': {},
                'statistics': {}
            }
        }
        
        results = CurlDataTransformer.batch_transform_company_info_curl(data_dict)
        
        self.assertEqual(len(results), 2)
        self.assertIn('AAPL', results)
        self.assertIn('GOOGL', results)
        self.assertIsInstance(results['AAPL'], CompanyInfo)
        self.assertIsInstance(results['GOOGL'], CompanyInfo)
        self.assertEqual(results['AAPL'].company_name, 'Apple Inc.')
        self.assertEqual(results['GOOGL'].company_name, 'Alphabet Inc.')


if __name__ == '__main__':
    unittest.main()