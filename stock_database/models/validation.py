"""
Data validation utilities for stock database models.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class Anomaly:
    """
    Represents an anomaly detected in data.
    """
    
    def __init__(self, anomaly_type: str, field: str, value: Any, 
                 expected_range: Optional[tuple] = None, 
                 severity: str = "warning", 
                 description: Optional[str] = None):
        self.anomaly_type = anomaly_type
        self.field = field
        self.value = value
        self.expected_range = expected_range
        self.severity = severity  # "info", "warning", "error"
        self.description = description or f"{anomaly_type} detected in {field}"
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.description}: {self.field}={self.value}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert anomaly to dictionary."""
        return {
            'type': self.anomaly_type,
            'field': self.field,
            'value': self.value,
            'expected_range': self.expected_range,
            'severity': self.severity,
            'description': self.description
        }


class ValidationResult:
    """
    Result of data validation containing validation status and error messages.
    """
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str):
        """Add an error message and mark as invalid."""
        self.is_valid = False
        self.errors.append(error)
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {'; '.join(self.errors)}"


class DataValidator:
    """
    Comprehensive data validator for all stock database models.
    """
    
    @staticmethod
    def validate_symbol(symbol: str) -> ValidationResult:
        """
        Validate stock symbol format.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        if not symbol:
            result.add_error("Symbol cannot be empty")
            return result
        
        if not isinstance(symbol, str):
            result.add_error("Symbol must be a string")
            return result
        
        # Check symbol format (letters, numbers, dots, hyphens allowed)
        if not re.match(r'^[A-Z0-9.\-]+$', symbol.upper()):
            result.add_error("Symbol contains invalid characters")
        
        if len(symbol) > 10:
            result.add_error("Symbol is too long (max 10 characters)")
        
        return result
    
    @staticmethod
    def validate_stock_data(data) -> ValidationResult:
        """
        Validate StockData instance.
        
        Args:
            data: StockData instance to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Validate symbol
        symbol_result = DataValidator.validate_symbol(data.symbol)
        if not symbol_result:
            result.errors.extend(symbol_result.errors)
            result.is_valid = False
        
        # Validate date
        if not isinstance(data.date, datetime):
            result.add_error("Date must be a datetime object")
        elif data.date > datetime.now():
            result.add_error("Date cannot be in the future")
        
        # Validate price fields
        price_fields = {
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'adjusted_close': data.adjusted_close
        }
        
        for field_name, value in price_fields.items():
            if value is None:
                result.add_error(f"{field_name} cannot be None")
            elif not isinstance(value, (int, float)):
                result.add_error(f"{field_name} must be a number")
            elif value < 0:
                result.add_error(f"{field_name} cannot be negative")
        
        # Validate volume
        if not isinstance(data.volume, int):
            result.add_error("Volume must be an integer")
        elif data.volume < 0:
            result.add_error("Volume cannot be negative")
        
        # Validate OHLC relationships
        if all(x is not None for x in [data.open, data.high, data.low, data.close]):
            if data.high < max(data.open, data.close):
                result.add_error("High price must be >= max(open, close)")
            if data.low > min(data.open, data.close):
                result.add_error("Low price must be <= min(open, close)")
        
        # Validate technical indicators
        if hasattr(data, 'rsi') and data.rsi is not None:
            if not isinstance(data.rsi, (int, float)):
                result.add_error("RSI must be a number")
            elif not (0 <= data.rsi <= 100):
                result.add_error("RSI must be between 0 and 100")
        
        # Validate Stochastic %K
        if hasattr(data, 'stoch_k') and data.stoch_k is not None:
            if not isinstance(data.stoch_k, (int, float)):
                result.add_error("Stochastic %K must be a number")
            elif not (0 <= data.stoch_k <= 100):
                result.add_error("Stochastic %K must be between 0 and 100")
        
        # Validate Bollinger Bands
        if (hasattr(data, 'bb_upper') and hasattr(data, 'bb_middle') and hasattr(data, 'bb_lower') and
            all(x is not None for x in [data.bb_upper, data.bb_middle, data.bb_lower])):
            if not (data.bb_lower <= data.bb_middle <= data.bb_upper):
                result.add_error("Bollinger Bands must be ordered: lower <= middle <= upper")
        
        return result
    
    @staticmethod
    def validate_financial_data(data) -> ValidationResult:
        """
        Validate FinancialData instance.
        
        Args:
            data: FinancialData instance to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Validate symbol
        symbol_result = DataValidator.validate_symbol(data.symbol)
        if not symbol_result:
            result.errors.extend(symbol_result.errors)
            result.is_valid = False
        
        # Validate fiscal year
        if not isinstance(data.fiscal_year, int):
            result.add_error("Fiscal year must be an integer")
        elif data.fiscal_year < 1900 or data.fiscal_year > datetime.now().year + 1:
            result.add_error("Fiscal year is out of reasonable range")
        
        # Validate fiscal quarter
        if hasattr(data, 'fiscal_quarter') and data.fiscal_quarter is not None:
            if not isinstance(data.fiscal_quarter, int):
                result.add_error("Fiscal quarter must be an integer")
            elif not (1 <= data.fiscal_quarter <= 4):
                result.add_error("Fiscal quarter must be between 1 and 4")
        
        # Validate financial ratios
        ratio_validations = {
            'roe': (-1, 2),  # -100% to 200%
            'roa': (-1, 1),  # -100% to 100%
            'current_ratio': (0, None),  # >= 0
            'debt_to_equity': (0, None),  # >= 0
        }
        
        for field_name, (min_val, max_val) in ratio_validations.items():
            if hasattr(data, field_name):
                value = getattr(data, field_name)
                if value is not None:
                    if not isinstance(value, (int, float)):
                        result.add_error(f"{field_name} must be a number")
                    elif min_val is not None and value < min_val:
                        result.add_error(f"{field_name} must be >= {min_val}")
                    elif max_val is not None and value > max_val:
                        result.add_error(f"{field_name} must be <= {max_val}")
        
        # Validate balance sheet equation if all components are available
        if (hasattr(data, 'total_assets') and hasattr(data, 'total_liabilities') and 
            hasattr(data, 'shareholders_equity') and 
            all(x is not None for x in [data.total_assets, data.total_liabilities, data.shareholders_equity])):
            expected_assets = data.total_liabilities + data.shareholders_equity
            if abs(data.total_assets - expected_assets) > abs(data.total_assets * 0.01):  # 1% tolerance
                result.add_error("Balance sheet equation does not balance: Assets ≠ Liabilities + Equity")
        
        return result
    
    @staticmethod
    def validate_company_info(data) -> ValidationResult:
        """
        Validate CompanyInfo instance.
        
        Args:
            data: CompanyInfo instance to validate
            
        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()
        
        # Validate symbol
        symbol_result = DataValidator.validate_symbol(data.symbol)
        if not symbol_result:
            result.errors.extend(symbol_result.errors)
            result.is_valid = False
        
        # Validate company name
        if not hasattr(data, 'company_name') or not data.company_name:
            result.add_error("Company name cannot be empty")
        elif not isinstance(data.company_name, str):
            result.add_error("Company name must be a string")
        elif len(data.company_name) > 200:
            result.add_error("Company name is too long (max 200 characters)")
        
        # Validate market cap
        if hasattr(data, 'market_cap') and data.market_cap is not None:
            if not isinstance(data.market_cap, (int, float)):
                result.add_error("Market cap must be a number")
            elif data.market_cap < 0:
                result.add_error("Market cap cannot be negative")
        
        # Validate currency code
        if hasattr(data, 'currency') and data.currency is not None:
            if not isinstance(data.currency, str):
                result.add_error("Currency must be a string")
            elif len(data.currency) != 3:
                result.add_error("Currency must be a 3-letter code")
            elif not data.currency.isupper():
                result.add_error("Currency code must be uppercase")
        
        return result
    
    @staticmethod
    def detect_anomalies(data) -> List[Anomaly]:
        """
        Detect anomalies in stock data using statistical methods.
        
        Args:
            data: Single StockData instance or list of StockData instances
            
        Returns:
            List[Anomaly]: List of detected anomalies
        """
        anomalies = []
        
        if not isinstance(data, list):
            data = [data]
        
        # OHLC consistency check works with single data point
        anomalies.extend(DataValidator._detect_ohlc_inconsistencies(data))
        
        if len(data) < 2:
            return anomalies
        
        # Convert to DataFrame for easier analysis
        df_data = []
        for stock_data in data:
            df_data.append({
                'symbol': stock_data.symbol,
                'date': stock_data.date,
                'open': stock_data.open,
                'high': stock_data.high,
                'low': stock_data.low,
                'close': stock_data.close,
                'volume': stock_data.volume,
                'adjusted_close': stock_data.adjusted_close
            })
        
        df = pd.DataFrame(df_data)
        
        # Price anomaly detection using IQR method
        price_fields = ['open', 'high', 'low', 'close', 'adjusted_close']
        for field in price_fields:
            if field in df.columns:
                anomalies.extend(DataValidator._detect_outliers_iqr(df, field, data))
        
        # Volume anomaly detection
        if 'volume' in df.columns:
            anomalies.extend(DataValidator._detect_outliers_iqr(df, 'volume', data))
        
        # Price gap detection
        anomalies.extend(DataValidator._detect_price_gaps(df, data))
        
        # Volume spike detection
        anomalies.extend(DataValidator._detect_volume_spikes(df, data))
        
        return anomalies
    
    @staticmethod
    def _detect_outliers_iqr(df: pd.DataFrame, field: str, data) -> List[Anomaly]:
        """Detect outliers using Interquartile Range method."""
        anomalies = []
        
        if len(df) < 4:  # Need at least 4 data points for IQR
            return anomalies
        
        values = df[field].dropna()
        if len(values) < 4:
            return anomalies
        
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                anomalies.append(Anomaly(
                    anomaly_type="outlier",
                    field=field,
                    value=value,
                    expected_range=(lower_bound, upper_bound),
                    severity="warning",
                    description=f"Statistical outlier detected in {field}"
                ))
        
        return anomalies
    
    @staticmethod
    def _detect_price_gaps(df: pd.DataFrame, data) -> List[Anomaly]:
        """Detect significant price gaps between consecutive days."""
        anomalies = []
        
        if len(df) < 2:
            return anomalies
        
        df_sorted = df.sort_values('date')
        
        for i in range(1, len(df_sorted)):
            prev_close = df_sorted.iloc[i-1]['close']
            curr_open = df_sorted.iloc[i]['open']
            
            if prev_close > 0:  # Avoid division by zero
                gap_percentage = abs(curr_open - prev_close) / prev_close
                
                if gap_percentage > 0.1:  # 10% gap threshold
                    anomalies.append(Anomaly(
                        anomaly_type="price_gap",
                        field="open",
                        value=curr_open,
                        expected_range=(prev_close * 0.9, prev_close * 1.1),
                        severity="warning",
                        description=f"Significant price gap detected: {gap_percentage:.2%}"
                    ))
        
        return anomalies
    
    @staticmethod
    def _detect_volume_spikes(df: pd.DataFrame, data) -> List[Anomaly]:
        """Detect unusual volume spikes."""
        anomalies = []
        
        if len(df) < 5:  # Need enough data for meaningful average
            return anomalies
        
        volumes = df['volume'].dropna()
        if len(volumes) < 5:
            return anomalies
        
        avg_volume = volumes.mean()
        std_volume = volumes.std()
        
        for i, volume in enumerate(volumes):
            if volume > avg_volume + 3 * std_volume:  # 3 standard deviations
                anomalies.append(Anomaly(
                    anomaly_type="volume_spike",
                    field="volume",
                    value=volume,
                    expected_range=(0, avg_volume + 2 * std_volume),
                    severity="info",
                    description=f"Unusual volume spike detected: {volume:,} vs avg {avg_volume:,.0f}"
                ))
        
        return anomalies
    
    @staticmethod
    def _detect_ohlc_inconsistencies(data) -> List[Anomaly]:
        """Detect OHLC data inconsistencies."""
        anomalies = []
        
        for stock_data in data:
            # Check if high is actually the highest
            if stock_data.high < max(stock_data.open, stock_data.close):
                anomalies.append(Anomaly(
                    anomaly_type="ohlc_inconsistency",
                    field="high",
                    value=stock_data.high,
                    severity="error",
                    description="High price is less than max(open, close)"
                ))
            
            # Check if low is actually the lowest
            if stock_data.low > min(stock_data.open, stock_data.close):
                anomalies.append(Anomaly(
                    anomaly_type="ohlc_inconsistency",
                    field="low",
                    value=stock_data.low,
                    severity="error",
                    description="Low price is greater than min(open, close)"
                ))
        
        return anomalies
    
    @staticmethod
    def validate_stock_data_object(data) -> bool:
        """
        Validate StockData object and return boolean result.
        
        Args:
            data: StockData instance to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        result = DataValidator.validate_stock_data(data)
        return result.is_valid
    
    @staticmethod
    def validate_financial_data_object(data) -> bool:
        """
        Validate FinancialData object and return boolean result.
        
        Args:
            data: FinancialData instance to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        result = DataValidator.validate_financial_data(data)
        return result.is_valid
    
    @staticmethod
    def validate_company_info_object(data) -> bool:
        """
        Validate CompanyInfo object and return boolean result.
        
        Args:
            data: CompanyInfo instance to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        result = DataValidator.validate_company_info(data)
        return result.is_valid
    
    @staticmethod
    def validate_batch(data_list) -> Dict[int, ValidationResult]:
        """
        Validate a batch of data objects.
        
        Args:
            data_list: List of data objects to validate
            
        Returns:
            Dict[int, ValidationResult]: Dictionary mapping index to validation result
        """
        results = {}
        
        for i, data in enumerate(data_list):
            # Check data type by class name to avoid imports
            class_name = data.__class__.__name__
            
            if class_name == 'StockData':
                results[i] = DataValidator.validate_stock_data(data)
            elif class_name == 'FinancialData':
                results[i] = DataValidator.validate_financial_data(data)
            elif class_name == 'CompanyInfo':
                results[i] = DataValidator.validate_company_info(data)
            else:
                result = ValidationResult()
                result.add_error(f"Unknown data type: {type(data)}")
                results[i] = result
        
        return results