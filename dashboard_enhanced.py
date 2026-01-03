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
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 3px solid rgba(102, 126, 234, 0.3);
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
        font-weight: 800 !important;
        font-size: 3rem !important;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        letter-spacing: -1px;
        margin-bottom: 1.5rem !important;
    }
    
    h2 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #f0f0f0 !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #667eea !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    
    /* Cards and containers */
    .stContainer, div[data-testid="column"] > div {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stContainer:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.25);
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 15px;
        border-left: 6px solid;
        animation: slideIn 0.6s ease-out;
        font-weight: 500;
        padding: 1.5rem;
    }
    
    /* Success alert */
    [data-baseweb="notification"][kind="success"] {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-left-color: #11998e;
    }
    
    /* Warning alert */
    [data-baseweb="notification"][kind="warning"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-left-color: #f5576c;
    }
    
    /* Info alert */
    [data-baseweb="notification"][kind="info"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left-color: #667eea;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-30px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        font-weight: 700;
        font-size: 17px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Custom badges */
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-high {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        box-shadow: 0 3px 10px rgba(245, 87, 108, 0.3);
    }
    
    .badge-medium {
        background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
        color: white;
        box-shadow: 0 3px 10px rgba(255, 167, 38, 0.3);
    }
    
    .badge-low {
        background: linear-gradient(135deg, #66bb6a 0%, #43a047 100%);
        color: white;
        box-shadow: 0 3px 10px rgba(102, 187, 106, 0.3);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
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
            "",
            stocks,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Alert Rules")
        rules_preset = st.radio(
            "",
            ["Conservative", "Moderate", "Aggressive"],
            index=1,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Dataset Info")
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;'>
            <p style='color: #a0a0ff; margin: 5px 0;'><b>Total Records:</b> {len(full_data):,}</p>
            <p style='color: #a0a0ff; margin: 5px 0;'><b>Stocks:</b> {len(stocks)}</p>
            <p style='color: #a0a0ff; margin: 5px 0;'><b>Date Range:</b> {full_data['Date'].min().strftime('%Y-%m-%d')} to {full_data['Date'].max().strftime('%Y-%m-%d')}</p>
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
        increasing_line_color='#11998e',
        decreasing_line_color='#f5576c'
    ))
    
    # Add forecast point
    last_date = stock_data['Date'].iloc[-1]
    next_date = pd.Timestamp(last_date) + pd.Timedelta(days=1)
    
    fig.add_trace(go.Scatter(
        x=[last_date, next_date],
        y=[metrics['last_close'], metrics['predicted_close']],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#667eea', width=3, dash='dash'),
        marker=dict(size=12, color='#667eea', symbol='star')
    ))
    
    fig.update_layout(
        title=f"{selected_stock} Stock Price (Last 100 Days)",
        title_font=dict(size=20, color='#333', family='Poppins'),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode='x unified',
        height=500,
        plot_bgcolor='rgba(255,255,255,0.9)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(family='Poppins', size=12),
        xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume Chart
    st.markdown("## 📊 Trading Volume")
    
    fig_volume = go.Figure()
    fig_volume.add_trace(go.Bar(
        x=stock_data['Date'],
        y=stock_data['Volume'],
        name='Volume',
        marker=dict(
            color=stock_data['Volume'],
            colorscale='Viridis',
            showscale=True
        )
    ))
    
    fig_volume.update_layout(
        title=f"{selected_stock} Trading Volume",
        title_font=dict(size=20, color='#333', family='Poppins'),
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_white",
        height=350,
        plot_bgcolor='rgba(255,255,255,0.9)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(family='Poppins', size=12),
        xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.3)')
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)
    
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
            use_container_width=True
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
