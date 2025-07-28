"""
Financial data model for company financial metrics and ratios.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class FinancialData:
    """
    Data model for company financial data based on yfinance fields.
    
    Attributes:
        symbol: Stock symbol (e.g., 'AAPL')
        fiscal_year: Fiscal year
        fiscal_quarter: Fiscal quarter (1-4, None for annual data)
        
        # Income Statement (from yfinance financials)
        total_revenue: Total revenue
        cost_of_revenue: Cost of revenue
        gross_profit: Gross profit
        operating_expense: Operating expense
        operating_income: Operating income
        pretax_income: Pretax income
        tax_provision: Tax provision
        net_income: Net income
        basic_eps: Basic earnings per share
        diluted_eps: Diluted earnings per share
        
        # Balance Sheet (from yfinance balance_sheet)
        total_assets: Total assets
        total_liabilities_net_minority_interest: Total liabilities
        stockholders_equity: Stockholders' equity
        cash_and_cash_equivalents: Cash and cash equivalents
        total_debt: Total debt
        
        # Cash Flow (from yfinance cashflow)
        operating_cash_flow: Operating cash flow
        free_cash_flow: Free cash flow
        capital_expenditure: Capital expenditure
        
        # Financial Ratios (from yfinance info)
        trailing_pe: Trailing P/E ratio
        forward_pe: Forward P/E ratio
        price_to_book: Price-to-book ratio
        return_on_equity: Return on equity
        return_on_assets: Return on assets
        debt_to_equity: Debt-to-equity ratio
        current_ratio: Current ratio
        quick_ratio: Quick ratio
        gross_margins: Gross margins
        operating_margins: Operating margins
        profit_margins: Profit margins
        
        # Metadata
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
    """
    symbol: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    
    # Income Statement
    total_revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expense: Optional[float] = None
    operating_income: Optional[float] = None
    pretax_income: Optional[float] = None
    tax_provision: Optional[float] = None
    net_income: Optional[float] = None
    basic_eps: Optional[float] = None
    diluted_eps: Optional[float] = None
    
    # Balance Sheet
    total_assets: Optional[float] = None
    total_liabilities_net_minority_interest: Optional[float] = None
    stockholders_equity: Optional[float] = None
    cash_and_cash_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    
    # Financial Ratios
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    gross_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    profit_margins: Optional[float] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """
        Validate the financial data for consistency and correctness.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self.symbol or not isinstance(self.symbol, str):
                return False
            
            if not isinstance(self.fiscal_year, int) or self.fiscal_year < 1900:
                return False
            
            # Check fiscal quarter is valid if provided
            if self.fiscal_quarter is not None:
                if not isinstance(self.fiscal_quarter, int) or not (1 <= self.fiscal_quarter <= 4):
                    return False
            
            # Check that ratios are within reasonable ranges
            if self.return_on_equity is not None and (self.return_on_equity < -1 or self.return_on_equity > 2):  # -100% to 200%
                return False
            
            if self.return_on_assets is not None and (self.return_on_assets < -1 or self.return_on_assets > 1):  # -100% to 100%
                return False
            
            if self.current_ratio is not None and self.current_ratio < 0:
                return False
            
            if self.debt_to_equity is not None and self.debt_to_equity < 0:
                return False
            
            # Check balance sheet equation if all components are available
            if all(x is not None for x in [self.total_assets, self.total_liabilities_net_minority_interest, self.stockholders_equity]):
                if abs(self.total_assets - (self.total_liabilities_net_minority_interest + self.stockholders_equity)) > 0.01:
                    return False
            
            return True
        except (TypeError, ValueError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the financial data to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the financial data
        """
        return {
            'symbol': self.symbol,
            'fiscal_year': self.fiscal_year,
            'fiscal_quarter': self.fiscal_quarter,
            'total_revenue': self.total_revenue,
            'cost_of_revenue': self.cost_of_revenue,
            'gross_profit': self.gross_profit,
            'operating_expense': self.operating_expense,
            'operating_income': self.operating_income,
            'pretax_income': self.pretax_income,
            'tax_provision': self.tax_provision,
            'net_income': self.net_income,
            'basic_eps': self.basic_eps,
            'diluted_eps': self.diluted_eps,
            'total_assets': self.total_assets,
            'total_liabilities_net_minority_interest': self.total_liabilities_net_minority_interest,
            'stockholders_equity': self.stockholders_equity,
            'cash_and_cash_equivalents': self.cash_and_cash_equivalents,
            'total_debt': self.total_debt,
            'operating_cash_flow': self.operating_cash_flow,
            'free_cash_flow': self.free_cash_flow,
            'capital_expenditure': self.capital_expenditure,
            'trailing_pe': self.trailing_pe,
            'forward_pe': self.forward_pe,
            'price_to_book': self.price_to_book,
            'return_on_equity': self.return_on_equity,
            'return_on_assets': self.return_on_assets,
            'debt_to_equity': self.debt_to_equity,
            'current_ratio': self.current_ratio,
            'quick_ratio': self.quick_ratio,
            'gross_margins': self.gross_margins,
            'operating_margins': self.operating_margins,
            'profit_margins': self.profit_margins,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialData':
        """
        Create a FinancialData instance from a dictionary.
        
        Args:
            data: Dictionary containing financial data
            
        Returns:
            FinancialData: New instance created from the dictionary
        """
        # Convert date strings back to datetime objects
        data_copy = data.copy()
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        data_copy['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data_copy)
    
    def to_json(self) -> str:
        """
        Convert the financial data to JSON string.
        
        Returns:
            str: JSON representation of the financial data
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FinancialData':
        """
        Create a FinancialData instance from a JSON string.
        
        Args:
            json_str: JSON string containing financial data
            
        Returns:
            FinancialData: New instance created from the JSON
        """
        data = json.loads(json_str)
        return cls.from_dict(data)