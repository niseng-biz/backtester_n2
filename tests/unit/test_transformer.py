"""
Unit tests for data transformation functionality.
"""
import unittest
from datetime import datetime

import pandas as pd

from stock_database.models import DataTransformer, StockData


class TestDataTransformer(unittest.TestCase):
    """Test DataTransformer class."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample DataFrame similar to Yahoo Finance output
        dates = pd.date_range('2024-01-01', periods=60, freq='D')
        self.sample_df = pd.DataFrame({
            'Open': [150.0 + i * 0.5 for i in range(60)],
            'High': [155.0 + i * 0.5 for i in range(60)],
            'Low': [149.0 + i * 0.5 for i in range(60)],
            'Close': [154.0 + i * 0.5 for i in range(60)],
            'Volume': [1000000 + i * 1000 for i in range(60)],
            'Adj Close': [154.0 + i * 0.5 for i in range(60)]
        }, index=dates)
        
        # Create sample financial data dictionary
        self.sample_financial_dict = {
            'symbol': 'AAPL',
            'info': {
                'trailingPE': 25.0,
                'priceToBook': 3.5,
                'returnOnEquity': 0.167,
                'returnOnAssets': 0.071,
                'debtToEquity': 1.33,
                'currentRatio': 1.2,
                'trailingEps': 6.15,
                'sharesOutstanding': 4000000000
            },
            'financials': pd.DataFrame({
                pd.Timestamp('2023-12-31'): {
                    'Total Revenue': 100000000000,
                    'Gross Profit': 40000000000,
                    'Operating Income': 30000000000,
                    'Net Income': 25000000000
                },
                pd.Timestamp('2022-12-31'): {
                    'Total Revenue': 95000000000,
                    'Gross Profit': 38000000000,
                    'Operating Income': 28000000000,
                    'Net Income': 23000000000
                }
            }).T,
            'balance_sheet': pd.DataFrame({
                pd.Timestamp('2023-12-31'): {
                    'Total Assets': 350000000000,
                    'Total Liab': 200000000000,
                    'Total Stockholder Equity': 150000000000
                }
            }).T,
            'cash_flow': pd.DataFrame({
                pd.Timestamp('2023-12-31'): {
                    'Total Cash From Operating Activities': 28000000000,
                    'Free Cash Flow': 25000000000
                }
            }).T
        }
        
        # Create sample company info dictionary
        self.sample_company_dict = {
            'symbol': 'AAPL',
            'info': {
                'longName': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'marketCap': 3000000000000,
                'country': 'United States',
                'currency': 'USD',
                'exchange': 'NASDAQ'
            }
        }
    
    def test_transform_stock_data(self):
        """Test stock data transformation."""
        result = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        self.assertEqual(len(result), 60)
        self.assertIsInstance(result[0], StockData)
        self.assertEqual(result[0].symbol, 'AAPL')
        self.assertEqual(result[0].open, 150.0)
        self.assertEqual(result[0].high, 155.0)
        self.assertEqual(result[0].low, 149.0)
        self.assertEqual(result[0].close, 154.0)
        self.assertEqual(result[0].volume, 1000000)
    
    def test_transform_stock_data_missing_columns(self):
        """Test stock data transformation with missing columns."""
        incomplete_df = self.sample_df.drop(columns=['Volume'])
        
        with self.assertRaises(ValueError) as context:
            DataTransformer.transform_stock_data(incomplete_df, 'AAPL')
        
        self.assertIn("Missing required columns", str(context.exception))
    
    def test_transform_financial_data(self):
        """Test financial data transformation."""
        result = DataTransformer.transform_financial_data(self.sample_financial_dict)
        
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0].symbol, 'AAPL')
        self.assertEqual(result[0].fiscal_year, 2023)
        self.assertEqual(result[0].revenue, 100000000000)
        self.assertEqual(result[0].net_income, 25000000000)
    
    def test_transform_financial_data_missing_symbol(self):
        """Test financial data transformation with missing symbol."""
        invalid_dict = self.sample_financial_dict.copy()
        del invalid_dict['symbol']
        
        with self.assertRaises(ValueError) as context:
            DataTransformer.transform_financial_data(invalid_dict)
        
        self.assertIn("Symbol is required", str(context.exception))
    
    def test_transform_company_info(self):
        """Test company info transformation."""
        result = DataTransformer.transform_company_info(self.sample_company_dict)
        
        self.assertEqual(result.symbol, 'AAPL')
        self.assertEqual(result.company_name, 'Apple Inc.')
        self.assertEqual(result.sector, 'Technology')
        self.assertEqual(result.industry, 'Consumer Electronics')
        self.assertEqual(result.market_cap, 3000000000000)
        self.assertEqual(result.country, 'United States')
        self.assertEqual(result.currency, 'USD')
        self.assertEqual(result.exchange, 'NASDAQ')
    
    def test_transform_company_info_missing_symbol(self):
        """Test company info transformation with missing symbol."""
        invalid_dict = self.sample_company_dict.copy()
        del invalid_dict['symbol']
        
        with self.assertRaises(ValueError) as context:
            DataTransformer.transform_company_info(invalid_dict)
        
        self.assertIn("Symbol is required", str(context.exception))
    
    def test_enrich_with_technical_indicators(self):
        """Test technical indicators enrichment."""
        # Create stock data list
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Enrich with technical indicators
        enriched_data = DataTransformer.enrich_with_technical_indicators(stock_data_list)
        
        self.assertEqual(len(enriched_data), 60)
        
        # Check that SMA values are calculated for later data points
        # SMA_20 should be available from index 19 onwards
        self.assertIsNotNone(enriched_data[19].sma_20)
        self.assertIsNotNone(enriched_data[49].sma_50)
        
        # Check that RSI values are calculated
        self.assertIsNotNone(enriched_data[14].rsi)
        self.assertTrue(0 <= enriched_data[14].rsi <= 100)
    
    def test_enrich_with_technical_indicators_insufficient_data(self):
        """Test technical indicators with insufficient data."""
        # Create small dataset
        small_df = self.sample_df.head(10)
        stock_data_list = DataTransformer.transform_stock_data(small_df, 'AAPL')
        
        # Should return original data without indicators
        enriched_data = DataTransformer.enrich_with_technical_indicators(stock_data_list)
        
        self.assertEqual(len(enriched_data), 10)
        # No technical indicators should be calculated
        for data in enriched_data:
            self.assertIsNone(data.sma_20)
            self.assertIsNone(data.sma_50)
            self.assertIsNone(data.rsi)
    
    def test_calculate_sma(self):
        """Test SMA calculation."""
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Calculate 20-day SMA
        DataTransformer._calculate_sma(stock_data_list, 20)
        
        # Check that SMA is calculated correctly
        self.assertIsNotNone(stock_data_list[19].sma_20)
        
        # Manually calculate expected SMA for verification
        expected_sma = sum([stock_data_list[i].close for i in range(0, 20)]) / 20
        self.assertAlmostEqual(stock_data_list[19].sma_20, expected_sma, places=2)
    
    def test_calculate_rsi(self):
        """Test RSI calculation."""
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Calculate RSI
        DataTransformer._calculate_rsi(stock_data_list, 14)
        
        # Check that RSI is calculated and within valid range
        self.assertIsNotNone(stock_data_list[14].rsi)
        self.assertTrue(0 <= stock_data_list[14].rsi <= 100)
    
    def test_batch_transform_stock_data(self):
        """Test batch transformation of stock data."""
        data_dict = {
            'AAPL': self.sample_df,
            'GOOGL': self.sample_df.copy()  # Use same data for simplicity
        }
        
        result = DataTransformer.batch_transform_stock_data(data_dict)
        
        self.assertEqual(len(result), 2)
        self.assertIn('AAPL', result)
        self.assertIn('GOOGL', result)
        self.assertEqual(len(result['AAPL']), 60)
        self.assertEqual(len(result['GOOGL']), 60)
        
        # Check that technical indicators are calculated
        self.assertIsNotNone(result['AAPL'][19].sma_20)
        self.assertIsNotNone(result['GOOGL'][19].sma_20)
    
    def test_detect_and_handle_anomalies(self):
        """Test anomaly detection and handling."""
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Add an anomalous data point
        anomalous_data = StockData(
            symbol='AAPL',
            date=datetime(2024, 3, 1),
            open=150.0,
            high=149.0,  # High less than open - OHLC inconsistency
            low=149.0,
            close=154.0,
            volume=1000000,
            adjusted_close=154.0
        )
        stock_data_list.append(anomalous_data)
        
        # Detect and handle anomalies
        filtered_data, anomalies = DataTransformer.detect_and_handle_anomalies(
            stock_data_list, handle_anomalies=True
        )
        
        self.assertGreater(len(anomalies), 0)
        # Should filter out the anomalous data point if it's severe
        self.assertLessEqual(len(filtered_data), len(stock_data_list))
    
    def test_safe_get_financial_value(self):
        """Test safe financial value extraction."""
        df = pd.DataFrame({
            'col1': [100, 200],
            'col2': [300, 400]
        }, index=['row1', 'row2'])
        
        # Valid extraction
        value = DataTransformer._safe_get_financial_value(df, 'col1', 'row1')
        self.assertEqual(value, 100.0)
        
        # Invalid index
        value = DataTransformer._safe_get_financial_value(df, 'col1', 'invalid_row')
        self.assertIsNone(value)
        
        # Invalid column
        value = DataTransformer._safe_get_financial_value(df, 'invalid_col', 'row1')
        self.assertIsNone(value)
        
        # Empty DataFrame
        empty_df = pd.DataFrame()
        value = DataTransformer._safe_get_financial_value(empty_df, 'col1', 'row1')
        self.assertIsNone(value)


    def test_calculate_technical_indicators(self):
        """Test additional technical indicators calculation."""
        # Create stock data list with enough data points
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Calculate additional technical indicators
        enriched_data = DataTransformer.calculate_technical_indicators(stock_data_list)
        
        self.assertEqual(len(enriched_data), 60)
        
        # Check that Bollinger Bands are calculated for later data points
        self.assertIsNotNone(enriched_data[19].bb_upper)
        self.assertIsNotNone(enriched_data[19].bb_middle)
        self.assertIsNotNone(enriched_data[19].bb_lower)
        
        # Check Bollinger Bands ordering
        self.assertLessEqual(enriched_data[19].bb_lower, enriched_data[19].bb_middle)
        self.assertLessEqual(enriched_data[19].bb_middle, enriched_data[19].bb_upper)
        
        # Check that Stochastic %K is calculated and within valid range
        self.assertIsNotNone(enriched_data[19].stoch_k)
        self.assertTrue(0 <= enriched_data[19].stoch_k <= 100)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Calculate Bollinger Bands
        DataTransformer._calculate_bollinger_bands(stock_data_list, 20, 2)
        
        # Check that Bollinger Bands are calculated correctly
        self.assertIsNotNone(stock_data_list[19].bb_upper)
        self.assertIsNotNone(stock_data_list[19].bb_middle)
        self.assertIsNotNone(stock_data_list[19].bb_lower)
        
        # Verify ordering
        self.assertLessEqual(stock_data_list[19].bb_lower, stock_data_list[19].bb_middle)
        self.assertLessEqual(stock_data_list[19].bb_middle, stock_data_list[19].bb_upper)
    
    def test_calculate_ema(self):
        """Test EMA calculation."""
        prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ema_values = DataTransformer._calculate_ema(prices, 5)
        
        # Check that EMA values are calculated
        self.assertEqual(len(ema_values), 10)
        self.assertIsNotNone(ema_values[4])  # First EMA value at index 4
        
        # EMA should be different from SMA after the first calculation
        sma = sum(prices[:5]) / 5
        self.assertEqual(ema_values[4], sma)  # First value should be SMA
        
        # Check that EMA is calculated (should be different from simple average)
        self.assertIsNotNone(ema_values[5])
        self.assertTrue(isinstance(ema_values[5], float))
    
    def test_calculate_stochastic(self):
        """Test Stochastic Oscillator calculation."""
        stock_data_list = DataTransformer.transform_stock_data(self.sample_df, 'AAPL')
        
        # Calculate Stochastic
        DataTransformer._calculate_stochastic(stock_data_list, 14)
        
        # Check that Stochastic %K is calculated and within valid range
        self.assertIsNotNone(stock_data_list[13].stoch_k)
        self.assertTrue(0 <= stock_data_list[13].stoch_k <= 100)
if __name__ == '__main__':
    unittest.main()