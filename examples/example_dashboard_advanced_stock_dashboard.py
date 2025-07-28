#!/usr/bin/env python3
"""
高度な株式データダッシュボード - プロフェッショナル分析ツール

🎯 目的:
Streamlitベースの高機能株式データ分析ダッシュボードを提供し、
投資家やアナリストが詳細な技術分析を行えるようにします。

📊 主要機能:
- 個別銘柄の詳細分析
- テクニカル指標（MACD、RSI、ボリンジャーバンド、移動平均）
- セクター内比較分析
- 財務指標の可視化
- インタラクティブチャート
- パフォーマンス統計
- リアルタイムデータ表示

🚀 実行方法:
    streamlit run examples/advanced_stock_dashboard.py
    # または
    python scripts/run_dashboard.py

🌐 アクセス:
ブラウザで http://localhost:8501 を開いてください

📈 必要なデータ:
- stock_data.db（SQLiteデータベース）
- S&P500/NASDAQ100銘柄データ

💡 準備コマンド:
    python scripts/fetch_sp500_nasdaq100_sqlite.py --limit 600

👥 対象者:
- 投資家・トレーダー
- 金融アナリスト
- データサイエンティスト
- 技術分析を学びたい方

✨ 特徴:
- レスポンシブデザイン
- リアルタイム更新
- エクスポート機能
- カスタマイズ可能な指標
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ページ設定
st.set_page_config(
    page_title="株式データダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AdvancedStockDashboard:
    """高度な株式データダッシュボードクラス"""
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        self.db_path = db_path
        
    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)
    
    def get_available_symbols(self):
        """利用可能な銘柄リストを取得"""
        conn = self.get_connection()
        query = """
            SELECT symbol, company_name, sector 
            FROM company_info 
            ORDER BY symbol
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_company_info(self, symbol: str):
        """会社情報を取得"""
        conn = self.get_connection()
        query = """
            SELECT * FROM company_info WHERE symbol = ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        return df.iloc[0] if not df.empty else None
    
    def get_financial_data(self, symbol: str):
        """財務データを取得"""
        conn = self.get_connection()
        query = """
            SELECT * FROM financial_data WHERE symbol = ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        return df
    
    def get_stock_data(self, symbol: str, days: int = None):
        """株価データを取得"""
        conn = self.get_connection()
        
        if days:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            query = """
                SELECT date, open_price, high_price, low_price, close_price, volume
                FROM stock_data 
                WHERE symbol = ? AND date >= ? AND date <= ?
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
        else:
            query = """
                SELECT date, open_price, high_price, low_price, close_price, volume
                FROM stock_data 
                WHERE symbol = ?
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(symbol,))
        
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        return df
    
    def get_sector_comparison(self, sector: str, metric: str = 'market_cap'):
        """セクター内比較データを取得"""
        conn = self.get_connection()
        query = f"""
            SELECT c.symbol, c.company_name, f.{metric}
            FROM company_info c
            JOIN financial_data f ON c.symbol = f.symbol
            WHERE c.sector = ? AND f.{metric} IS NOT NULL
            ORDER BY f.{metric} DESC
            LIMIT 20
        """
        df = pd.read_sql_query(query, conn, params=(sector,))
        conn.close()
        return df
    
    def calculate_technical_indicators(self, df):
        """テクニカル指標を計算"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 移動平均
        df['SMA_20'] = df['close_price'].rolling(window=20).mean()
        df['SMA_50'] = df['close_price'].rolling(window=50).mean()
        df['SMA_200'] = df['close_price'].rolling(window=200).mean()
        
        # EMA
        df['EMA_12'] = df['close_price'].ewm(span=12).mean()
        df['EMA_26'] = df['close_price'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ボリンジャーバンド
        df['BB_Middle'] = df['close_price'].rolling(window=20).mean()
        bb_std = df['close_price'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # 出来高移動平均
        df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def calculate_returns(self, df):
        """リターンを計算"""
        if df.empty:
            return df
        
        df = df.copy()
        df['Daily_Return'] = df['close_price'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        
        return df


def main():
    """メイン関数"""
    
    # タイトル
    st.title("📊 株式データダッシュボード")
    st.markdown("---")
    
    # データベースファイルの確認
    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        st.error(f"データベースファイル '{db_path}' が見つかりません。")
        st.info("まず `python scripts/fetch_sp500_nasdaq100_sqlite.py` を実行してデータを取得してください。")
        return
    
    # ダッシュボードインスタンスを作成
    dashboard = AdvancedStockDashboard(db_path)
    
    # サイドバー
    st.sidebar.header("🔍 分析設定")
    
    try:
        symbols_df = dashboard.get_available_symbols()
        
        if symbols_df.empty:
            st.error("データベースに銘柄データがありません。")
            return
        
        # 分析タイプ選択
        analysis_type = st.sidebar.selectbox(
            "分析タイプ",
            ["個別銘柄分析", "セクター比較"]
        )
        
        if analysis_type == "個別銘柄分析":
            show_individual_analysis(dashboard, symbols_df)
        elif analysis_type == "セクター比較":
            show_sector_comparison(dashboard, symbols_df)
            
    except Exception as e:
        st.error(f"データベースエラー: {e}")
        return


def show_individual_analysis(dashboard, symbols_df):
    """個別銘柄分析を表示"""
    
    # 銘柄選択
    symbol_options = {}
    for _, row in symbols_df.iterrows():
        symbol_options[f"{row['symbol']} - {row['company_name']}"] = row['symbol']
    
    selected_display = st.sidebar.selectbox("銘柄", list(symbol_options.keys()))
    selected_symbol = symbol_options[selected_display]
    
    # 期間選択
    period_options = {
        "1ヶ月": 30,
        "3ヶ月": 90,
        "6ヶ月": 180,
        "1年": 365,
        "2年": 730,
        "5年": 1825,
        "全期間": None
    }
    selected_period = st.sidebar.selectbox("期間", list(period_options.keys()), index=3)
    
    # 会社情報を取得
    company_info = dashboard.get_company_info(selected_symbol)
    financial_data = dashboard.get_financial_data(selected_symbol)
    
    if company_info is None:
        st.error(f"銘柄 {selected_symbol} の情報が見つかりません。")
        return
    
    # 会社情報表示
    st.header(f"🏢 {company_info['company_name']} ({selected_symbol})")
    
    # 基本情報
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("セクター", company_info.get('sector', 'N/A'))
    
    with col2:
        market_cap = company_info.get('market_cap')
        if market_cap:
            market_cap_b = market_cap / 1e9
            st.metric("時価総額", f"${market_cap_b:.1f}B")
        else:
            st.metric("時価総額", "N/A")
    
    with col3:
        employees = company_info.get('employees')
        if employees:
            st.metric("従業員数", f"{employees:,}")
        else:
            st.metric("従業員数", "N/A")
    
    with col4:
        exchange = company_info.get('exchange', 'N/A')
        st.metric("取引所", exchange)
    
    # 財務指標
    if not financial_data.empty:
        st.subheader("💰 財務指標")
        
        fin_col1, fin_col2, fin_col3, fin_col4, fin_col5, fin_col6 = st.columns(6)
        
        fin_data = financial_data.iloc[0]
        
        with fin_col1:
            trailing_pe = fin_data.get('trailing_pe')
            if trailing_pe and trailing_pe > 0:
                st.metric("PER", f"{trailing_pe:.2f}")
            else:
                st.metric("PER", "N/A")
        
        with fin_col2:
            trailing_eps = fin_data.get('trailing_eps')
            if trailing_eps:
                st.metric("EPS", f"${trailing_eps:.2f}")
            else:
                st.metric("EPS", "N/A")
        
        with fin_col3:
            price_to_book = fin_data.get('price_to_book')
            if price_to_book:
                st.metric("PBR", f"{price_to_book:.2f}")
            else:
                st.metric("PBR", "N/A")
        
        with fin_col4:
            return_on_equity = fin_data.get('return_on_equity')
            if return_on_equity:
                roe_pct = return_on_equity * 100
                st.metric("ROE", f"{roe_pct:.2f}%")
            else:
                st.metric("ROE", "N/A")
        
        with fin_col5:
            debt_to_equity = fin_data.get('debt_to_equity')
            if debt_to_equity:
                st.metric("D/E比率", f"{debt_to_equity:.2f}")
            else:
                st.metric("D/E比率", "N/A")
        
        with fin_col6:
            dividend_yield = fin_data.get('dividend_yield')
            if dividend_yield and dividend_yield > 0:
                # 配当利回りが小数形式（0.0193 = 1.93%）の場合
                if dividend_yield <= 1:
                    dividend_pct = dividend_yield * 100
                else:
                    # 既にパーセンテージ形式の場合はそのまま使用
                    dividend_pct = dividend_yield
                st.metric("配当利回り", f"{dividend_pct:.2f}%")
            else:
                st.metric("配当利回り", "N/A")
    
    # 株価データを取得
    stock_data = dashboard.get_stock_data(selected_symbol, period_options[selected_period])
    
    if stock_data.empty:
        st.warning(f"銘柄 {selected_symbol} の株価データが見つかりません。")
        return
    
    # リターン計算
    stock_data = dashboard.calculate_returns(stock_data)
    
    # 株価チャートとリターン
    st.subheader(f"📊 株価チャートとリターン ({selected_period})")
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('株価', 'リターン', '出来高'),
        row_heights=[0.5, 0.3, 0.2]
    )
    
    # キャンドルスティック
    fig.add_trace(
        go.Candlestick(
            x=stock_data.index,
            open=stock_data['open_price'],
            high=stock_data['high_price'],
            low=stock_data['low_price'],
            close=stock_data['close_price'],
            name="株価"
        ),
        row=1, col=1
    )
    
    # 累積リターン
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=stock_data['Cumulative_Return'] * 100,
            mode='lines',
            name="累積リターン (%)",
            line=dict(color='green')
        ),
        row=2, col=1
    )
    
    # 出来高
    fig.add_trace(
        go.Bar(
            x=stock_data.index,
            y=stock_data['volume'],
            name="出来高",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=3, col=1
    )
    
    fig.update_layout(
        title=f"{company_info['company_name']} ({selected_symbol}) - 詳細分析",
        height=800,
        showlegend=False
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # パフォーマンス統計
    st.subheader("📈 パフォーマンス統計")
    
    if len(stock_data) > 1:
        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        
        total_return = stock_data['Cumulative_Return'].iloc[-1] * 100
        volatility = stock_data['Daily_Return'].std() * np.sqrt(252) * 100
        sharpe_ratio = stock_data['Daily_Return'].mean() / stock_data['Daily_Return'].std() * np.sqrt(252) if stock_data['Daily_Return'].std() != 0 else 0
        max_drawdown = ((stock_data['close_price'] / stock_data['close_price'].cummax()) - 1).min() * 100
        
        with perf_col1:
            st.metric("総リターン", f"{total_return:.2f}%")
        
        with perf_col2:
            st.metric("年率ボラティリティ", f"{volatility:.2f}%")
        
        with perf_col3:
            st.metric("シャープレシオ", f"{sharpe_ratio:.2f}")
        
        with perf_col4:
            st.metric("最大ドローダウン", f"{max_drawdown:.2f}%")
    
     # テクニカル指標を計算
    stock_data = dashboard.calculate_technical_indicators(stock_data)
    
    # 価格とテクニカル指標
    st.subheader("📊 価格とテクニカル指標")
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('価格と移動平均', 'MACD', 'RSI', '出来高'),
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )
    
    # 価格と移動平均
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['close_price'], name='終値', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['SMA_20'], name='SMA20', line=dict(color='orange')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['SMA_50'], name='SMA50', line=dict(color='red')),
        row=1, col=1
    )
    
    # ボリンジャーバンド
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['BB_Upper'], name='BB上限', line=dict(color='gray', dash='dash')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['BB_Lower'], name='BB下限', line=dict(color='gray', dash='dash')),
        row=1, col=1
    )
    
    # MACD
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['MACD'], name='MACD', line=dict(color='blue')),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['MACD_Signal'], name='Signal', line=dict(color='red')),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=stock_data.index, y=stock_data['MACD_Histogram'], name='Histogram'),
        row=2, col=1
    )
    
    # RSI
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['RSI'], name='RSI', line=dict(color='purple')),
        row=3, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # 出来高
    fig.add_trace(
        go.Bar(x=stock_data.index, y=stock_data['volume'], name='出来高'),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(x=stock_data.index, y=stock_data['Volume_SMA'], name='出来高SMA', line=dict(color='red')),
        row=4, col=1
    )
    
    fig.update_layout(
        title=f"{selected_symbol} テクニカル分析",
        height=1000,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 現在のテクニカル指標値
    st.subheader("📊 現在のテクニカル指標")
    
    if not stock_data.empty:
        latest = stock_data.iloc[-1]
        
        tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
        
        with tech_col1:
            st.metric("RSI", f"{latest['RSI']:.2f}")
        
        with tech_col2:
            st.metric("MACD", f"{latest['MACD']:.4f}")
        
        with tech_col3:
            sma20_position = ((latest['close_price'] - latest['SMA_20']) / latest['SMA_20'] * 100) if latest['SMA_20'] else 0
            st.metric("SMA20からの乖離", f"{sma20_position:.2f}%")
        
        with tech_col4:
            bb_position = ((latest['close_price'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower']) * 100) if (latest['BB_Upper'] - latest['BB_Lower']) != 0 else 0
            st.metric("BB位置", f"{bb_position:.1f}%")



def show_sector_comparison(dashboard, symbols_df):
    """セクター比較を表示"""
    
    sectors = sorted(symbols_df['sector'].dropna().unique().tolist())
    selected_sector = st.sidebar.selectbox("セクター", sectors)
    
    st.header(f"🏭 {selected_sector} セクター比較")
    metric_selector = ["market_cap", "trailing_pe", "price_to_book", "return_on_equity", "dividend_yield"]
    
    for comparison_metric in metric_selector:
        st.header(f"{comparison_metric} 比較")

        # セクター内比較データを取得
        sector_data = dashboard.get_sector_comparison(selected_sector, comparison_metric)
        
        if sector_data.empty:
            st.warning(f"{selected_sector} セクターのデータが見つかりません。")
            return

        # 比較チャート
        fig = px.bar(
            sector_data.head(15),
            x='symbol',
            y=comparison_metric,
            hover_data=['company_name'],
            title=f"{selected_sector} セクター - {comparison_metric} 比較"
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # データテーブル
        st.subheader("詳細データ")
        st.dataframe(sector_data)

if __name__ == "__main__":
    main()