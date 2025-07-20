"""
Technical indicators for trading strategies.
"""

from typing import List, Optional


class TechnicalIndicators:
    """Collection of technical indicators for trading strategies."""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: List of closing prices
            period: RSI calculation period (default 14)

        Returns:
            List of RSI values (None for insufficient data points)
        """
        if len(prices) < period + 1:
            return [None] * len(prices)

        rsi_values = [None] * period

        # Calculate price changes
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i - 1])

        # Calculate initial average gain and loss
        gains = [max(0, change) for change in price_changes[:period]]
        losses = [abs(min(0, change)) for change in price_changes[:period]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Calculate first RSI value
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)

        # Calculate subsequent RSI values using smoothed averages
        for i in range(period + 1, len(prices)):
            change = prices[i] - prices[i - 1]
            gain = max(0, change)
            loss = abs(min(0, change))

            # Smoothed averages (Wilder's smoothing)
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period

            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        return rsi_values

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            prices: List of prices
            period: Moving average period

        Returns:
            List of SMA values (None for insufficient data points)
        """
        if len(prices) < period:
            return [None] * len(prices)

        sma_values = [None] * (period - 1)

        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1 : i + 1]) / period
            sma_values.append(sma)

        return sma_values

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            prices: List of prices
            period: EMA period

        Returns:
            List of EMA values (None for insufficient data points)
        """
        if len(prices) < period:
            return [None] * len(prices)

        ema_values = [None] * (period - 1)

        # Calculate first EMA as SMA
        first_ema = sum(prices[:period]) / period
        ema_values.append(first_ema)

        # Calculate multiplier
        multiplier = 2 / (period + 1)

        # Calculate subsequent EMA values
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)

        return ema_values

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float], period: int = 20, std_dev: float = 2.0
    ) -> tuple:
        """
        Calculate Bollinger Bands.

        Args:
            prices: List of prices
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Tuple of (upper_band, middle_band, lower_band) lists
        """
        if len(prices) < period:
            none_list = [None] * len(prices)
            return none_list, none_list, none_list

        upper_band = [None] * (period - 1)
        middle_band = [None] * (period - 1)
        lower_band = [None] * (period - 1)

        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            sma = sum(window) / period
            variance = sum((x - sma) ** 2 for x in window) / period
            std = variance**0.5

            upper_band.append(sma + (std_dev * std))
            middle_band.append(sma)
            lower_band.append(sma - (std_dev * std))

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            Tuple of (macd_line, signal_line, histogram) lists
        """
        fast_ema = TechnicalIndicators.calculate_ema(prices, fast_period)
        slow_ema = TechnicalIndicators.calculate_ema(prices, slow_period)

        # Calculate MACD line
        macd_line = []
        for i in range(len(prices)):
            if fast_ema[i] is not None and slow_ema[i] is not None:
                macd_line.append(fast_ema[i] - slow_ema[i])
            else:
                macd_line.append(None)

        # Calculate signal line (EMA of MACD line)
        macd_values = [x for x in macd_line if x is not None]
        if len(macd_values) >= signal_period:
            signal_ema = TechnicalIndicators.calculate_ema(macd_values, signal_period)
            # Pad with None values to match original length
            signal_line = [None] * (len(macd_line) - len(signal_ema)) + signal_ema
        else:
            signal_line = [None] * len(macd_line)

        # Calculate histogram
        histogram = []
        for i in range(len(macd_line)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)

        return macd_line, signal_line, histogram
