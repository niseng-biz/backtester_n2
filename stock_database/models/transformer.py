"""
Data transformation utilities for converting Yahoo Finance data to internal models.
"""
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .company_info import CompanyInfo
from .financial_data import FinancialData
from .stock_data import StockData


class DataTransformer:
    """
    Transforms Yahoo Finance data into internal data models with validation and enrichment.
    """
    
    @staticmethod
    def transform_stock_data(df: pd.DataFrame, symbol: str) -> List[StockData]:
        """
        Transform pandas DataFrame from Yahoo Finance to list of StockData objects.
        
        Args:
            df: DataFrame with stock price data from Yahoo Finance
            symbol: Stock symbol
            
        Returns:
            List[StockData]: List of validated StockData objects
        """
        stock_data_list = []
        
        # Ensure DataFrame has the expected columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col.lower() not in [c.lower() for c in df.columns]]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Normalize column names to lowercase
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        for index, row in df.iterrows():
            try:
                # Extract date from index
                if hasattr(index, 'to_pydatetime'):
                    date = index.to_pydatetime()
                elif isinstance(index, datetime):
                    date = index
                else:
                    date = pd.to_datetime(index).to_pydatetime()
                
                # Create StockData object
                stock_data = StockData(
                    symbol=symbol.upper(),
                    date=date,
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=int(row.get('volume', 0)),
                    adjusted_close=float(row.get('adj_close', row.get('close', 0))),
                    dividend=float(row.get('dividends', 0)) if 'dividends' in row and pd.notna(row.get('dividends')) else None,
                    stock_split=float(row.get('stock_splits', 1)) if 'stock_splits' in row and pd.notna(row.get('stock_splits')) else None
                )
                
                # Validate the data using built-in validation
                if stock_data.validate():
                    stock_data_list.append(stock_data)
                else:
                    print(f"Warning: Invalid stock data for {symbol} on {date}")
                    
            except Exception as e:
                print(f"Error transforming data for {symbol} on {index}: {e}")
        
        return stock_data_list
    
    @staticmethod
    def transform_financial_data(financial_dict: Dict[str, Any]) -> List[FinancialData]:
        """
        Transform financial data dictionary from Yahoo Finance to list of FinancialData objects.
        
        Args:
            financial_dict: Dictionary containing financial data from Yahoo Finance
            
        Returns:
            List[FinancialData]: List of validated FinancialData objects
        """
        financial_data_list = []
        symbol = financial_dict.get('symbol', '').upper()
        
        if not symbol:
            raise ValueError("Symbol is required in financial_dict")
        
        info = financial_dict.get('info', {})
        financials = financial_dict.get('financials', pd.DataFrame())
        balance_sheet = financial_dict.get('balance_sheet', pd.DataFrame())
        cash_flow = financial_dict.get('cash_flow', pd.DataFrame())
        
        # Process annual data from financials DataFrame
        if not financials.empty:
            # Iterate through the index (dates) instead of columns
            for date_index in financials.index:
                try:
                    # Handle both Timestamp and string date indices
                    if hasattr(date_index, 'year'):
                        fiscal_year = date_index.year
                    elif isinstance(date_index, str):
                        # Try to parse as datetime if it's a string
                        fiscal_year = pd.to_datetime(date_index).year
                    else:
                        # Skip if we can't determine the year
                        continue
                    
                    financial_data = FinancialData(
                        symbol=symbol,
                        fiscal_year=fiscal_year,
                        # Income statement data
                        revenue=DataTransformer._safe_get_financial_value(financials, 'Total Revenue', date_index),
                        gross_profit=DataTransformer._safe_get_financial_value(financials, 'Gross Profit', date_index),
                        operating_income=DataTransformer._safe_get_financial_value(financials, 'Operating Income', date_index),
                        net_income=DataTransformer._safe_get_financial_value(financials, 'Net Income', date_index),
                        # Balance sheet data
                        total_assets=DataTransformer._safe_get_financial_value(balance_sheet, 'Total Assets', date_index),
                        total_liabilities=DataTransformer._safe_get_financial_value(balance_sheet, 'Total Liab', date_index),
                        shareholders_equity=DataTransformer._safe_get_financial_value(balance_sheet, 'Total Stockholder Equity', date_index),
                        # Cash flow data
                        operating_cash_flow=DataTransformer._safe_get_financial_value(cash_flow, 'Total Cash From Operating Activities', date_index),
                        free_cash_flow=DataTransformer._safe_get_financial_value(cash_flow, 'Free Cash Flow', date_index),
                        # Ratios from info (these are current ratios, not historical)
                        per=info.get('trailingPE') if fiscal_year == datetime.now().year else None,
                        pbr=info.get('priceToBook') if fiscal_year == datetime.now().year else None,
                        roe=info.get('returnOnEquity') if fiscal_year == datetime.now().year else None,
                        roa=info.get('returnOnAssets') if fiscal_year == datetime.now().year else None,
                        debt_to_equity=info.get('debtToEquity') if fiscal_year == datetime.now().year else None,
                        current_ratio=info.get('currentRatio') if fiscal_year == datetime.now().year else None
                    )
                    
                    # Calculate EPS if we have net income and shares outstanding
                    shares_outstanding = info.get('sharesOutstanding')
                    if financial_data.net_income and shares_outstanding:
                        financial_data.eps = financial_data.net_income / shares_outstanding
                    elif fiscal_year == datetime.now().year:
                        financial_data.eps = info.get('trailingEps')
                    
                    # Calculate additional ratios if we have the data
                    if financial_data.net_income and financial_data.shareholders_equity:
                        financial_data.roe = financial_data.net_income / financial_data.shareholders_equity
                    
                    if financial_data.net_income and financial_data.total_assets:
                        financial_data.roa = financial_data.net_income / financial_data.total_assets
                    
                    # Validate the data using built-in validation
                    if financial_data.validate():
                        financial_data_list.append(financial_data)
                    else:
                        print(f"Warning: Invalid financial data for {symbol} year {fiscal_year}")
                        
                except Exception as e:
                    print(f"Error transforming financial data for {symbol}: {e}")
        
        return financial_data_list
    
    @staticmethod
    def transform_company_info(company_dict: Dict[str, Any]) -> CompanyInfo:
        """
        Transform company info dictionary from Yahoo Finance to CompanyInfo object.
        
        Args:
            company_dict: Dictionary containing company info from Yahoo Finance
            
        Returns:
            CompanyInfo: Validated CompanyInfo object
        """
        symbol = company_dict.get('symbol', '').upper()
        
        if not symbol:
            raise ValueError("Symbol is required in company_dict")
        
        info = company_dict.get('info', {})
        
        company_info = CompanyInfo(
            symbol=symbol,
            company_name=info.get('longName', info.get('shortName', symbol)),
            sector=info.get('sector'),
            industry=info.get('industry'),
            market_cap=info.get('marketCap'),
            country=info.get('country'),
            currency=info.get('currency'),
            exchange=info.get('exchange')
        )
        
        # Validate the data using built-in validation
        if not company_info.validate():
            print(f"Warning: Invalid company info for {symbol}")
        
        return company_info
    
    @staticmethod
    def calculate_technical_indicators(stock_data_list: List[StockData]) -> List[StockData]:
        """
        Calculate additional technical indicators for stock data.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            
        Returns:
            List[StockData]: List with additional technical indicators calculated
        """
        if len(stock_data_list) < 20:  # Need enough data for calculations
            return stock_data_list
        
        # Sort by date to ensure proper calculation
        sorted_data = sorted(stock_data_list, key=lambda x: x.date)
        
        # Calculate Bollinger Bands
        DataTransformer._calculate_bollinger_bands(sorted_data, 20, 2)
        
        # Calculate MACD
        DataTransformer._calculate_macd(sorted_data, 12, 26, 9)
        
        # Calculate Stochastic Oscillator
        DataTransformer._calculate_stochastic(sorted_data, 14)
        
        return sorted_data
    
    @staticmethod
    def _calculate_bollinger_bands(stock_data_list: List[StockData], period: int = 20, std_dev: float = 2) -> None:
        """
        Calculate Bollinger Bands and update stock data in place.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            period: Period for moving average calculation
            std_dev: Number of standard deviations for bands
        """
        if len(stock_data_list) < period:
            return
        
        for i in range(period - 1, len(stock_data_list)):
            prices = [stock_data_list[j].close for j in range(i - period + 1, i + 1)]
            sma = sum(prices) / period
            variance = sum((price - sma) ** 2 for price in prices) / period
            std = variance ** 0.5
            
            # Add Bollinger Bands as additional attributes
            stock_data_list[i].bb_upper = sma + (std_dev * std)
            stock_data_list[i].bb_middle = sma
            stock_data_list[i].bb_lower = sma - (std_dev * std)
    
    @staticmethod
    def _calculate_macd(stock_data_list: List[StockData], fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        """
        Calculate MACD (Moving Average Convergence Divergence) and update stock data in place.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
        """
        if len(stock_data_list) < slow + signal:
            return
        
        # Calculate EMAs
        fast_ema = DataTransformer._calculate_ema([data.close for data in stock_data_list], fast)
        slow_ema = DataTransformer._calculate_ema([data.close for data in stock_data_list], slow)
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(fast_ema)):
            if i < slow - 1:
                macd_line.append(None)
            else:
                macd_line.append(fast_ema[i] - slow_ema[i])
        
        # Calculate Signal line (EMA of MACD line)
        macd_values = [val for val in macd_line if val is not None]
        signal_ema = DataTransformer._calculate_ema(macd_values, signal)
        
        # Update stock data with MACD values
        signal_start_index = slow - 1 + signal - 1
        for i in range(signal_start_index, len(stock_data_list)):
            macd_index = i - (slow - 1)
            signal_index = i - signal_start_index
            
            if macd_index < len(macd_line) and macd_line[macd_index] is not None:
                stock_data_list[i].macd = macd_line[macd_index]
                if signal_index < len(signal_ema):
                    stock_data_list[i].macd_signal = signal_ema[signal_index]
                    stock_data_list[i].macd_histogram = macd_line[macd_index] - signal_ema[signal_index]
    
    @staticmethod
    def _calculate_ema(prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: EMA period
            
        Returns:
            List[float]: EMA values
        """
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = []
        
        # Start with SMA for the first value
        sma = sum(prices[:period]) / period
        ema_values.extend([None] * (period - 1))
        ema_values.append(sma)
        
        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def _calculate_stochastic(stock_data_list: List[StockData], period: int = 14) -> None:
        """
        Calculate Stochastic Oscillator and update stock data in place.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            period: Period for stochastic calculation
        """
        if len(stock_data_list) < period:
            return
        
        for i in range(period - 1, len(stock_data_list)):
            # Get high and low values for the period
            highs = [stock_data_list[j].high for j in range(i - period + 1, i + 1)]
            lows = [stock_data_list[j].low for j in range(i - period + 1, i + 1)]
            
            highest_high = max(highs)
            lowest_low = min(lows)
            current_close = stock_data_list[i].close
            
            # Calculate %K
            if highest_high != lowest_low:
                k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
                stock_data_list[i].stoch_k = k_percent
            else:
                stock_data_list[i].stoch_k = 50  # Neutral value when no range
    
    @staticmethod
    def enrich_with_technical_indicators(stock_data_list: List[StockData]) -> List[StockData]:
        """
        Enrich stock data with technical indicators.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            
        Returns:
            List[StockData]: List with technical indicators calculated
        """
        if len(stock_data_list) < 50:  # Need enough data for 50-day SMA
            return stock_data_list
        
        # Sort by date to ensure proper calculation
        sorted_data = sorted(stock_data_list, key=lambda x: x.date)
        
        # Calculate Simple Moving Averages
        DataTransformer._calculate_sma(sorted_data, 20)
        DataTransformer._calculate_sma(sorted_data, 50)
        
        # Calculate RSI
        DataTransformer._calculate_rsi(sorted_data, 14)
        
        # Calculate additional technical indicators if we have enough data
        if len(sorted_data) >= 50:
            enriched_data = DataTransformer.calculate_technical_indicators(sorted_data)
            return enriched_data
        
        return sorted_data
    
    @staticmethod
    def _calculate_sma(stock_data_list: List[StockData], period: int) -> None:
        """
        Calculate Simple Moving Average and update stock data in place.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            period: Period for SMA calculation
        """
        if len(stock_data_list) < period:
            return
        
        for i in range(period - 1, len(stock_data_list)):
            prices = [stock_data_list[j].close for j in range(i - period + 1, i + 1)]
            sma_value = sum(prices) / period
            
            if period == 20:
                stock_data_list[i].sma_20 = sma_value
            elif period == 50:
                stock_data_list[i].sma_50 = sma_value
    
    @staticmethod
    def _calculate_rsi(stock_data_list: List[StockData], period: int = 14) -> None:
        """
        Calculate Relative Strength Index and update stock data in place.
        
        Args:
            stock_data_list: List of StockData objects sorted by date
            period: Period for RSI calculation (default 14)
        """
        if len(stock_data_list) < period + 1:
            return
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(stock_data_list)):
            change = stock_data_list[i].close - stock_data_list[i-1].close
            price_changes.append(change)
        
        # Calculate RSI for each point after the initial period
        for i in range(period, len(price_changes) + 1):
            recent_changes = price_changes[i-period:i]
            
            gains = [change for change in recent_changes if change > 0]
            losses = [-change for change in recent_changes if change < 0]
            
            avg_gain = sum(gains) / period if gains else 0
            avg_loss = sum(losses) / period if losses else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Update the stock data (i corresponds to price_changes index, so add 1 for stock_data_list)
            stock_data_list[i].rsi = rsi
    
    @staticmethod
    def _safe_get_financial_value(df: pd.DataFrame, key: str, date_index) -> Optional[float]:
        """
        Safely get a financial value from DataFrame.
        
        Args:
            df: Financial data DataFrame
            key: Row key to look for
            date_index: Date index to get value from
            
        Returns:
            Optional[float]: Financial value or None if not found
        """
        try:
            if df.empty or key not in df.columns or date_index not in df.index:
                return None
            
            value = df.loc[date_index, key]
            return float(value) if pd.notna(value) else None
        except (KeyError, ValueError, TypeError):
            return None
    
    @staticmethod
    def detect_and_handle_anomalies(stock_data_list: List[StockData], 
                                   handle_anomalies: bool = False) -> tuple:
        """
        Detect anomalies in stock data and optionally filter them out.
        
        Args:
            stock_data_list: List of StockData objects to analyze
            handle_anomalies: Whether to filter out severe anomalies
            
        Returns:
            tuple: (filtered_data_list, anomalies_list)
        """
        from .validation import DataValidator

        # Detect anomalies
        anomalies = DataValidator.detect_anomalies(stock_data_list)
        
        if not handle_anomalies:
            return stock_data_list, anomalies
        
        # Filter out severe anomalies (errors)
        filtered_data = []
        severe_anomaly_dates = set()
        
        # Collect dates with severe anomalies
        for anomaly in anomalies:
            if anomaly.severity == "error":
                # Find the corresponding stock data by matching field values
                for stock_data in stock_data_list:
                    if hasattr(stock_data, anomaly.field) and getattr(stock_data, anomaly.field) == anomaly.value:
                        severe_anomaly_dates.add(stock_data.date)
        
        # Filter out data points with severe anomalies
        for stock_data in stock_data_list:
            if stock_data.date not in severe_anomaly_dates:
                filtered_data.append(stock_data)
        
        return filtered_data, anomalies
    
    @staticmethod
    def batch_transform_stock_data(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, List[StockData]]:
        """
        Transform multiple symbols' stock data in batch.
        
        Args:
            data_dict: Dictionary mapping symbols to their DataFrames
            
        Returns:
            Dict[str, List[StockData]]: Dictionary mapping symbols to their StockData lists
        """
        results = {}
        
        for symbol, df in data_dict.items():
            try:
                stock_data_list = DataTransformer.transform_stock_data(df, symbol)
                # Enrich with technical indicators
                enriched_data = DataTransformer.enrich_with_technical_indicators(stock_data_list)
                results[symbol] = enriched_data
            except Exception as e:
                print(f"Error transforming data for {symbol}: {e}")
                results[symbol] = []
        
        return results
    
