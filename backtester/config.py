"""
Configuration utilities for backtester components.
"""

from .models import LotConfig, LotSizeMode


class ConfigFactory:
    """Factory class for creating common configurations."""
    
    @staticmethod
    def create_crypto_lot_config(
        lot_size_mode: LotSizeMode = LotSizeMode.VARIABLE,
        capital_percentage: float = 0.8,
        max_lot_size: float = 10.0
    ) -> LotConfig:
        """
        Create standard crypto LOT configuration.
        
        Args:
            lot_size_mode: LOT sizing mode (VARIABLE or FIXED)
            capital_percentage: Percentage of capital to use (for VARIABLE mode)
            max_lot_size: Maximum lot size allowed
            
        Returns:
            Configured LotConfig for crypto trading
        """
        return LotConfig(
            asset_type="crypto",
            min_lot_size=0.01,
            lot_step=0.01,
            lot_size_mode=lot_size_mode,
            capital_percentage=capital_percentage,
            max_lot_size=max_lot_size
        )
    
    @staticmethod
    def create_stock_lot_config(
        lot_size_mode: LotSizeMode = LotSizeMode.FIXED,
        capital_percentage: float = 1.0,
        max_lot_size: float = 1000.0
    ) -> LotConfig:
        """
        Create standard stock LOT configuration.
        
        Args:
            lot_size_mode: LOT sizing mode (VARIABLE or FIXED)
            capital_percentage: Percentage of capital to use (for VARIABLE mode)
            max_lot_size: Maximum lot size allowed
            
        Returns:
            Configured LotConfig for stock trading
        """
        return LotConfig(
            asset_type="stock",
            min_lot_size=1.0,
            lot_step=1.0,
            lot_size_mode=lot_size_mode,
            capital_percentage=capital_percentage,
            max_lot_size=max_lot_size
        )