#!/usr/bin/env python3
"""
S&P 500とNASDAQ 100の600銘柄のデータを取得し、
EPS、PERなどの財務データを最大期間でSQLiteデータベースに保存するスクリプト
"""

import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stock_database.models.symbol_info import SymbolInfo
from stock_database.utils.sp500_nasdaq100_source import SP500Nasdaq100Source

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteStockDatabase:
    """SQLite用の株式データベースクラス"""
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self.connection = None
        self.init_database()
    
    def init_database(self):
        """データベースを初期化し、テーブルを作成"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        cursor = self.connection.cursor()
        
        # 会社情報テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_info (
                symbol TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                exchange TEXT,
                market_cap REAL,
                employees INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 株価データテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                adjusted_close REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # 財務データテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                market_cap REAL,
                enterprise_value REAL,
                trailing_pe REAL,
                forward_pe REAL,
                peg_ratio REAL,
                price_to_book REAL,
                price_to_sales REAL,
                enterprise_to_revenue REAL,
                enterprise_to_ebitda REAL,
                trailing_eps REAL,
                forward_eps REAL,
                book_value REAL,
                return_on_assets REAL,
                return_on_equity REAL,
                revenue_per_share REAL,
                profit_margins REAL,
                operating_margins REAL,
                ebitda_margins REAL,
                gross_margins REAL,
                dividend_rate REAL,
                dividend_yield REAL,
                payout_ratio REAL,
                beta REAL,
                week_52_high REAL,
                week_52_low REAL,
                current_price REAL,
                target_high_price REAL,
                target_low_price REAL,
                target_mean_price REAL,
                recommendation_mean REAL,
                number_of_analyst_opinions INTEGER,
                total_cash REAL,
                total_cash_per_share REAL,
                ebitda REAL,
                total_debt REAL,
                quick_ratio REAL,
                current_ratio REAL,
                total_revenue REAL,
                debt_to_equity REAL,
                revenue_growth REAL,
                earnings_growth REAL,
                free_cashflow REAL,
                operating_cashflow REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_data(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_data(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_symbol ON financial_data(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_data(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_sector ON company_info(sector)")
        
        self.connection.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_company_info(self, symbol: str, company_name: str, sector: str = None, 
                         industry: str = None, exchange: str = None, market_cap: float = None,
                         employees: int = None, description: str = None):
        """会社情報を保存"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO company_info 
            (symbol, company_name, sector, industry, exchange, market_cap, employees, description, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, company_name, sector, industry, exchange, market_cap, employees, description, datetime.now()))
        self.connection.commit()
    
    def save_stock_data(self, symbol: str, date: datetime, open_price: float = None,
                       high_price: float = None, low_price: float = None, close_price: float = None,
                       volume: int = None, adjusted_close: float = None):
        """株価データを保存"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO stock_data 
            (symbol, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, date.date(), open_price, high_price, low_price, close_price, volume, adjusted_close))
        self.connection.commit()
    
    def save_financial_data(self, symbol: str, date: datetime, **financial_metrics):
        """財務データを保存"""
        cursor = self.connection.cursor()
        
        # 財務指標のフィールド名を定義
        fields = [
            'market_cap', 'enterprise_value', 'trailing_pe', 'forward_pe', 'peg_ratio',
            'price_to_book', 'price_to_sales', 'enterprise_to_revenue', 'enterprise_to_ebitda',
            'trailing_eps', 'forward_eps', 'book_value', 'return_on_assets', 'return_on_equity',
            'revenue_per_share', 'profit_margins', 'operating_margins', 'ebitda_margins',
            'gross_margins', 'dividend_rate', 'dividend_yield', 'payout_ratio', 'beta',
            'week_52_high', 'week_52_low', 'current_price', 'target_high_price', 'target_low_price',
            'target_mean_price', 'recommendation_mean', 'number_of_analyst_opinions', 'total_cash',
            'total_cash_per_share', 'ebitda', 'total_debt', 'quick_ratio', 'current_ratio',
            'total_revenue', 'debt_to_equity', 'revenue_growth', 'earnings_growth',
            'free_cashflow', 'operating_cashflow'
        ]
        
        # 値を準備
        values = [symbol, date.date()]
        for field in fields:
            values.append(financial_metrics.get(field))
        
        # プレースホルダーを作成
        placeholders = ', '.join(['?'] * (len(fields) + 2))
        field_names = 'symbol, date, ' + ', '.join(fields)
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO financial_data ({field_names})
            VALUES ({placeholders})
        """, values)
        self.connection.commit()
    
    def get_statistics(self):
        """データベースの統計情報を取得"""
        cursor = self.connection.cursor()
        
        # 会社数
        cursor.execute("SELECT COUNT(*) as count FROM company_info")
        company_count = cursor.fetchone()['count']
        
        # 株価データの期間
        cursor.execute("SELECT MIN(date) as min_date, MAX(date) as max_date FROM stock_data")
        date_range = cursor.fetchone()
        
        # セクター別統計
        cursor.execute("SELECT sector, COUNT(*) as count FROM company_info WHERE sector IS NOT NULL GROUP BY sector ORDER BY count DESC")
        sectors = cursor.fetchall()
        
        return {
            'company_count': company_count,
            'date_range': date_range,
            'sectors': sectors
        }
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()


class SP500Nasdaq100DataFetcher:
    """S&P 500とNASDAQ 100のデータを取得するクラス"""
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db = SQLiteStockDatabase(db_path)
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
            
            return {
                'symbol': symbol,
                'history': hist,
                'info': info
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def extract_financial_metrics(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        財務データからEPS、PERなどの指標を抽出
        
        Args:
            info: yfinanceから取得した基本情報
            
        Returns:
            Dict[str, Any]: 財務指標
        """
        # 配当利回りの正規化（yfinanceの値は既にパーセンテージ形式なので100で割る）
        dividend_yield = info.get('dividendYield')
        if dividend_yield is not None:
            # yfinanceのdividendYieldは既にパーセンテージ形式（6.29 = 6.29%）
            # 小数形式に変換（6.29 -> 0.0629）
            dividend_yield = dividend_yield / 100
        
        return {
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
            'return_on_assets': info.get('returnOnAssets'),
            'return_on_equity': info.get('returnOnEquity'),
            'revenue_per_share': info.get('revenuePerShare'),
            'profit_margins': info.get('profitMargins'),
            'operating_margins': info.get('operatingMargins'),
            'ebitda_margins': info.get('ebitdaMargins'),
            'gross_margins': info.get('grossMargins'),
            'dividend_rate': info.get('dividendRate'),
            'dividend_yield': dividend_yield,
            'payout_ratio': info.get('payoutRatio'),
            'beta': info.get('beta'),
            'week_52_high': info.get('fiftyTwoWeekHigh'),
            'week_52_low': info.get('fiftyTwoWeekLow'),
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
    
    def save_to_database(self, symbol_info: SymbolInfo, stock_data: Dict[str, Any]):
        """
        データをデータベースに保存
        
        Args:
            symbol_info: 銘柄情報
            stock_data: 株価・財務データ
        """
        try:
            symbol = symbol_info.symbol
            info = stock_data.get('info', {})
            
            # 会社情報を保存
            self.db.save_company_info(
                symbol=symbol,
                company_name=symbol_info.company_name,
                sector=symbol_info.sector,
                industry=symbol_info.industry,
                exchange=symbol_info.exchange,
                market_cap=info.get('marketCap'),
                employees=info.get('fullTimeEmployees'),
                description=info.get('longBusinessSummary')
            )
            
            # 株価履歴データを保存
            history = stock_data.get('history')
            if history is not None and not history.empty:
                for date, row in history.iterrows():
                    self.db.save_stock_data(
                        symbol=symbol,
                        date=date,
                        open_price=float(row['Open']) if pd.notna(row['Open']) else None,
                        high_price=float(row['High']) if pd.notna(row['High']) else None,
                        low_price=float(row['Low']) if pd.notna(row['Low']) else None,
                        close_price=float(row['Close']) if pd.notna(row['Close']) else None,
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                        adjusted_close=float(row['Close']) if pd.notna(row['Close']) else None
                    )
            
            # 財務指標を保存
            metrics = self.extract_financial_metrics(info)
            if metrics:
                self.db.save_financial_data(
                    symbol=symbol,
                    date=datetime.now(),
                    **{k: v for k, v in metrics.items() if v is not None}
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
            stats = self.db.get_statistics()
            
            logger.info(f"Total companies in database: {stats['company_count']}")
            
            if stats['date_range']['min_date'] and stats['date_range']['max_date']:
                logger.info(f"Stock data date range: {stats['date_range']['min_date']} to {stats['date_range']['max_date']}")
            
            logger.info(f"Sectors represented: {len(stats['sectors'])}")
            for sector in stats['sectors'][:10]:  # 上位10セクターを表示
                logger.info(f"  {sector['sector']}: {sector['count']} companies")
            
        except Exception as e:
            logger.error(f"Failed to show statistics: {e}")
    
    def close(self):
        """リソースをクリーンアップ"""
        self.db.close()


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch S&P 500 and NASDAQ 100 data to SQLite')
    parser.add_argument('--limit', type=int, default=600, help='Maximum number of symbols to fetch')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--db-path', type=str, default='data/stock_data.db', help='SQLite database file path')
    
    args = parser.parse_args()
    
    # データ取得を実行
    fetcher = SP500Nasdaq100DataFetcher(db_path=args.db_path)
    
    try:
        fetcher.run(limit=args.limit, delay=args.delay)
    finally:
        fetcher.close()


if __name__ == "__main__":
    main()