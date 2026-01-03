"""
Market Alert Agent - Enhanced Web Dashboard
===========================================
Beautiful, interactive Streamlit dashboard with modern UI/UX

Run with: streamlit run dashboard_enhanced.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Add scripts to path
sys.path.append('./scripts')

try:
    from simple_forecaster import SimpleForecaster, load_market_data
    from agent_logic import AlertAgent, MODERATE_RULES, CONSERVATIVE_RULES, AGGRESSIVE_RULES
    from llm_explainer import LLMExplainer, format_explanation_for_output
    from alert_system import AlertSystem
except ImportError as e:
    st.error(f"Import error: {e}")

# Page configuration
st.set_page_config(
    page_title="🚀 Market Alert Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main background - Professional Dark */
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
        background-attachment: fixed;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a14 0%, #1a1a2e 100%);
        border-right: 2px solid rgba(64, 224, 208, 0.3);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff;
    }
    
    /* Main content area */
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Headers */
    h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 2.8rem !important;
        text-shadow: 2px 2px 8px rgba(64, 224, 208, 0.3);
        letter-spacing: 0px;
        margin-bottom: 1.5rem !important;
    }
    
    h2 {
        color: #40e0d0 !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
        font-size: 1.2rem !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #40e0d0 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #b0b0b0 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    
    /* Cards and containers */
    .stContainer, div[data-testid="column"] > div {
        background: linear-gradient(145deg, #1e1e3f 0%, #2a2a4a 100%);
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(64, 224, 208, 0.2);
        transition: all 0.3s ease;
    }
    
    .stContainer:hover {
        border-color: rgba(64, 224, 208, 0.4);
        box-shadow: 0 12px 40px rgba(64, 224, 208, 0.15);
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
        font-weight: 500;
        padding: 1.2rem;
        backdrop-filter: blur(10px);
    }
    
    /* Success alert */
    [data-baseweb="notification"][kind="success"] {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border-left-color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Warning alert */
    [data-baseweb="notification"][kind="warning"] {
        background: rgba(251, 146, 60, 0.15);
        color: #fb923c;
        border-left-color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.3);
    }
    
    /* Info alert */
    [data-baseweb="notification"][kind="info"] {
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border-left-color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        font-size: 15px;
        background: linear-gradient(135deg, #40e0d0 0%, #2c9e91 100%);
        color: #0a0a14;
        border: none;
        box-shadow: 0 4px 15px rgba(64, 224, 208, 0.3);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #52f5e2 0%, #40e0d0 100%);
        box-shadow: 0 6px 20px rgba(64, 224, 208, 0.5);
    }
    
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(30, 30, 63, 0.8);
        border-radius: 8px;
        border: 1px solid rgba(64, 224, 208, 0.3);
        color: #e0e0e0;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #40e0d0;
        background: rgba(30, 30, 63, 1);
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: rgba(30, 30, 63, 0.5);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(64, 224, 208, 0.2);
    }
    
    .stRadio label {
        color: #e0e0e0 !important;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(64, 224, 208, 0.2);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #40e0d0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(64, 224, 208, 0.1);
        border-radius: 8px;
        font-weight: 600;
        color: #e0e0e0;
        border: 1px solid rgba(64, 224, 208, 0.2);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(30, 30, 63, 0.5);
        border-radius: 10px;
        padding: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #b0b0b0;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #40e0d0 0%, #2c9e91 100%);
        color: #0a0a14;
        box-shadow: 0 4px 15px rgba(64, 224, 208, 0.4);
    }
    
    /* Text colors */
    p, span, div {
        color: #e0e0e0;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(30, 30, 63, 0.8);
        color: #e0e0e0;
        border: 1px solid rgba(64, 224, 208, 0.3);
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #40e0d0;
        box-shadow: 0 0 10px rgba(64, 224, 208, 0.3);
    }
    
    /* Custom badges */
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-high {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    
    .badge-medium {
        background: rgba(251, 146, 60, 0.2);
        color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.4);
    }
    
    .badge-low {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 30, 63, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #40e0d0 0%, #2c9e91 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #52f5e2 0%, #40e0d0 100%);
    }
</style>
""", unsafe_allow_html=True)


# Sidebar configuration
with st.sidebar:
    st.markdown("# ⚙️ Configuration")
    st.markdown("---")
    
    # Load dataset
    @st.cache_data
    def load_full_dataset():
        df = pd.read_csv('stock_market_dataset.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    try:
        full_data = load_full_dataset()
        stocks = sorted(full_data['Stock'].unique())
        
        st.markdown("### 📈 Select Stock")
        selected_stock = st.selectbox(
            "Choose a stock to analyze",
            stocks,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Alert Rules")
        rules_preset = st.radio(
            "Select alert sensitivity",
            ["Conservative", "Moderate", "Aggressive"],
            index=1,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Dataset Info")
        st.markdown(f"""
        <div style='background: rgba(30, 30, 63, 0.6); padding: 15px; border-radius: 8px; border: 1px solid rgba(64, 224, 208, 0.2);'>
            <p style='color: #40e0d0; margin: 5px 0; font-weight: 600;'><b>Total Records:</b> {len(full_data):,}</p>
            <p style='color: #40e0d0; margin: 5px 0; font-weight: 600;'><b>Stocks:</b> {len(stocks)}</p>
            <p style='color: #40e0d0; margin: 5px 0; font-weight: 600;'><b>Date Range:</b> {full_data['Date'].min().strftime('%Y-%m-%d')} to {full_data['Date'].max().strftime('%Y-%m-%d')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        analyze_button = st.button("🚀 Run Analysis", type="primary")
        
    except FileNotFoundError:
        st.error("❌ Dataset not found!")
        st.info("Make sure 'stock_market_dataset.csv' is in the project root.")
        st.stop()

# Main content
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🚀 Market Data Forecaster & Alert Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: white; font-size: 1.2rem; margin-top: 0;'>Intelligent Market Monitoring with AI-Powered Insights</p>", unsafe_allow_html=True)
st.markdown("---")

# Analysis function
def run_analysis(stock, rules_name):
    """Run the agent analysis."""
    with st.spinner(f"🔍 Analyzing {stock}..."):
        # Prepare data
        stock_data = full_data[full_data['Stock'] == stock].copy()
        stock_data = stock_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(100)
        
        # Initialize components
        forecaster = SimpleForecaster(window=10)
        rules = {
            'Conservative': CONSERVATIVE_RULES,
            'Moderate': MODERATE_RULES,
            'Aggressive': AGGRESSIVE_RULES
        }[rules_name]
        agent = AlertAgent(**rules)
        explainer = LLMExplainer()
        
        # Forecast
        forecaster.fit(stock_data)
        forecast = forecaster.forecast(steps=1)
        metrics = forecaster.calculate_metrics(stock_data, forecast)
        
        # Decision
        decision = agent.evaluate(metrics)
        explanation = explainer.generate_explanation(decision)
        
        return stock_data, metrics, decision, explanation

# Run analysis on button click or auto-run
if analyze_button or True:  # Auto-run on first load
    stock_data, metrics, decision, explanation = run_analysis(selected_stock, rules_preset)
    
    # Alert Status Section
    st.markdown("## 🎯 Alert Status")
    
    if decision.should_alert:
        alert_type_emoji = "⚠️" if decision.alert_type.value == "price_drop" else "🚀"
        confidence_badge = f"<span class='badge badge-{decision.confidence.value}'>{decision.confidence.value.upper()}</span>"
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 30px; border-radius: 20px; color: white; 
                    box-shadow: 0 10px 30px rgba(245, 87, 108, 0.4);
                    animation: pulse 2s ease-in-out infinite;'>
            <h2 style='color: white !important; margin: 0; font-size: 2rem;'>
                {alert_type_emoji} ALERT TRIGGERED!
            </h2>
            <p style='font-size: 1.3rem; margin: 15px 0 10px 0;'>
                <b>{decision.alert_type.value.replace('_', ' ').title()}</b>
            </p>
            <p style='margin: 10px 0;'>Confidence: {confidence_badge}</p>
            <p style='font-size: 0.95rem; opacity: 0.95; margin-top: 15px;'>
                {decision.reason}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 30px; border-radius: 20px; color: white;
                    box-shadow: 0 10px 30px rgba(56, 239, 125, 0.4);'>
            <h2 style='color: white !important; margin: 0; font-size: 2rem;'>
                ✅ No Alert - Market Stable
            </h2>
            <p style='font-size: 1.1rem; margin-top: 15px; opacity: 0.95;'>
                All market conditions are within normal ranges. No action required.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Metrics Row
    st.markdown("## 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Last Close",
            f"${metrics['last_close']:.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Predicted Close",
            f"${metrics['predicted_close']:.2f}",
            delta=f"{metrics['percent_change']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Volatility",
            f"{metrics['volatility']:.4f}",
            delta=None
        )
    
    with col4:
        trend_emoji = {"upward": "📈", "downward": "📉", "stable": "➡️"}
        st.metric(
            "Trend",
            metrics['trend'].title(),
            delta=None
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # AI Explanation
    st.markdown("## 💬 AI Explanation")
    st.info(explanation.explanation)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Price Chart
    st.markdown("## 📈 Price Chart")
    
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=stock_data['Date'],
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name='Price',
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    ))
    
    # Add forecast point
    last_date = stock_data['Date'].iloc[-1]
    next_date = pd.Timestamp(last_date) + pd.Timedelta(days=1)
    
    fig.add_trace(go.Scatter(
        x=[last_date, next_date],
        y=[metrics['last_close'], metrics['predicted_close']],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#40e0d0', width=3, dash='dash'),
        marker=dict(size=12, color='#40e0d0', symbol='star')
    ))
    
    fig.update_layout(
        title=f"{selected_stock} Stock Price (Last 100 Days)",
        title_font=dict(size=20, color='#e0e0e0', family='Poppins'),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_dark",
        hovermode='x unified',
        height=500,
        plot_bgcolor='rgba(30,30,63,0.6)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=12, color='#e0e0e0'),
        xaxis=dict(showgrid=True, gridcolor='rgba(64,224,208,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(64,224,208,0.1)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(30,30,63,0.8)',
            bordercolor='rgba(64,224,208,0.3)',
            borderwidth=1
        )
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Volume Chart
    st.markdown("## 📊 Trading Volume")
    
    fig_volume = go.Figure()
    fig_volume.add_trace(go.Bar(
        x=stock_data['Date'],
        y=stock_data['Volume'],
        name='Volume',
        marker=dict(
            color=stock_data['Volume'],
            colorscale='Turbo',
            showscale=True
        )
    ))
    
    fig_volume.update_layout(
        title=f"{selected_stock} Trading Volume",
        title_font=dict(size=20, color='#e0e0e0', family='Poppins'),
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_dark",
        height=350,
        plot_bgcolor='rgba(30,30,63,0.6)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins', size=12, color='#e0e0e0'),
        xaxis=dict(showgrid=True, gridcolor='rgba(64,224,208,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(64,224,208,0.1)')
    )
    
    st.plotly_chart(fig_volume, width='stretch')
    
    # Data Table
    with st.expander("📋 View Raw Data (Last 20 Days)"):
        st.dataframe(
            stock_data.tail(20).style.format({
                'Open': '${:.2f}',
                'High': '${:.2f}',
                'Low': '${:.2f}',
                'Close': '${:.2f}',
                'Volume': '{:,.0f}'
            }),
            width='stretch'
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white; padding: 20px;'>
    <p style='font-size: 1.1rem; font-weight: 600;'>🚀 Market Data Forecaster & Alert Agent v2.0</p>
    <p style='font-size: 0.9rem; opacity: 0.8;'>Powered by Agentic AI | Built for Supervity 2026 Hackathon</p>
    <p style='font-size: 0.85rem; opacity: 0.7;'>Author: Shaik Shaafiya</p>
</div>
""", unsafe_allow_html=True)
