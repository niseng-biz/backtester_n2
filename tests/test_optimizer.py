"""
Tests for the optimizer module.
"""

from datetime import datetime, timedelta

import pytest

from backtester.models import MarketData
from backtester.optimizer import DataSplitter, ParameterSpace


class TestDataSplitter:
    """Test cases for DataSplitter class."""
    
    def create_sample_data(self, n_points: int = 100) -> list[MarketData]:
        """Create sample market data for testing."""
        data = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(n_points):
            data.append(MarketData(
                timestamp=base_date + timedelta(days=i),
                open=100.0 + i * 0.1,
                high=101.0 + i * 0.1,
                low=99.0 + i * 0.1,
                close=100.5 + i * 0.1,
                volume=1000
            ))
        
        return data
    
    def test_chronological_split_default_ratios(self):
        """Test chronological split with default ratios."""
        data = self.create_sample_data(100)
        splits = DataSplitter.chronological_split(data)
        
        assert len(splits) == 3
        assert 'train' in splits
        assert 'validation' in splits
        assert 'test' in splits
        
        # Check split sizes (60/20/20)
        assert len(splits['train']) == 60
        assert len(splits['validation']) == 20
        assert len(splits['test']) == 20
        
        # Check chronological order
        assert splits['train'][0].timestamp < splits['validation'][0].timestamp
        assert splits['validation'][0].timestamp < splits['test'][0].timestamp
        
    def test_chronological_split_custom_ratios(self):
        """Test chronological split with custom ratios."""
        data = self.create_sample_data(100)
        splits = DataSplitter.chronological_split(data, 0.7, 0.2, 0.1)
        
        assert len(splits['train']) == 70
        assert len(splits['validation']) == 20
        assert len(splits['test']) == 10
        
    def test_validate_split_ratios_valid(self):
        """Test validation of valid split ratios."""
        assert DataSplitter.validate_split_ratios(0.6, 0.2, 0.2) == True
        assert DataSplitter.validate_split_ratios(0.7, 0.2, 0.1) == True
        assert DataSplitter.validate_split_ratios(0.5, 0.3, 0.2) == True
        
    def test_validate_split_ratios_invalid(self):
        """Test validation of invalid split ratios."""
        assert DataSplitter.validate_split_ratios(0.6, 0.2, 0.3) == False  # Sum > 1
        assert DataSplitter.validate_split_ratios(0.5, 0.2, 0.2) == False  # Sum < 1
        assert DataSplitter.validate_split_ratios(0.4, 0.3, 0.2) == False  # Sum < 1
        
    def test_insufficient_data_error(self):
        """Test error handling for insufficient data."""
        data = self.create_sample_data(50)  # Less than minimum 100
        
        with pytest.raises(ValueError, match="Insufficient data"):
            DataSplitter.chronological_split(data)
            
    def test_invalid_ratios_error(self):
        """Test error handling for invalid ratios."""
        data = self.create_sample_data(100)
        
        with pytest.raises(ValueError, match="Split ratios must sum to 1.0"):
            DataSplitter.chronological_split(data, 0.6, 0.2, 0.3)
            
    def test_get_split_info(self):
        """Test split information generation."""
        data = self.create_sample_data(100)
        splits = DataSplitter.chronological_split(data)
        info = DataSplitter.get_split_info(splits)
        
        assert info['total_points'] == 100
        assert info['train_points'] == 60
        assert info['validation_points'] == 20
        assert info['test_points'] == 20
        
        assert abs(info['train_ratio'] - 0.6) < 0.01
        assert abs(info['validation_ratio'] - 0.2) < 0.01
        assert abs(info['test_ratio'] - 0.2) < 0.01
        
        # Check date ranges
        assert 'train_start_date' in info
        assert 'train_end_date' in info
        assert 'validation_start_date' in info
        assert 'test_end_date' in info


class TestParameterSpace:
    """Test cases for ParameterSpace class."""
    
    def test_add_int_parameter(self):
        """Test adding integer parameters."""
        space = ParameterSpace()
        space.add_int_parameter('short_period', 5, 50, 1)
        
        assert 'short_period' in space.ranges
        assert space.ranges['short_period']['type'] == 'int'
        assert space.ranges['short_period']['min'] == 5
        assert space.ranges['short_period']['max'] == 50
        assert space.ranges['short_period']['step'] == 1
        
    def test_add_float_parameter(self):
        """Test adding float parameters."""
        space = ParameterSpace()
        space.add_float_parameter('threshold', 0.1, 0.9, 0.1)
        
        assert 'threshold' in space.ranges
        assert space.ranges['threshold']['type'] == 'float'
        assert space.ranges['threshold']['min'] == 0.1
        assert space.ranges['threshold']['max'] == 0.9
        assert space.ranges['threshold']['step'] == 0.1
        
    def test_add_categorical_parameter(self):
        """Test adding categorical parameters."""
        space = ParameterSpace()
        space.add_categorical_parameter('method', ['sma', 'ema', 'wma'])
        
        assert 'method' in space.ranges
        assert space.ranges['method']['type'] == 'categorical'
        assert space.ranges['method']['choices'] == ['sma', 'ema', 'wma']
        
    def test_add_constraint(self):
        """Test adding parameter constraints."""
        space = ParameterSpace()
        
        def constraint_func(params):
            return params.get('short_period', 0) < params.get('long_period', 100)
            
        space.add_constraint(constraint_func)
        assert len(space.constraints) == 1
        
    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        space = ParameterSpace()
        
        def constraint_func(params):
            return params.get('short_period', 0) < params.get('long_period', 100)
            
        space.add_constraint(constraint_func)
        
        valid_params = {'short_period': 10, 'long_period': 30}
        assert space.validate_parameters(valid_params) == True
        
    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid parameters."""
        space = ParameterSpace()
        
        def constraint_func(params):
            return params.get('short_period', 0) < params.get('long_period', 100)
            
        space.add_constraint(constraint_func)
        
        invalid_params = {'short_period': 30, 'long_period': 10}
        assert space.validate_parameters(invalid_params) == False


if __name__ == "__main__":
    pytest.main([__file__])