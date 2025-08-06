"""
Example usage of the parameter optimization system.

This script demonstrates how to use the Optimizer class to optimize
trading strategy parameters using Optuna with proper data splitting.
"""

import os
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

# Add the parent directory to the Python path to import backtester
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backtester.crypto_data_reader import CryptoDataReader
from backtester.optimizer import Optimizer
from backtester.strategy import MovingAverageStrategy, RSIStrategy


def main():
    """Run parameter optimization example."""
    print("=== Parameter Optimization Example ===\n")
    
    # Load data
    print("Loading data...")
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    
    if not os.path.exists(data_file):
        print(f"Error: Data file {data_file} not found!")
        print("Please ensure the data file exists in the pricedata directory.")
        return
    
    # Initialize data reader and optimizer
    data_reader = CryptoDataReader()
    
    print("\nInitializing optimizer...")
    optimizer = Optimizer(
        data_reader=data_reader,
        data_source=data_file,
        initial_capital=1000000
    )
    
    # Display data split information
    split_info = optimizer.get_data_split_info()
    print(f"Loaded {split_info['total_data_points']} data points")
    print(f"Data split - Train: {split_info['train_points']}, Validation: {split_info['validation_points']}, Test: {split_info['test_points']}")
    print(f"Date range: {split_info['date_range']['start']} to {split_info['date_range']['end']}")
    
    # Create output directory
    output_dir = "charts"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define strategies to optimize
    strategies_to_optimize = [
        {
            'name': 'MovingAverage',
            'class': MovingAverageStrategy,
            'parameter_space': MovingAverageStrategy.get_parameter_space(),
            'default_params': MovingAverageStrategy.get_default_parameters()
        },
        {
            'name': 'RSI',
            'class': RSIStrategy,
            'parameter_space': RSIStrategy.get_parameter_space(),
            'default_params': RSIStrategy.get_default_parameters()
        }
    ]
    
    optimization_results = {}
    
    for strategy_config in strategies_to_optimize:
        strategy_name = strategy_config['name']
        strategy_class = strategy_config['class']
        parameter_space = strategy_config['parameter_space']
        default_params = strategy_config['default_params']
        
        print(f"\n{'='*50}")
        print(f"Optimizing {strategy_name} Strategy")
        print(f"{'='*50}")
        print(f"Parameter space: {parameter_space}")
        print(f"Default parameters: {default_params}")
        
        try:
            # Prepare initial suggestions based on strategy type
            initial_suggestions = []
            if strategy_name == 'MovingAverage':
                # Add some well-known MA combinations
                initial_suggestions = [
                    {'short_window': 50, 'long_window': 200, 'position_lots': 1.0},  # Golden cross
                    {'short_window': 5, 'long_window': 20, 'position_lots': 0.5},    # Short-term
                    {'short_window': 10, 'long_window': 30, 'position_lots': 1.0},   # Default-like
                ]
            elif strategy_name == 'RSI':
                # Add some common RSI configurations
                initial_suggestions = [
                    {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70},  # Classic
                    {'rsi_period': 21, 'oversold_threshold': 25, 'overbought_threshold': 75},  # Conservative
                    {'rsi_period': 7, 'oversold_threshold': 35, 'overbought_threshold': 65},   # Aggressive
                ]
            
            print(f"Using {len(initial_suggestions)} initial suggestions")
            
            # Run optimization with suggestions and fixed seed for reproducibility
            result = optimizer.optimize_strategy(
                strategy_class=strategy_class,
                parameter_space=parameter_space,
                n_trials=50,  # Reduced for faster example
                optimization_metric='sharpe_ratio',
                random_state=42,  # Fixed seed for reproducible results
                initial_suggestions=initial_suggestions,
                use_default_suggestions=True  # Also include strategy defaults
            )
            
            optimization_results[strategy_name] = result
            
            print(f"\nOptimization completed!")
            print(f"Best parameters: {result.best_parameters}")
            print(f"Best {result.optimization_metric}: {result.best_metric_value:.4f}")
            print(f"Number of trials: {result.n_trials}")
            
            # Print performance metrics
            print(f"\nTrain performance:")
            print(f"  Total return: {result.train_result.total_return:.2%}")
            print(f"  Sharpe ratio: {result.train_result.sharpe_ratio:.4f}" if result.train_result.sharpe_ratio else "  Sharpe ratio: N/A")
            print(f"  Max drawdown: {result.train_result.max_drawdown:.2%}")
            print(f"  Win rate: {result.train_result.win_rate:.2%}")
            
            print(f"\nValidation performance:")
            print(f"  Total return: {result.validation_result.total_return:.2%}")
            print(f"  Sharpe ratio: {result.validation_result.sharpe_ratio:.4f}" if result.validation_result.sharpe_ratio else "  Sharpe ratio: N/A")
            print(f"  Max drawdown: {result.validation_result.max_drawdown:.2%}")
            print(f"  Win rate: {result.validation_result.win_rate:.2%}")
            
            print(f"\nTest performance:")
            print(f"  Total return: {result.test_result.total_return:.2%}")
            print(f"  Sharpe ratio: {result.test_result.sharpe_ratio:.4f}" if result.test_result.sharpe_ratio else "  Sharpe ratio: N/A")
            print(f"  Max drawdown: {result.test_result.max_drawdown:.2%}")
            print(f"  Win rate: {result.test_result.win_rate:.2%}")
            
            # Generate optimization history plot
            print(f"\nGenerating optimization plots...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = os.path.join(output_dir, f"{strategy_name}_optimization_{timestamp}.png")
            
            fig = optimizer.create_optimization_history_chart(result, save_path=plot_path)
            plt.close(fig)  # Close to free memory
            print(f"Optimization plot saved to: {plot_path}")
            
            # Generate performance comparison
            print(f"\nGenerating performance comparison...")
            comparison_path = os.path.join(output_dir, f"{strategy_name}_comparison_{timestamp}.png")
            comparison_result = optimizer.compare_before_after(
                strategy_class=strategy_class,
                default_params=default_params,
                optimized_params=result.best_parameters
            )
            
            # Create comparison visualization using the new method
            fig = optimizer.create_optimization_comparison_chart(
                comparison_result,
                save_path=comparison_path
            )
            plt.close(fig)  # Close to free memory
            
            print(f"Comparison plot saved to: {comparison_path}")
            
            # Generate optimized strategy dashboard (single comprehensive chart)
            print(f"\nGenerating optimized strategy dashboard...")
            optimized_dashboard_path = os.path.join(output_dir, f"{strategy_name}_optimized_dashboard_{timestamp}.png")
            fig = optimizer.create_optimization_dashboard(
                result,
                comparison_result,
                save_path=optimized_dashboard_path
            )
            plt.close(fig)  # Close to free memory
            print(f"Optimized strategy dashboard saved to: {optimized_dashboard_path}")
            
            # Print improvement summary
            print(f"\nImprovement Summary:")
            for metric, improvement in comparison_result.improvement_metrics.items():
                if 'return' in metric or 'drawdown' in metric:
                    print(f"  {metric}: {improvement:+.2%}")
                elif 'rate' in metric:
                    print(f"  {metric}: {improvement:+.2%}")
                else:
                    print(f"  {metric}: {improvement:+.4f}")
            
        except Exception as e:
            print(f"Error optimizing {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Generate optimization summary
    print(f"\n{'='*50}")
    print("Optimization Summary")
    print(f"{'='*50}")
    
    if optimization_results:
        summary_data = []
        for strategy_name, result in optimization_results.items():
            summary_data.append({
                'Strategy': strategy_name,
                'Best Value': result.best_metric_value,
                'Trials': result.n_trials,
                'Val Sharpe': result.validation_result.sharpe_ratio or 0,
                'Test Sharpe': result.test_result.sharpe_ratio or 0,
                'Test Return': result.test_result.total_return,
                'Best Params': str(result.best_parameters)
            })
        
        summary = pd.DataFrame(summary_data)
        print(summary.to_string(index=False))
        
        # Save summary to CSV
        summary_path = os.path.join(output_dir, f"optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        summary.to_csv(summary_path, index=False)
        print(f"\nSummary saved to: {summary_path}")
    else:
        print("No optimization results to summarize.")
    
    print(f"\n{'='*50}")
    print("Parameter Optimization Complete!")
    print(f"{'='*50}")
    print(f"Results and plots saved to: {output_dir}")
    print("\nKey takeaways:")
    print("1. Check the optimization plots to understand parameter relationships")
    print("2. Compare validation vs test performance to assess overfitting")
    print("3. Use the optimized parameters for live trading with caution")
    print("4. Consider walk-forward optimization for more robust results")


if __name__ == "__main__":
    main()