"""
Parameter optimization engine using Optuna for systematic hyperparameter tuning.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import numpy as np
import optuna
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .backtester import Backtester
from .data_reader import DataReader
from .models import BacktestResult, MarketData
from .strategy import Strategy
from .visualization import VisualizationEngine

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DataSplit:
    """Container for train/validation/test data splits."""
    
    train_data: List[MarketData]
    validation_data: List[MarketData]
    test_data: List[MarketData]
    split_dates: Dict[str, datetime]
    split_indices: Dict[str, int]
    
    def __post_init__(self):
        """Validate data split integrity."""
        total_points = len(self.train_data) + len(self.validation_data) + len(self.test_data)
        if total_points == 0:
            raise ValueError("Data split cannot be empty")
        
        # Validate chronological order
        if self.train_data and self.validation_data:
            if self.train_data[-1].timestamp >= self.validation_data[0].timestamp:
                raise ValueError("Training data must end before validation data starts")
        
        if self.validation_data and self.test_data:
            if self.validation_data[-1].timestamp >= self.test_data[0].timestamp:
                raise ValueError("Validation data must end before test data starts")


@dataclass
class OptimizationResult:
    """Container for optimization results."""
    
    strategy_name: str
    best_parameters: Dict[str, Any]
    best_metric_value: float
    optimization_metric: str
    n_trials: int
    study: optuna.Study
    train_result: BacktestResult
    validation_result: BacktestResult
    test_result: BacktestResult
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def improvement_summary(self) -> Dict[str, Any]:
        """Get summary of optimization improvements."""
        return {
            'best_parameters': self.best_parameters,
            'best_metric_value': self.best_metric_value,
            'optimization_metric': self.optimization_metric,
            'n_trials_completed': self.n_trials,
            'train_performance': {
                'total_return': self.train_result.total_return,
                'sharpe_ratio': self.train_result.sharpe_ratio,
                'max_drawdown': self.train_result.max_drawdown,
                'win_rate': self.train_result.win_rate
            },
            'validation_performance': {
                'total_return': self.validation_result.total_return,
                'sharpe_ratio': self.validation_result.sharpe_ratio,
                'max_drawdown': self.validation_result.max_drawdown,
                'win_rate': self.validation_result.win_rate
            },
            'test_performance': {
                'total_return': self.test_result.total_return,
                'sharpe_ratio': self.test_result.sharpe_ratio,
                'max_drawdown': self.test_result.max_drawdown,
                'win_rate': self.test_result.win_rate
            }
        }


@dataclass
class ComparisonResult:
    """Container for before/after optimization comparison."""
    
    strategy_name: str
    before_params: Dict[str, Any]
    after_params: Dict[str, Any]
    before_result: BacktestResult
    after_result: BacktestResult
    improvement_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate improvement metrics."""
        self.improvement_metrics = {
            'total_return_improvement': self.after_result.total_return - self.before_result.total_return,
            'sharpe_improvement': (self.after_result.sharpe_ratio or 0) - (self.before_result.sharpe_ratio or 0),
            'drawdown_improvement': self.before_result.max_drawdown - self.after_result.max_drawdown,  # Positive is better
            'win_rate_improvement': self.after_result.win_rate - self.before_result.win_rate
        }


class DataSplitter:
    """Handles chronological data splitting for time series backtesting."""
    
    @staticmethod
    def split_data(
        market_data: List[MarketData],
        train_ratio: float = 0.6,
        validation_ratio: float = 0.2,
        test_ratio: float = 0.2
    ) -> DataSplit:
        """
        Split market data chronologically into train/validation/test sets.
        
        Args:
            market_data: List of market data points (must be chronologically ordered)
            train_ratio: Proportion of data for training (default: 0.6)
            validation_ratio: Proportion of data for validation (default: 0.2)
            test_ratio: Proportion of data for testing (default: 0.2)
            
        Returns:
            DataSplit object containing the three datasets
            
        Raises:
            ValueError: If ratios don't sum to 1.0 or data is insufficient
        """
        # Validate ratios
        ratios = [train_ratio, validation_ratio, test_ratio]
        if not DataSplitter.validate_split_ratios(ratios):
            raise ValueError("Split ratios must sum to 1.0 and be positive")
        
        # Validate minimum data requirements
        total_points = len(market_data)
        min_required = 100  # Minimum total data points
        if total_points < min_required:
            raise ValueError(f"Insufficient data: {total_points} points, minimum required: {min_required}")
        
        # Calculate split indices
        train_end = int(total_points * train_ratio)
        validation_end = int(total_points * (train_ratio + validation_ratio))
        
        # Ensure each split has minimum data
        min_split_size = 30
        if train_end < min_split_size:
            raise ValueError(f"Training split too small: {train_end} points, minimum: {min_split_size}")
        if (validation_end - train_end) < min_split_size:
            raise ValueError(f"Validation split too small: {validation_end - train_end} points, minimum: {min_split_size}")
        if (total_points - validation_end) < min_split_size:
            raise ValueError(f"Test split too small: {total_points - validation_end} points, minimum: {min_split_size}")
        
        # Split the data
        train_data = market_data[:train_end]
        validation_data = market_data[train_end:validation_end]
        test_data = market_data[validation_end:]
        
        # Create split metadata
        split_dates = {
            'train_start': train_data[0].timestamp,
            'train_end': train_data[-1].timestamp,
            'validation_start': validation_data[0].timestamp,
            'validation_end': validation_data[-1].timestamp,
            'test_start': test_data[0].timestamp,
            'test_end': test_data[-1].timestamp
        }
        
        split_indices = {
            'train_end': train_end,
            'validation_end': validation_end,
            'total_points': total_points
        }
        
        return DataSplit(
            train_data=train_data,
            validation_data=validation_data,
            test_data=test_data,
            split_dates=split_dates,
            split_indices=split_indices
        )
    
    @staticmethod
    def validate_split_ratios(ratios: List[float]) -> bool:
        """
        Validate that split ratios are positive and sum to 1.0.
        
        Args:
            ratios: List of ratio values
            
        Returns:
            True if ratios are valid, False otherwise
        """
        if not ratios or len(ratios) == 0:
            return False
        
        # Check if all ratios are positive
        if any(ratio <= 0 for ratio in ratios):
            return False
        
        # Check if ratios sum to approximately 1.0 (allow small floating point errors)
        total = sum(ratios)
        return abs(total - 1.0) < 1e-10


class Optimizer:
    """
    Main optimization engine for systematic hyperparameter tuning using Optuna.
    """
    
    def __init__(
        self,
        data_reader: DataReader,
        data_source: str,
        train_ratio: float = 0.6,
        validation_ratio: float = 0.2,
        test_ratio: float = 0.2,
        initial_capital: float = 100000.0
    ):
        """
        Initialize optimizer with data source and configuration.
        
        Args:
            data_reader: DataReader instance for loading market data
            data_source: Path to market data source
            train_ratio: Proportion of data for training (default: 0.6)
            validation_ratio: Proportion of data for validation (default: 0.2)
            test_ratio: Proportion of data for testing (default: 0.2)
            initial_capital: Initial capital for backtesting (default: 100000.0)
        """
        self.data_reader = data_reader
        self.data_source = data_source
        self.train_ratio = train_ratio
        self.validation_ratio = validation_ratio
        self.test_ratio = test_ratio
        self.initial_capital = initial_capital
        
        # Load and split data
        logger.info(f"Loading market data from {data_source}")
        self.market_data = self.data_reader.load_data(data_source)
        logger.info(f"Loaded {len(self.market_data)} data points")
        
        # Split data
        self.data_split = DataSplitter.split_data(
            self.market_data, train_ratio, validation_ratio, test_ratio
        )
        
        logger.info(f"Data split - Train: {len(self.data_split.train_data)}, "
                   f"Validation: {len(self.data_split.validation_data)}, "
                   f"Test: {len(self.data_split.test_data)}")
        
        # Initialize visualization engine
        self.viz_engine = VisualizationEngine()
    
    def optimize_strategy(
        self,
        strategy_class: Type[Strategy],
        parameter_space: Dict[str, Tuple],
        n_trials: int = 100,
        optimization_metric: str = 'sharpe_ratio',
        study_name: Optional[str] = None,
        random_state: Optional[int] = None
    ) -> OptimizationResult:
        """
        Optimize strategy parameters using Optuna.
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: Dictionary defining parameter search space
            n_trials: Number of optimization trials (default: 100)
            optimization_metric: Metric to optimize (default: 'sharpe_ratio')
            study_name: Optional name for the Optuna study
            random_state: Random seed for reproducibility
            
        Returns:
            OptimizationResult containing optimization results
        """
        if study_name is None:
            study_name = f"{strategy_class.__name__}_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting optimization for {strategy_class.__name__}")
        logger.info(f"Parameter space: {parameter_space}")
        logger.info(f"Optimization metric: {optimization_metric}")
        logger.info(f"Number of trials: {n_trials}")
        
        # Create Optuna study
        direction = 'maximize' if optimization_metric in ['sharpe_ratio', 'total_return', 'win_rate'] else 'minimize'
        study = optuna.create_study(
            direction=direction,
            study_name=study_name,
            sampler=optuna.samplers.TPESampler(seed=random_state) if random_state else None
        )
        
        # Define objective function
        def objective(trial: optuna.Trial) -> float:
            return self._objective_function(trial, strategy_class, parameter_space, optimization_metric)
        
        # Run optimization
        study.optimize(objective, n_trials=n_trials)
        
        # Get best parameters and create final results
        best_params = study.best_params
        logger.info(f"Optimization completed. Best parameters: {best_params}")
        logger.info(f"Best {optimization_metric}: {study.best_value}")
        
        # Run final backtests with best parameters
        train_result = self._run_backtest_with_params(strategy_class, best_params, self.data_split.train_data)
        validation_result = self._run_backtest_with_params(strategy_class, best_params, self.data_split.validation_data)
        test_result = self._run_backtest_with_params(strategy_class, best_params, self.data_split.test_data)
        
        # Create optimization history
        optimization_history = []
        for trial in study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                optimization_history.append({
                    'trial_number': trial.number,
                    'value': trial.value,
                    'params': trial.params,
                    'datetime': trial.datetime_start
                })
        
        return OptimizationResult(
            strategy_name=strategy_class.__name__,
            best_parameters=best_params,
            best_metric_value=study.best_value,
            optimization_metric=optimization_metric,
            n_trials=len(study.trials),
            study=study,
            train_result=train_result,
            validation_result=validation_result,
            test_result=test_result,
            optimization_history=optimization_history
        )
    
    def _objective_function(
        self,
        trial: optuna.Trial,
        strategy_class: Type[Strategy],
        parameter_space: Dict[str, Tuple],
        optimization_metric: str
    ) -> float:
        """
        Objective function for Optuna optimization.
        
        Args:
            trial: Optuna trial object
            strategy_class: Strategy class to optimize
            parameter_space: Parameter search space
            optimization_metric: Metric to optimize
            
        Returns:
            Metric value for this trial
        """
        try:
            # Suggest parameters based on parameter space
            params = {}
            for param_name, param_config in parameter_space.items():
                param_type, min_val, max_val = param_config
                
                if param_type == 'int':
                    params[param_name] = trial.suggest_int(param_name, min_val, max_val)
                elif param_type == 'float':
                    params[param_name] = trial.suggest_float(param_name, min_val, max_val)
                elif param_type == 'categorical':
                    params[param_name] = trial.suggest_categorical(param_name, min_val)  # min_val contains choices
                else:
                    raise ValueError(f"Unsupported parameter type: {param_type}")
            
            # Run backtest on training data
            train_result = self._run_backtest_with_params(strategy_class, params, self.data_split.train_data)
            
            # Get metric value
            metric_value = getattr(train_result, optimization_metric, None)
            if metric_value is None:
                logger.warning(f"Metric {optimization_metric} not found in backtest result")
                return float('-inf') if optimization_metric in ['sharpe_ratio', 'total_return', 'win_rate'] else float('inf')
            
            return float(metric_value)
            
        except Exception as e:
            logger.error(f"Error in trial {trial.number}: {str(e)}")
            # Return worst possible value for this optimization direction
            return float('-inf') if optimization_metric in ['sharpe_ratio', 'total_return', 'win_rate'] else float('inf')
    
    def _run_backtest_with_params(
        self,
        strategy_class: Type[Strategy],
        params: Dict[str, Any],
        market_data: List[MarketData]
    ) -> BacktestResult:
        """
        Run backtest with given parameters on specified data.
        
        Args:
            strategy_class: Strategy class to instantiate
            params: Parameters for strategy initialization
            market_data: Market data for backtesting
            
        Returns:
            BacktestResult from the backtest
        """
        # Create proper LOT configuration for crypto trading
        from .config import ConfigFactory
        lot_config = ConfigFactory.create_crypto_lot_config()
        
        # Create strategy instance with parameters and LOT config
        strategy = strategy_class.create_from_params(initial_capital=self.initial_capital, lot_config=lot_config, **params)
        
        # Create backtester and run backtest
        backtester = Backtester(initial_capital=self.initial_capital)
        
        # Set the market data and strategy directly
        backtester.market_data = market_data
        backtester.strategy = strategy
        backtester.strategy.reset()
        backtester.portfolio_manager.reset()
        
        # Run the backtesting loop with proper portfolio tracking
        total_steps = len(market_data)
        
        for i, current_data in enumerate(market_data):
            backtester.current_data_index = i
            
            # Get historical data up to current point
            historical_data = market_data[:i+1]
            
            # Generate trading signal
            order = strategy.generate_signal(current_data, historical_data[:-1])
            
            # Process order if generated
            if order is not None:
                trade = backtester.portfolio_manager.process_order(order, current_data)
                
                # Update strategy position tracking if trade executed
                if trade is not None:
                    strategy.update_position(order, trade.entry_price)
                    
                    # Update strategy cash and position for compatibility
                    if hasattr(strategy, "cash") and hasattr(strategy, "current_position"):
                        # Update strategy's cash and position tracking
                        strategy.cash = backtester.portfolio_manager.cash
                        
                        # Calculate total position from portfolio
                        total_position = 0
                        for position in backtester.portfolio_manager.positions.values():
                            total_position += position.quantity
                        strategy.current_position = total_position
            
            # Record portfolio snapshot
            current_prices = {"DEFAULT": current_data.close}
            backtester.portfolio_manager.record_portfolio_snapshot(
                current_data.timestamp, current_prices
            )
        
        # Generate and return results
        return backtester._generate_results()
    
    def compare_before_after(
        self,
        strategy_class: Type[Strategy],
        default_params: Dict[str, Any],
        optimized_params: Dict[str, Any]
    ) -> ComparisonResult:
        """
        Compare strategy performance before and after optimization.
        
        Args:
            strategy_class: Strategy class to compare
            default_params: Default/original parameters
            optimized_params: Optimized parameters
            
        Returns:
            ComparisonResult containing comparison metrics
        """
        logger.info(f"Comparing {strategy_class.__name__} before and after optimization")
        
        # Run backtests with both parameter sets on test data
        before_result = self._run_backtest_with_params(strategy_class, default_params, self.data_split.test_data)
        after_result = self._run_backtest_with_params(strategy_class, optimized_params, self.data_split.test_data)
        
        return ComparisonResult(
            strategy_name=strategy_class.__name__,
            before_params=default_params,
            after_params=optimized_params,
            before_result=before_result,
            after_result=after_result
        )
    
    def create_optimization_comparison_chart(
        self,
        comparison_result: ComparisonResult,
        save_path: Optional[str] = None
    ) -> 'plt.Figure':
        """
        Create optimization before/after comparison chart using VisualizationEngine.
        
        Args:
            comparison_result: Result from compare_before_after
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        # Prepare comparison data for VisualizationEngine
        comparison_data = {
            f'{comparison_result.strategy_name}_Default': comparison_result.before_result,
            f'{comparison_result.strategy_name}_Optimized': comparison_result.after_result
        }
        
        # Create comparison chart using existing visualization engine
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        title = f'{comparison_result.strategy_name} Strategy: Before vs After Optimization'
        
        fig = self.viz_engine.compare_strategies_chart(
            comparison_data,
            metrics=metrics,
            title=title,
            save_path=save_path
        )
        
        if save_path:
            logger.info(f"Optimization comparison chart saved: {save_path}")
        
        return fig
    
    def create_optimization_history_chart(
        self,
        optimization_result: OptimizationResult,
        save_path: Optional[str] = None
    ) -> 'plt.Figure':
        """
        Create optimization history chart showing metric progression over trials using matplotlib.
        
        Args:
            optimization_result: Result from optimization
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        import matplotlib.pyplot as plt
        
        history = optimization_result.optimization_history
        if not history:
            raise ValueError("No optimization history available")
        
        # Extract data for plotting
        trial_numbers = [h['trial_number'] for h in history]
        values = [h['value'] for h in history]
        
        # Calculate best value so far for each trial
        best_values = []
        current_best = values[0]
        direction = 'maximize' if optimization_result.optimization_metric in ['sharpe_ratio', 'total_return', 'win_rate'] else 'minimize'
        
        for value in values:
            if direction == 'maximize':
                current_best = max(current_best, value)
            else:
                current_best = min(current_best, value)
            best_values.append(current_best)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f'{optimization_result.strategy_name} Optimization History', fontsize=16, fontweight='bold')
        
        # Plot trial values
        ax1.scatter(trial_numbers, values, alpha=0.6, color='lightblue', s=30, label='Trial Values')
        ax1.set_title(f'{optimization_result.optimization_metric.replace("_", " ").title()} per Trial')
        ax1.set_xlabel('Trial Number')
        ax1.set_ylabel(optimization_result.optimization_metric.replace("_", " ").title())
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot best values progression
        ax2.plot(trial_numbers, best_values, color='red', linewidth=2, label='Best Value So Far')
        ax2.set_title(f'Best {optimization_result.optimization_metric.replace("_", " ").title()} Convergence')
        ax2.set_xlabel('Trial Number')
        ax2.set_ylabel(optimization_result.optimization_metric.replace("_", " ").title())
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Add final best value annotation
        final_best = best_values[-1]
        ax2.annotate(f'Final Best: {final_best:.4f}', 
                    xy=(trial_numbers[-1], final_best), 
                    xytext=(trial_numbers[-1] - len(trial_numbers)*0.2, final_best),
                    arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                    fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Optimization history chart saved: {save_path}")
        
        return fig
    
    def get_data_split_info(self) -> Dict[str, Any]:
        """
        Get information about the data split.
        
        Returns:
            Dictionary with data split information
        """
        return {
            'total_data_points': len(self.market_data),
            'train_points': len(self.data_split.train_data),
            'validation_points': len(self.data_split.validation_data),
            'test_points': len(self.data_split.test_data),
            'split_ratios': {
                'train': self.train_ratio,
                'validation': self.validation_ratio,
                'test': self.test_ratio
            },
            'split_dates': self.data_split.split_dates,
            'date_range': {
                'start': self.market_data[0].timestamp,
                'end': self.market_data[-1].timestamp
            }
        }
    
    def create_optimization_dashboard(
        self,
        optimization_result: OptimizationResult,
        comparison_result: ComparisonResult,
        save_path: Optional[str] = None
    ) -> 'plt.Figure':
        """
        Create comprehensive optimization dashboard showing optimized strategy performance with proper signals.
        
        Args:
            optimization_result: Result from optimization
            comparison_result: Result from before/after comparison
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        try:
            logger.info(f"Creating optimization dashboard for {optimization_result.strategy_name}")
            
            # Create a backtester instance with optimized parameters for dashboard
            from .backtester import Backtester

            # Create strategy instance with optimized parameters
            strategy = optimization_result.strategy_name
            strategy_class = None
            
            # Import strategy classes dynamically
            if optimization_result.strategy_name == 'MovingAverageStrategy':
                from .strategy import MovingAverageStrategy
                strategy_class = MovingAverageStrategy
            elif optimization_result.strategy_name == 'RSIStrategy':
                from .strategy import RSIStrategy
                strategy_class = RSIStrategy
            elif optimization_result.strategy_name == 'RSIAveragingStrategy':
                from .strategy import RSIAveragingStrategy
                strategy_class = RSIAveragingStrategy
            
            if strategy_class is None:
                raise ValueError(f"Unknown strategy: {optimization_result.strategy_name}")
            
            # Create proper LOT configuration for crypto trading
            from .config import ConfigFactory
            lot_config = ConfigFactory.create_crypto_lot_config()
            
            # Create optimized strategy instance with LOT config
            optimized_strategy = strategy_class.create_from_params(
                initial_capital=self.initial_capital, 
                lot_config=lot_config,
                **optimization_result.best_parameters
            )
            
            logger.info(f"Created optimized strategy with parameters: {optimization_result.best_parameters}")
            
            # Create backtester and run with optimized strategy using the standard run_backtest method
            backtester = Backtester(initial_capital=self.initial_capital)
            
            # Use a temporary data source file for the test data
            import csv
            import tempfile

            # Create temporary CSV file with test data using correct column names and unix timestamps
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
                writer = csv.writer(temp_file)
                writer.writerow(['time', 'open', 'high', 'low', 'close', 'Volume'])
                
                for data in self.data_split.test_data:
                    # Convert datetime to unix timestamp
                    unix_timestamp = int(data.timestamp.timestamp())
                    writer.writerow([
                        unix_timestamp,
                        data.open,
                        data.high,
                        data.low,
                        data.close,
                        data.volume
                    ])
                
                temp_file_path = temp_file.name
            
            try:
                # Run backtest using the standard method
                backtester.run_backtest(
                    self.data_reader,
                    optimized_strategy,
                    temp_file_path,
                    f"{optimization_result.strategy_name}_Optimized"
                )
                
                logger.info(f"Backtest completed successfully")
                
                # Create single dashboard chart with signals and optimized parameters
                strategy_name = f"{optimization_result.strategy_name}_Optimized"
                
                # Add optimized parameters to strategy name for display
                param_str = ", ".join([f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" 
                                     for k, v in optimization_result.best_parameters.items()])
                strategy_display_name = f"{strategy_name} ({param_str})"
                
                # Create the dashboard using create_performance_dashboard method
                fig = self.viz_engine.create_performance_dashboard(
                    backtester=backtester,
                    market_data=self.data_split.test_data,
                    strategy_name=strategy_display_name,
                    save_path=save_path
                )
                
                if save_path:
                    logger.info(f"Optimization dashboard saved: {save_path}")
                
                return fig
                
            finally:
                # Clean up temporary file
                import os
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error creating optimization dashboard: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return empty figure as fallback
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f'Error creating dashboard:\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
            ax.set_title('Dashboard Creation Error')
            
            if save_path:
                fig.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Error dashboard saved: {save_path}")
            
            return fig
    
    def create_strategy_comparison_dashboard(
        self,
        comparison_result: ComparisonResult,
        save_path: Optional[str] = None
    ) -> 'plt.Figure':
        """
        Create strategy comparison dashboard showing before vs after optimization.
        
        Args:
            comparison_result: Result from compare_before_after
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        # Prepare comparison data for VisualizationEngine
        comparison_data = {
            f'{comparison_result.strategy_name}_Default': comparison_result.before_result,
            f'{comparison_result.strategy_name}_Optimized': comparison_result.after_result
        }
        
        # Create strategy comparison dashboard
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        title = f'{comparison_result.strategy_name} Strategy Comparison Dashboard'
        
        fig = self.viz_engine.compare_strategies_chart(
            comparison_data,
            metrics=metrics,
            title=title,
            save_path=save_path
        )
        
        if save_path:
            logger.info(f"Strategy comparison dashboard saved: {save_path}")
        
        return fig

    def get_optimization_summary(self) -> 'pd.DataFrame':
        """Get summary of all optimization results."""
        import pandas as pd

        # This method would need to track optimization results
        # For now, return empty DataFrame as placeholder
        return pd.DataFrame()