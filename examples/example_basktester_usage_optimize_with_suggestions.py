#!/usr/bin/env python3
"""
Example usage of backtester optimization with initial parameter suggestions.

This example demonstrates how to use the Optuna optimization engine with:
1. User-provided initial parameter suggestions
2. Strategy default parameters as suggestions
3. Automatic generation of common starting points

The suggestion feature helps improve optimization efficiency by starting
with known good parameter combinations.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the Python path to import backtester
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backtester import (CryptoDataReader, MovingAverageStrategy, Optimizer,
                        RSIStrategy)


def main():
    """Main function demonstrating optimization with suggestions."""
    print("🚀 Backtester Optimization with Suggestions Example")
    print("=" * 60)
    
    # Configuration
    data_file = "pricedata/BITFLYER_BTCJPY_1D_c51ab.csv"
    initial_capital = 100000.0
    
    # Check if data file exists
    if not os.path.exists(data_file):
        print(f"❌ Error: Data file not found: {data_file}")
        print("Please ensure the data file exists in the pricedata directory.")
        return
    
    # Initialize data reader and optimizer
    print(f"📊 Loading data from: {data_file}")
    data_reader = CryptoDataReader()
    
    try:
        optimizer = Optimizer(
            data_reader=data_reader,
            data_source=data_file,
            train_ratio=0.6,
            validation_ratio=0.2,
            test_ratio=0.2,
            initial_capital=initial_capital
        )
        print(f"✅ Optimizer initialized successfully")
        print(f"   Train/Validation/Test split: 60%/20%/20%")
        
    except Exception as e:
        print(f"❌ Error initializing optimizer: {e}")
        return
    
    # Example 1: Moving Average Strategy with User Suggestions
    print("\n" + "=" * 60)
    print("📈 Example 1: Moving Average Strategy with User Suggestions")
    print("=" * 60)
    
    # Define parameter space for Moving Average strategy
    ma_parameter_space = {
        'short_window': ('int', 5, 50),
        'long_window': ('int', 20, 200),
        'position_lots': ('float', 0.1, 2.0)
    }
    
    # User-provided initial suggestions based on domain knowledge
    ma_initial_suggestions = [
        # Classic golden cross parameters
        {'short_window': 50, 'long_window': 200, 'position_lots': 1.0},
        # Short-term trading parameters
        {'short_window': 5, 'long_window': 20, 'position_lots': 0.5},
        # Medium-term parameters
        {'short_window': 10, 'long_window': 50, 'position_lots': 1.5},
        # Conservative approach
        {'short_window': 20, 'long_window': 100, 'position_lots': 0.8},
    ]
    
    print(f"🎯 User suggestions: {len(ma_initial_suggestions)} parameter sets")
    for i, suggestion in enumerate(ma_initial_suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    try:
        print(f"\n🔍 Starting optimization with {len(ma_initial_suggestions)} user suggestions...")
        
        ma_result = optimizer.optimize_strategy(
            strategy_class=MovingAverageStrategy,
            parameter_space=ma_parameter_space,
            n_trials=50,  # Reduced for example
            optimization_metric='sharpe_ratio',
            initial_suggestions=ma_initial_suggestions,
            use_default_suggestions=True,  # Also include strategy defaults
            random_state=42
        )
        
        print(f"✅ Moving Average optimization completed!")
        print(f"   Best Sharpe Ratio: {ma_result.best_metric_value:.4f}")
        print(f"   Best Parameters: {ma_result.best_parameters}")
        print(f"   Total Trials: {ma_result.n_trials}")
        
        # Show performance comparison
        print(f"\n📊 Performance Summary:")
        print(f"   Train Sharpe: {ma_result.train_result.sharpe_ratio:.4f}")
        print(f"   Validation Sharpe: {ma_result.validation_result.sharpe_ratio:.4f}")
        print(f"   Test Sharpe: {ma_result.test_result.sharpe_ratio:.4f}")
        
    except Exception as e:
        print(f"❌ Error during Moving Average optimization: {e}")
    
    # Example 2: RSI Strategy with Default Suggestions Only
    print("\n" + "=" * 60)
    print("📊 Example 2: RSI Strategy with Default Suggestions Only")
    print("=" * 60)
    
    # Define parameter space for RSI strategy
    rsi_parameter_space = {
        'rsi_period': ('int', 5, 30),
        'oversold_threshold': ('float', 20, 40),
        'overbought_threshold': ('float', 60, 80)
    }
    
    try:
        print(f"🔍 Starting RSI optimization with default suggestions only...")
        
        rsi_result = optimizer.optimize_strategy(
            strategy_class=RSIStrategy,
            parameter_space=rsi_parameter_space,
            n_trials=30,  # Reduced for example
            optimization_metric='total_return',
            initial_suggestions=None,  # No user suggestions
            use_default_suggestions=True,  # Use strategy defaults + common suggestions
            random_state=42
        )
        
        print(f"✅ RSI optimization completed!")
        print(f"   Best Total Return: {rsi_result.best_metric_value:.4f}")
        print(f"   Best Parameters: {rsi_result.best_parameters}")
        print(f"   Total Trials: {rsi_result.n_trials}")
        
        # Show performance comparison
        print(f"\n📊 Performance Summary:")
        print(f"   Train Return: {rsi_result.train_result.total_return:.4f}")
        print(f"   Validation Return: {rsi_result.validation_result.total_return:.4f}")
        print(f"   Test Return: {rsi_result.test_result.total_return:.4f}")
        
    except Exception as e:
        print(f"❌ Error during RSI optimization: {e}")
    
    # Example 3: Comparison of optimization with and without suggestions
    print("\n" + "=" * 60)
    print("🔬 Example 3: Comparison - With vs Without Suggestions")
    print("=" * 60)
    
    try:
        print(f"🔍 Running optimization WITHOUT suggestions...")
        
        # Run optimization without suggestions
        ma_no_suggestions = optimizer.optimize_strategy(
            strategy_class=MovingAverageStrategy,
            parameter_space=ma_parameter_space,
            n_trials=20,  # Small number for comparison
            optimization_metric='sharpe_ratio',
            initial_suggestions=None,
            use_default_suggestions=False,  # No suggestions at all
            random_state=42
        )
        
        print(f"🔍 Running optimization WITH suggestions...")
        
        # Run optimization with suggestions
        ma_with_suggestions = optimizer.optimize_strategy(
            strategy_class=MovingAverageStrategy,
            parameter_space=ma_parameter_space,
            n_trials=20,  # Same number for fair comparison
            optimization_metric='sharpe_ratio',
            initial_suggestions=ma_initial_suggestions[:2],  # Use first 2 suggestions
            use_default_suggestions=True,
            random_state=42
        )
        
        print(f"\n📈 Comparison Results:")
        print(f"   Without Suggestions - Best Sharpe: {ma_no_suggestions.best_metric_value:.4f}")
        print(f"   With Suggestions    - Best Sharpe: {ma_with_suggestions.best_metric_value:.4f}")
        
        improvement = ma_with_suggestions.best_metric_value - ma_no_suggestions.best_metric_value
        print(f"   Improvement: {improvement:+.4f} ({improvement/abs(ma_no_suggestions.best_metric_value)*100:+.1f}%)")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Optimization with Suggestions Example Completed!")
    print("=" * 60)
    
    print(f"\n💡 Key Benefits of Using Suggestions:")
    print(f"   • Faster convergence to good solutions")
    print(f"   • Incorporates domain knowledge and experience")
    print(f"   • Reduces random exploration in poor parameter regions")
    print(f"   • Can start with known working configurations")
    print(f"   • Automatic generation of conservative/moderate/aggressive starting points")


if __name__ == "__main__":
    main()