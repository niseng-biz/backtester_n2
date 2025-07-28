#!/usr/bin/env python3
"""
S&P 500とNASDAQ 100の600銘柄のデータを取得し、
EPS、PERなどの財務データを最大期間で取得するスクリプト
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stock_database.models.symbol_info import SymbolInfo
from stock_database.repositories.company_info_repository import \
    CompanyInfoRepository
from stock_database.repositories.financial_data_repository import \
    FinancialDataRepository
from stock_database.repositories.stock_data_repository import \
    StockDataRepository
from stock_database.sqlite_database import SQLiteManager
from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SP500Nasdaq100DataFetcher:
    """S&P 500とNASDAQ 100のデータを取得するクラス"""
    
    def __init__(self, db_path: str = "stock_data.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db = SQLiteManager(db_path=db_path)
        self.db.connect()
        self.stock_repo = StockDataRepository(self.db)
        self.financial_repo = FinancialDataRepository(self.db)
        self.company_repo = CompanyInfoRepository(self.db)
        self.symbol_source = SP500Nasdaq100Source()
        
    def fetch_symbols(self, limit: int = 600) -> List[SymbolInfo]:
        """
        S&P 500とNASDAQ 100の銘柄を取得
        
        Args:
            limit: 取得する銘柄数の上限
            
        Returns:
            List[SymbolInfo]: 銘柄情報のリスト
        """
        logger.info(f"Fetching up to {limit} symbols from S&P 500 and NASDAQ 100...")
        
        try:
            symbols = self.symbol_source.fetch_symbols(limit=limit)
            logger.info(f"Successfully fetched {len(symbols)} symbols")
            return symbols
        except Exception as e:
            logger.error(f"Failed to fetch symbols: {e}")
            return []
    
    def fetch_stock_data(self, symbol: str, period: str = "max") -> Dict[str, Any]:
        """
        個別銘柄の株価データを取得
        
        Args:
            symbol: 銘柄シンボル
            period: 取得期間 ("max", "5y", "2y", "1y", "6mo", "3mo", "1mo")
            
        Returns:
            Dict[str, Any]: 株価データ
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # 株価履歴データを取得
            hist = ticker.history(period=period)
            
            # 基本情報を取得
            info = ticker.info
            
            # 財務データを取得
            financials = None
            quarterly_financials = None
            try:
                financials = ticker.financials
                quarterly_financials = ticker.quarterly_financials
            except Exception as e:
                logger.debug(f"Failed to get financials for {symbol}: {e}")
            
            # バランスシートを取得
            balance_sheet = None
            quarterly_balance_sheet = None
            try:
                balance_sheet = ticker.balance_sheet
                quarterly_balance_sheet = ticker.quarterly_balance_sheet
            except Exception as e:
                logger.debug(f"Failed to get balance sheet for {symbol}: {e}")
            
            # キャッシュフローを取得
            cashflow = None
            quarterly_cashflow = None
            try:
                cashflow = ticker.cashflow
                quarterly_cashflow = ticker.quarterly_cashflow
            except Exception as e:
                logger.debug(f"Failed to get cashflow for {symbol}: {e}")
            
            return {
                'symbol': symbol,
                'history': hist,
                'info': info,
                'financials': financials,
                'quarterly_financials': quarterly_financials,
                'balance_sheet': balance_sheet,
                'quarterly_balance_sheet': quarterly_balance_sheet,
                'cashflow': cashflow,
                'quarterly_cashflow': quarterly_cashflow
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def extract_financial_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        財務データからEPS、PERなどの指標を抽出
        
        Args:
            data: yfinanceから取得したデータ
            
        Returns:
            Dict[str, Any]: 財務指標
        """
        symbol = data['symbol']
        info = data.get('info', {})
        
        metrics = {
            'symbol': symbol,
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'trailing_pe': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'enterprise_to_revenue': info.get('enterpriseToRevenue'),
            'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
            'trailing_eps': info.get('trailingEps'),
            'forward_eps': info.get('forwardEps'),
            'book_value': info.get('bookValue'),
            'price_to_book': info.get('priceToBook'),
            'return_on_assets': info.get('returnOnAssets'),
            'return_on_equity': info.get('returnOnEquity'),
            'revenue_per_share': info.get('revenuePerShare'),
            'profit_margins': info.get('profitMargins'),
            'operating_margins': info.get('operatingMargins'),
            'ebitda_margins': info.get('ebitdaMargins'),
            'gross_margins': info.get('grossMargins'),
            'dividend_rate': info.get('dividendRate'),
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
            'beta': info.get('beta'),
            '52_week_high': info.get('fiftyTwoWeekHigh'),
            '52_week_low': info.get('fiftyTwoWeekLow'),
            'current_price': info.get('currentPrice'),
            'target_high_price': info.get('targetHighPrice'),
            'target_low_price': info.get('targetLowPrice'),
            'target_mean_price': info.get('targetMeanPrice'),
            'recommendation_mean': info.get('recommendationMean'),
            'number_of_analyst_opinions': info.get('numberOfAnalystOpinions'),
            'total_cash': info.get('totalCash'),
            'total_cash_per_share': info.get('totalCashPerShare'),
            'ebitda': info.get('ebitda'),
            'total_debt': info.get('totalDebt'),
            'quick_ratio': info.get('quickRatio'),
            'current_ratio': info.get('currentRatio'),
            'total_revenue': info.get('totalRevenue'),
            'debt_to_equity': info.get('debtToEquity'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'free_cashflow': info.get('freeCashflow'),
            'operating_cashflow': info.get('operatingCashflow')
        }
        
        return metrics
    
    def save_to_database(self, symbol_info: SymbolInfo, stock_data: Dict[str, Any]):
        """
        データをデータベースに保存
        
        Args:
            symbol_info: 銘柄情報
            stock_data: 株価・財務データ
        """
        try:
            symbol = symbol_info.symbol
            
            # 会社情報を保存
            self.company_repo.save_company_info(
                symbol=symbol,
                company_name=symbol_info.company_name,
                sector=symbol_info.sector,
                industry=symbol_info.industry,
                exchange=symbol_info.exchange,
                market_cap=stock_data.get('info', {}).get('marketCap'),
                employees=stock_data.get('info', {}).get('fullTimeEmployees'),
                description=stock_data.get('info', {}).get('longBusinessSummary')
            )
            
            # 株価履歴データを保存
            history = stock_data.get('history')
            if history is not None and not history.empty:
                for date, row in history.iterrows():
                    self.stock_repo.save_stock_data(
                        symbol=symbol,
                        date=date.date(),
                        open_price=float(row['Open']) if pd.notna(row['Open']) else None,
                        high_price=float(row['High']) if pd.notna(row['High']) else None,
                        low_price=float(row['Low']) if pd.notna(row['Low']) else None,
                        close_price=float(row['Close']) if pd.notna(row['Close']) else None,
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                        adjusted_close=float(row['Close']) if pd.notna(row['Close']) else None
                    )
            
            # 財務指標を保存
            metrics = self.extract_financial_metrics(stock_data)
            if metrics:
                self.financial_repo.save_financial_data(
                    symbol=symbol,
                    date=datetime.now().date(),
                    **{k: v for k, v in metrics.items() if k != 'symbol' and v is not None}
                )
            
            logger.info(f"Successfully saved data for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to save data for {symbol}: {e}")
    
    def run(self, limit: int = 600, delay: float = 1.0):
        """
        メイン実行関数
        
        Args:
            limit: 取得する銘柄数の上限
            delay: リクエスト間の遅延（秒）
        """
        logger.info("Starting S&P 500 and NASDAQ 100 data fetching process...")
        
        # 銘柄リストを取得
        symbols = self.fetch_symbols(limit=limit)
        if not symbols:
            logger.error("No symbols found. Exiting.")
            return
        
        logger.info(f"Processing {len(symbols)} symbols...")
        
        # 各銘柄のデータを取得・保存
        success_count = 0
        error_count = 0
        
        for i, symbol_info in enumerate(symbols, 1):
            symbol = symbol_info.symbol
            logger.info(f"Processing {i}/{len(symbols)}: {symbol} ({symbol_info.company_name})")
            
            try:
                # 株価・財務データを取得
                stock_data = self.fetch_stock_data(symbol, period="max")
                
                if 'error' in stock_data:
                    logger.error(f"Error fetching data for {symbol}: {stock_data['error']}")
                    error_count += 1
                    continue
                
                # データベースに保存
                self.save_to_database(symbol_info, stock_data)
                success_count += 1
                
                # レート制限のための遅延
                if delay > 0:
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Unexpected error processing {symbol}: {e}")
                error_count += 1
                continue
        
        logger.info(f"Data fetching completed. Success: {success_count}, Errors: {error_count}")
        
        # 統計情報を表示
        self.show_statistics()
    
    def show_statistics(self):
        """データベースの統計情報を表示"""
        try:
            # 銘柄数
            total_symbols = len(self.company_repo.get_all_symbols())
            logger.info(f"Total symbols in database: {total_symbols}")
            
            # 株価データの期間
            stock_data_stats = self.stock_repo.get_data_range_stats()
            if stock_data_stats:
                logger.info(f"Stock data date range: {stock_data_stats}")
            
            # セクター別統計
            sectors = self.company_repo.get_sectors()
            logger.info(f"Sectors represented: {len(sectors)}")
            for sector in sectors[:10]:  # 上位10セクターを表示
                count = len(self.company_repo.get_companies_by_sector(sector))
                logger.info(f"  {sector}: {count} companies")
            
        except Exception as e:
            logger.error(f"Failed to show statistics: {e}")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch S&P 500 and NASDAQ 100 data')
    parser.add_argument('--limit', type=int, default=600, help='Maximum number of symbols to fetch')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--db-path', type=str, default='stock_data.db', help='Database file path')
    
    args = parser.parse_args()
    
    # データ取得を実行
    fetcher = SP500Nasdaq100DataFetcher(db_path=args.db_path)
    fetcher.run(limit=args.limit, delay=args.delay)


if __name__ == "__main__":
    main()