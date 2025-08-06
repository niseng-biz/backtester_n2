"""
Unit tests for data reader implementations.
"""

from datetime import datetime

import pytest

from backtester.data_reader import CSVDataReader
from backtester.models import MarketData


class TestCSVDataReader:
    """Test cases for CSVDataReader class."""
    
    def test_load_valid_csv(self, temp_csv_file):
        """Test loading valid CSV data."""
        reader = CSVDataReader()
        data = reader.load_data(temp_csv_file)
        
        assert len(data) == 5
        assert data[0].timestamp == datetime(2024, 1, 1)
        assert data[0].open == 100.0
        assert data[0].high == 105.0
        assert data[0].low == 95.0
        assert data[0].close == 102.0
        assert data[0].volume == 1000
        
        # Check chronological order
        assert data[0].timestamp < data[1].timestamp < data[2].timestamp
    
    def test_load_custom_columns(self, tmp_path):
        """Test loading CSV with custom column names."""
        csv_data = """Timestamp,O,H,L,C,Vol
2023-01-01,100.0,105.0,95.0,102.0,1000
2023-01-02,102.0,108.0,100.0,106.0,1200"""
        
        csv_file = tmp_path / "test_custom.csv"
        csv_file.write_text(csv_data)
        
        reader = CSVDataReader(
            date_column='Timestamp',
            open_column='O',
            high_column='H',
            low_column='L',
            close_column='C',
            volume_column='Vol'
        )
        data = reader.load_data(str(csv_file))
        
        assert len(data) == 2
        assert data[0].open == 100.0
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        reader = CSVDataReader()
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            reader.load_data("non_existent_file.csv")
    
    def test_missing_columns(self, tmp_path):
        """Test handling of missing required columns."""
        csv_data = """Date,Open,High,Low,Volume
2023-01-01,100.0,105.0,95.0,1000"""
        
        csv_file = tmp_path / "test_missing_cols.csv"
        csv_file.write_text(csv_data)
        
        reader = CSVDataReader()
        with pytest.raises(ValueError, match="Missing required columns"):
            reader.load_data(str(csv_file))
    
    def test_invalid_data_types(self, tmp_path):
        """Test handling of invalid data types."""
        csv_data = """Date,Open,High,Low,Close,Volume
2023-01-01,invalid,105.0,95.0,102.0,1000"""
        
        csv_file = tmp_path / "test_invalid_types.csv"
        csv_file.write_text(csv_data)
        
        reader = CSVDataReader()
        with pytest.raises(ValueError, match="Invalid data in row"):
            reader.load_data(str(csv_file))
    
    def test_invalid_date_format(self, tmp_path):
        """Test handling of invalid date formats."""
        csv_data = """Date,Open,High,Low,Close,Volume
invalid-date,100.0,105.0,95.0,102.0,1000"""
        
        csv_file = tmp_path / "test_invalid_date.csv"
        csv_file.write_text(csv_data)
        
        reader = CSVDataReader()
        with pytest.raises(ValueError, match="Invalid data in row"):
            reader.load_data(str(csv_file))
    
    def test_empty_csv(self, tmp_path):
        """Test handling of empty CSV file."""
        csv_file = tmp_path / "test_empty.csv"
        csv_file.write_text("")
        
        reader = CSVDataReader()
        with pytest.raises(ValueError, match="CSV file is empty"):
            reader.load_data(str(csv_file))
    
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
    
    def test_different_date_formats(self, tmp_path):
        """Test parsing different date formats."""
        csv_data = """Date,Open,High,Low,Close,Volume
01/01/2023,100.0,105.0,95.0,102.0,1000
01/02/2023,102.0,108.0,100.0,106.0,1200"""
        
        csv_file = tmp_path / "test_date_formats.csv"
        csv_file.write_text(csv_data)
        
        reader = CSVDataReader()
        data = reader.load_data(str(csv_file))
        
        assert len(data) == 2
        assert data[0].timestamp == datetime(2023, 1, 1)


