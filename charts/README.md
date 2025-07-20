# Charts Directory

This directory contains generated visualization charts from backtesting results.

## Chart Types

- **Price Charts**: Show price movements with entry/exit signals
- **Equity Curves**: Display portfolio value over time
- **Drawdown Analysis**: Visualize portfolio drawdowns
- **Performance Dashboards**: Comprehensive performance overview
- **Strategy Comparisons**: Compare multiple strategies

## Usage

Charts are automatically generated when running backtests with visualization enabled:

```python
from backtester.visualization import VisualizationEngine

viz_engine = VisualizationEngine()
fig = viz_engine.create_price_chart_with_signals(
    market_data, trades, 
    save_path="charts/my_strategy_signals.png"
)
```

Charts are saved in PNG format with high resolution (300 DPI) suitable for reports and presentations.