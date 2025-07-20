"""
Setup script for the Stock Trading Backtester package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core requirements (excluding dev dependencies)
requirements = [
    "pandas>=1.3.0,<3.0.0",
    "numpy>=1.21.0,<2.0.0", 
    "matplotlib>=3.4.0,<4.0.0",
    "TA-Lib>=0.4.0",
    "japanize-matplotlib>=1.1.0",
    "scipy>=1.7.0,<2.0.0",
    "seaborn>=0.11.0,<1.0.0",
]

setup(
    name="stock-trading-backtester",
    version="1.0.0",
    author="Stock Trading Backtester Contributors",
    author_email="contributors@example.com",
    description="High-performance, extensible backtesting framework for stock and cryptocurrency trading strategies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/stock-trading-backtester",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.2.0,<8.0.0",
            "pytest-cov>=2.12.0,<5.0.0",
            "black>=21.0.0,<25.0.0",
            "flake8>=3.9.0,<7.0.0",
            "isort>=5.9.0,<6.0.0",
            "mypy>=0.910,<2.0.0",
            "pre-commit>=2.13.0,<4.0.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0,<2.0.0",
            "ipykernel>=6.0.0,<7.0.0",
        ],
        "profiling": [
            "memory-profiler>=0.58.0,<1.0.0",
            "line-profiler>=3.3.0,<5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "backtester-demo=example_usage:main",
        ],
    },
    include_package_data=True,
    package_data={
        "backtester": ["py.typed"],
    },
    keywords=[
        "trading", "backtesting", "finance", "cryptocurrency", "stocks", 
        "strategy", "portfolio", "analytics", "quantitative", "algotrading"
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-username/stock-trading-backtester/issues",
        "Source": "https://github.com/your-username/stock-trading-backtester",
        "Documentation": "https://github.com/your-username/stock-trading-backtester#readme",
        "Changelog": "https://github.com/your-username/stock-trading-backtester/blob/main/CHANGELOG.md",
        "Contributing": "https://github.com/your-username/stock-trading-backtester/blob/main/CONTRIBUTING.md",
    },
)