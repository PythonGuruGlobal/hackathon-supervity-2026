"""
Real-Time Stock Market Dashboard
=================================
Fetches live stock data from Alpha Vantage API and displays real-time graphs

Run with: streamlit run realtime_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import time
import sys
import os

# Add scripts to path
sys.path.append('./scripts')

try:
    from simple_forecaster import SimpleForecaster
    from agent_logic import AlertAgent, MODERATE_RULES
    from llm_explainer import LLMExplainer
except ImportError as e:
    st.error(f"Import error: {e}")

# Alpha Vantage API Configuration
API_KEY = "BEWGGWDHQV07D4GG"
BASE_URL = "https://www.alphavantage.co/query"

# Page configuration
st.set_page_config(
    page_title="📈 Real-Time Stock Market",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
        background-attachment: fixed;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    h1, h2, h3 {
        color: white;
        font-weight: 700;
    }
    
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #00ff00;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_realtime_data(symbol):
    """Fetch real-time stock data from Alpha Vantage API."""
    try:
        # Fetch intraday data (1 min intervals)
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': '1min',
            'apikey': API_KEY,
            'outputsize': 'compact'
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (1min)' in data:
            time_series = data['Time Series (1min)']
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            
            return df, None
        elif 'Note' in data:
            return None, "API call frequency exceeded. Please wait a minute."
        else:
            return None, f"Error: {data.get('Error Message', 'Unknown error')}"
            
    except Exception as e:
        return None, f"Error fetching data: {str(e)}"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_daily_data(symbol):
    """Fetch daily stock data for historical analysis."""
    try:
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'compact',
            'apikey': API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            
            return df, None
        else:
            return None, f"Error: {data.get('Error Message', 'Unknown error')}"
            
    except Exception as e:
        return None, f"Error fetching data: {str(e)}"


def plot_realtime_chart(df, symbol):
    """Create an interactive real-time candlestick chart."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{symbol} Real-Time Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff0055'
        ),
        row=1, col=1
    )
    
    # Add moving average
    if len(df) >= 20:
        ma20 = df['close'].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ma20,
                name='MA(20)',
                line=dict(color='#ffd700', width=2)
            ),
            row=1, col=1
        )
    
    # Volume bars
    colors = ['#00ff88' if close >= open else '#ff0055' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    
    return fig


def display_metrics(df, symbol):
    """Display key metrics in cards."""
    current_price = df['close'].iloc[-1]
    open_price = df['open'].iloc[0]
    high_price = df['high'].max()
    low_price = df['low'].min()
    volume = df['volume'].sum()
    
    price_change = current_price - open_price
    price_change_pct = (price_change / open_price) * 100
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #888; margin:0;">Current Price</h4>
            <h2 style="margin:10px 0; color: white;">${current_price:.2f}</h2>
            <p style="color: {'#00ff88' if price_change >= 0 else '#ff0055'}; margin:0;">
                {'+' if price_change >= 0 else ''}{price_change:.2f} 
                ({'+' if price_change_pct >= 0 else ''}{price_change_pct:.2f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #888; margin:0;">Day High</h4>
            <h2 style="margin:10px 0; color: #00ff88;">${high_price:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #888; margin:0;">Day Low</h4>
            <h2 style="margin:10px 0; color: #ff0055;">${low_price:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #888; margin:0;">Day Open</h4>
            <h2 style="margin:10px 0; color: white;">${open_price:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #888; margin:0;">Volume</h4>
            <h2 style="margin:10px 0; color: #667eea;">{volume:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)


def main():
    # Header
    st.markdown("""
        <h1 style="text-align: center; margin-bottom: 10px;">
            📈 Real-Time Stock Market Dashboard
        </h1>
        <p style="text-align: center; color: #888; margin-bottom: 30px;">
            <span class="live-indicator"></span>
            Live market data powered by Alpha Vantage
        </p>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Stock symbol input
        symbol = st.text_input(
            "Stock Symbol",
            value="AAPL",
            help="Enter stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
        ).upper()
        
        # Refresh interval
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=30,
            max_value=300,
            value=60,
            step=30
        )
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        
        # Manual refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Data Source")
        st.markdown("""
        **Alpha Vantage API**
        - Real-time data (1-min intervals)
        - Daily historical data
        - Professional market data
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This dashboard displays real-time stock market data
        with live price updates, candlestick charts, and 
        technical indicators.
        """)
    
    # Main content
    try:
        # Fetch real-time data
        with st.spinner(f'Fetching real-time data for {symbol}...'):
            df_realtime, error = fetch_realtime_data(symbol)
        
        if error:
            st.error(error)
            st.info("Trying to fetch daily data instead...")
            df_realtime, error = fetch_daily_data(symbol)
            if error:
                st.error(error)
                return
        
        if df_realtime is not None and not df_realtime.empty:
            # Display last update time
            last_update = df_realtime.index[-1]
            st.markdown(f"""
                <p style="text-align: center; color: #888; margin-bottom: 20px;">
                    Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            """, unsafe_allow_html=True)
            
            # Display metrics
            display_metrics(df_realtime, symbol)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display chart
            fig = plot_realtime_chart(df_realtime, symbol)
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table (expandable)
            with st.expander("📋 View Raw Data"):
                st.dataframe(
                    df_realtime.sort_index(ascending=False).head(50),
                    use_container_width=True
                )
            
            # Technical Analysis Section
            st.markdown("### 📊 Technical Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if len(df_realtime) >= 14:
                    # RSI calculation
                    delta = df_realtime['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    rsi_color = '#00ff88' if 30 <= current_rsi <= 70 else '#ff0055'
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #888;">RSI (14)</h4>
                        <h2 style="color: {rsi_color};">{current_rsi:.2f}</h2>
                        <p style="color: #888;">
                            {'Oversold' if current_rsi < 30 else 'Overbought' if current_rsi > 70 else 'Neutral'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if len(df_realtime) >= 20:
                    # Volatility (Standard Deviation)
                    volatility = df_realtime['close'].pct_change().std() * 100
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #888;">Volatility</h4>
                        <h2 style="color: #667eea;">{volatility:.2f}%</h2>
                        <p style="color: #888;">Price Standard Deviation</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Auto-refresh
            if auto_refresh:
                time.sleep(refresh_interval)
                st.rerun()
        
        else:
            st.warning(f"No data available for {symbol}")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check your internet connection and API key.")


if __name__ == "__main__":
    main()
