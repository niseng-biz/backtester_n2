"""
Unit tests for data reader implementations.
"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from backtester.data_reader import CSVDataReader
from backtester.models import MarketData


class TestCSVDataReader:
    """Test cases for CSVDataReader class."""
    
    def create_test_csv(self, filename: str, data: str) -> str:
        """Create a temporary CSV file for testing."""
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(data)
        return file_path
    
    def test_load_valid_csv(self):
        """Test loading valid CSV data."""
        csv_data = """Date,Open,High,Low,Close,Volume
2023-01-01,100.0,105.0,95.0,102.0,1000
2023-01-02,102.0,108.0,100.0,106.0,1200
2023-01-03,106.0,110.0,104.0,108.0,1100"""
        
        file_path = self.create_test_csv("test_valid.csv", csv_data)
        
        try:
            reader = CSVDataReader()
            data = reader.load_data(file_path)
            
            assert len(data) == 3
            assert data[0].timestamp == datetime(2023, 1, 1)
            assert data[0].open == 100.0
            assert data[0].high == 105.0
            assert data[0].low == 95.0
            assert data[0].close == 102.0
            assert data[0].volume == 1000
            
            # Check chronological order
            assert data[0].timestamp < data[1].timestamp < data[2].timestamp
            
        finally:
            os.unlink(file_path)
    
    def test_load_custom_columns(self):
        """Test loading CSV with custom column names."""
        csv_data = """Timestamp,O,H,L,C,Vol
2023-01-01,100.0,105.0,95.0,102.0,1000
2023-01-02,102.0,108.0,100.0,106.0,1200"""
        
        file_path = self.create_test_csv("test_custom.csv", csv_data)
        
        try:
            reader = CSVDataReader(
                date_column='Timestamp',
                open_column='O',
                high_column='H',
                low_column='L',
                close_column='C',
                volume_column='Vol'
            )
            data = reader.load_data(file_path)
            
            assert len(data) == 2
            assert data[0].open == 100.0
            
        finally:
            os.unlink(file_path)
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        reader = CSVDataReader()
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            reader.load_data("non_existent_file.csv")
    
    def test_missing_columns(self):
        """Test handling of missing required columns."""
        csv_data = """Date,Open,High,Low,Volume
2023-01-01,100.0,105.0,95.0,1000"""
        
        file_path = self.create_test_csv("test_missing_cols.csv", csv_data)
        
        try:
            reader = CSVDataReader()
            with pytest.raises(ValueError, match="Missing required columns"):
                reader.load_data(file_path)
        finally:
            os.unlink(file_path)
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        csv_data = """Date,Open,High,Low,Close,Volume
2023-01-01,invalid,105.0,95.0,102.0,1000"""
        
        file_path = self.create_test_csv("test_invalid_types.csv", csv_data)
        
        try:
            reader = CSVDataReader()
            with pytest.raises(ValueError, match="Invalid data in row"):
                reader.load_data(file_path)
        finally:
            os.unlink(file_path)
    
    def test_invalid_date_format(self):
        """Test handling of invalid date formats."""
        csv_data = """Date,Open,High,Low,Close,Volume
invalid-date,100.0,105.0,95.0,102.0,1000"""
        
        file_path = self.create_test_csv("test_invalid_date.csv", csv_data)
        
        try:
            reader = CSVDataReader()
            with pytest.raises(ValueError, match="Invalid data in row"):
                reader.load_data(file_path)
        finally:
            os.unlink(file_path)
    
    def test_empty_csv(self):
        """Test handling of empty CSV file."""
        file_path = self.create_test_csv("test_empty.csv", "")
        
        try:
            reader = CSVDataReader()
            with pytest.raises(ValueError, match="CSV file is empty"):
                reader.load_data(file_path)
        finally:
            os.unlink(file_path)
    
    def test_data_validation_success(self):
        """Test successful data validation."""
        data = [
            MarketData(datetime(2023, 1, 1), 100.0, 105.0, 95.0, 102.0, 1000),
            MarketData(datetime(2023, 1, 2), 102.0, 108.0, 100.0, 106.0, 1200),
            MarketData(datetime(2023, 1, 3), 106.0, 110.0, 104.0, 108.0, 1100)
        ]
        
        reader = CSVDataReader()
        assert reader.validate_data(data) is True
    
    def test_data_validation_empty(self):
        """Test validation of empty data."""
        reader = CSVDataReader()
        assert reader.validate_data([]) is False
    
    def test_data_validation_wrong_order(self):
        """Test validation of incorrectly ordered data."""
        data = [
            MarketData(datetime(2023, 1, 2), 102.0, 108.0, 100.0, 106.0, 1200),
            MarketData(datetime(2023, 1, 1), 100.0, 105.0, 95.0, 102.0, 1000)  # Wrong order
        ]
        
        reader = CSVDataReader()
        assert reader.validate_data(data) is False
    
    def test_different_date_formats(self):
        """Test parsing different date formats."""
        csv_data = """Date,Open,High,Low,Close,Volume
01/01/2023,100.0,105.0,95.0,102.0,1000
01/02/2023,102.0,108.0,100.0,106.0,1200"""
        
        file_path = self.create_test_csv("test_date_formats.csv", csv_data)
        
        try:
            reader = CSVDataReader()
            data = reader.load_data(file_path)
            
            assert len(data) == 2
            assert data[0].timestamp == datetime(2023, 1, 1)
            
        finally:
            os.unlink(file_path)


