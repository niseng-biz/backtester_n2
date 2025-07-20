# Contributing to Stock Trading Backtester

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/your-username/stock-trading-backtester.git
cd stock-trading-backtester

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=backtester

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/examples/
```

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **mypy**: Type checking

```bash
# Format code
black backtester/ tests/

# Check linting
flake8 backtester/ tests/

# Sort imports
isort backtester/ tests/

# Type checking
mypy backtester/
```

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints for all functions and methods
- Write comprehensive docstrings
- Keep functions focused and small
- Use meaningful variable and function names

### Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Include examples in docstrings when helpful
- Update README.md for significant changes

### Testing

- Write tests for new features
- Maintain or improve test coverage
- Use descriptive test names
- Test edge cases and error conditions

### Example Code Style

```python
from typing import List, Optional
from datetime import datetime

def calculate_returns(
    prices: List[float], 
    periods: int = 1
) -> List[Optional[float]]:
    """
    Calculate period-over-period returns.
    
    Args:
        prices: List of price values
        periods: Number of periods for return calculation
        
    Returns:
        List of return values, None for insufficient data
        
    Example:
        >>> prices = [100, 105, 110]
        >>> calculate_returns(prices)
        [None, 0.05, 0.047619...]
    """
    if len(prices) < periods + 1:
        return [None] * len(prices)
    
    returns = [None] * periods
    for i in range(periods, len(prices)):
        ret = (prices[i] - prices[i - periods]) / prices[i - periods]
        returns.append(ret)
    
    return returns
```

## Issue Reporting

### Bug Reports

Great Bug Reports tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

### Feature Requests

We welcome feature requests! Please provide:

- Clear description of the feature
- Use case and motivation
- Possible implementation approach
- Any relevant examples or references

## Project Structure

```
backtester/
├── models.py              # Core data models
├── data_reader.py         # Data loading framework
├── strategy.py            # Trading strategy framework
├── backtester.py          # Main backtesting engine
├── portfolio.py           # Portfolio management
├── analytics.py           # Performance analytics
├── visualization.py       # Chart generation
└── ...

tests/
├── unit/                  # Unit tests
├── integration/           # Integration tests
├── examples/              # Example tests
└── conftest.py           # Test configuration

docs/                      # Documentation
examples/                  # Usage examples
```

## Areas for Contribution

### High Priority

- **Performance Optimization**: Improve backtesting speed for large datasets
- **Additional Strategies**: Implement new trading strategies
- **Risk Management**: Enhanced risk controls and position sizing
- **Data Sources**: Support for additional data formats and sources

### Medium Priority

- **Visualization**: New chart types and interactive features
- **Documentation**: Tutorials, examples, and API documentation
- **Testing**: Increase test coverage and add integration tests
- **Error Handling**: Improve error messages and edge case handling

### Low Priority

- **Code Quality**: Refactoring and optimization
- **Utilities**: Helper functions and convenience methods
- **Examples**: Real-world usage examples and case studies

## Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes for significant contributions
- GitHub contributors page

## Questions?

Don't hesitate to ask questions by:

- Opening an issue with the "question" label
- Starting a discussion in GitHub Discussions
- Reaching out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.