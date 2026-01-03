"""
Market Alert Agent - Web Dashboard
==================================
Interactive Streamlit dashboard for visualizing market data and alerts.

Run with: streamlit run dashboard.py
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
sys.path.append('../scripts')

try:
    from simple_forecaster import SimpleForecaster, load_market_data
    from agent_logic import AlertAgent, MODERATE_RULES, CONSERVATIVE_RULES, AGGRESSIVE_RULES
    from llm_explainer import LLMExplainer, format_explanation_for_output
    from alert_system import AlertSystem
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure you're running from the project root directory")


# Page configuration
st.set_page_config(
    page_title="Market Alert Agent Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-low {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def load_full_dataset():
    """Load the full stock market dataset."""
    try:
        df = pd.read_csv('stock_market_dataset.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        st.error("stock_market_dataset.csv not found!")
        return None


def load_alerts_history():
    """Load alert history from CSV."""
    try:
        df = pd.read_csv('outputs/alerts.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()


def analyze_stock(stock_symbol, data, rules_preset):
    """Run agent analysis on a stock."""
    # Filter data for stock
    stock_data = data[data['Stock'] == stock_symbol].copy()
    stock_data = stock_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    stock_data = stock_data.sort_values('Date').tail(100)
    
    if len(stock_data) < 20:
        return None, "Insufficient data"
    
    # Get rules
    rules = {
        'Conservative': CONSERVATIVE_RULES,
        'Moderate': MODERATE_RULES,
        'Aggressive': AGGRESSIVE_RULES
    }[rules_preset]
    
    # Initialize components
    forecaster = SimpleForecaster(window=10)
    agent = AlertAgent(**rules)
    explainer = LLMExplainer()
    
    # Forecast
    forecaster.fit(stock_data)
    forecast = forecaster.forecast(steps=1)
    metrics = forecaster.calculate_metrics(stock_data, forecast)
    
    # Decision
    decision = agent.evaluate(metrics)
    
    # Explanation
    explanation = explainer.generate_explanation(decision)
    
    return {
        'stock_data': stock_data,
        'forecast': forecast,
        'metrics': metrics,
        'decision': decision,
        'explanation': explanation
    }, None


def plot_stock_chart(stock_data, forecast_price=None):
    """Create interactive stock price chart."""
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=stock_data['Date'],
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name='OHLC'
    ))
    
    # Add forecast point if provided
    if forecast_price:
        last_date = stock_data['Date'].iloc[-1]
        next_date = last_date + pd.Timedelta(days=1)
        
        fig.add_trace(go.Scatter(
            x=[next_date],
            y=[forecast_price],
            mode='markers',
            marker=dict(size=15, color='red', symbol='star'),
            name='Forecast'
        ))
    
    fig.update_layout(
        title="Stock Price Chart (Last 100 Days)",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    return fig


def plot_volume_chart(stock_data):
    """Create volume bar chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=stock_data['Date'],
        y=stock_data['Volume'],
        name='Volume',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        height=300
    )
    
    return fig


def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Market Alert Agent Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Real-time Market Monitoring & Alert System")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # Load data
    with st.spinner("Loading data..."):
        full_data = load_full_dataset()
    
    if full_data is None:
        st.error("Failed to load dataset. Please ensure stock_market_dataset.csv is in the root directory.")
        return
    
    # Stock selection
    stocks = sorted(full_data['Stock'].unique())
    selected_stock = st.sidebar.selectbox("Select Stock", stocks, index=0)
    
    # Rules preset
    rules_preset = st.sidebar.selectbox(
        "Alert Rules",
        ["Conservative", "Moderate", "Aggressive"],
        index=1
    )
    
    # Analysis button
    run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary")
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Dataset Info")
    st.sidebar.info(f"""
    **Total Records**: {len(full_data):,}  
    **Stocks**: {len(stocks)}  
    **Date Range**: {full_data['Date'].min().strftime('%Y-%m-%d')} to {full_data['Date'].max().strftime('%Y-%m-%d')}
    """)
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Analysis", "🚨 Alerts History", "📊 Portfolio View", "ℹ️ About"])
    
    with tab1:
        st.header(f"Analysis: {selected_stock}")
        
        if run_analysis:
            with st.spinner(f"Analyzing {selected_stock}..."):
                result, error = analyze_stock(selected_stock, full_data, rules_preset)
            
            if error:
                st.error(f"Error: {error}")
            elif result:
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                metrics = result['metrics']
                
                with col1:
                    st.metric(
                        "Last Close",
                        f"${metrics['last_close']:.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Predicted Close",
                        f"${metrics['predicted_close']:.2f}",
                        f"{metrics['percent_change']:.2f}%"
                    )
                
                with col3:
                    st.metric(
                        "Volatility",
                        f"{metrics['volatility']:.4f}"
                    )
                
                with col4:
                    st.metric(
                        "Trend",
                        metrics['trend'].upper()
                    )
                
                # Alert status
                st.markdown("---")
                decision = result['decision']
                
                if decision.should_alert:
                    alert_class = f"alert-{decision.confidence.value}"
                    st.markdown(f"""
                    <div class="{alert_class}">
                        <h3>⚠️ ALERT TRIGGERED</h3>
                        <p><strong>Type:</strong> {decision.alert_type.value.upper()}</p>
                        <p><strong>Confidence:</strong> {decision.confidence.value.upper()}</p>
                        <p><strong>Reason:</strong> {decision.reason}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 💬 AI Explanation")
                    st.info(result['explanation'].explanation)
                else:
                    st.success("✅ No alerts - Market conditions are normal")
                
                # Charts
                st.markdown("---")
                st.subheader("📈 Price Chart")
                fig1 = plot_stock_chart(result['stock_data'], metrics['predicted_close'])
                st.plotly_chart(fig1, use_container_width=True)
                
                st.subheader("📊 Volume Chart")
                fig2 = plot_volume_chart(result['stock_data'])
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("👈 Click 'Run Analysis' to analyze the selected stock")
            
            # Show recent data preview
            stock_preview = full_data[full_data['Stock'] == selected_stock].tail(10)
            st.subheader("Recent Data Preview")
            st.dataframe(
                stock_preview[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']],
                use_container_width=True
            )
    
    with tab2:
        st.header("🚨 Alert History")
        
        alerts_df = load_alerts_history()
        
        if not alerts_df.empty:
            # Filter controls
            col1, col2 = st.columns(2)
            
            with col1:
                filter_stock = st.multiselect(
                    "Filter by Stock",
                    options=alerts_df['stock'].unique(),
                    default=alerts_df['stock'].unique()
                )
            
            with col2:
                filter_alert = st.multiselect(
                    "Filter by Alert Type",
                    options=alerts_df['alert_type'].dropna().unique(),
                    default=alerts_df['alert_type'].dropna().unique()
                )
            
            # Apply filters
            filtered_alerts = alerts_df[
                (alerts_df['stock'].isin(filter_stock)) &
                (alerts_df['alert_type'].isin(filter_alert) | alerts_df['alert_type'].isna())
            ]
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Alerts", len(filtered_alerts[filtered_alerts['alert_triggered']]))
            
            with col2:
                if len(filtered_alerts) > 0:
                    alert_rate = (filtered_alerts['alert_triggered'].sum() / len(filtered_alerts)) * 100
                    st.metric("Alert Rate", f"{alert_rate:.1f}%")
            
            with col3:
                high_conf = len(filtered_alerts[filtered_alerts['confidence'] == 'high'])
                st.metric("High Confidence", high_conf)
            
            # Alert cards
            st.markdown("---")
            st.subheader("Recent Alerts")
            
            triggered_alerts = filtered_alerts[filtered_alerts['alert_triggered']].sort_values('timestamp', ascending=False)
            
            if not triggered_alerts.empty:
                for _, alert in triggered_alerts.head(10).iterrows():
                    alert_class = f"alert-{alert['confidence']}" if alert['confidence'] else "alert-low"
                    
                    st.markdown(f"""
                    <div class="{alert_class}">
                        <h4>{alert['stock']} - {alert['alert_type'].upper() if pd.notna(alert['alert_type']) else 'N/A'}</h4>
                        <p><strong>Date:</strong> {alert['timestamp']}</p>
                        <p><strong>Change:</strong> {alert['percent_change']:.2f}%</p>
                        <p><strong>Confidence:</strong> {alert['confidence'].upper() if pd.notna(alert['confidence']) else 'N/A'}</p>
                        <p><strong>Explanation:</strong> {alert['human_explanation']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No alerts found with current filters")
            
            # Data table
            st.markdown("---")
            st.subheader("Alert Data Table")
            st.dataframe(
                filtered_alerts[['timestamp', 'stock', 'alert_type', 'confidence', 
                                'last_close', 'predicted_close', 'percent_change']],
                use_container_width=True
            )
        else:
            st.info("No alert history found. Run some analyses to generate alerts!")
    
    with tab3:
        st.header("📊 Portfolio Overview")
        
        if st.button("Analyze All Stocks", type="primary"):
            results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, stock in enumerate(stocks):
                status_text.text(f"Analyzing {stock}...")
                result, error = analyze_stock(stock, full_data, rules_preset)
                
                if result and not error:
                    results.append({
                        'Stock': stock,
                        'Last Close': result['metrics']['last_close'],
                        'Predicted': result['metrics']['predicted_close'],
                        'Change %': result['metrics']['percent_change'],
                        'Volatility': result['metrics']['volatility'],
                        'Alert': '⚠️' if result['decision'].should_alert else '✅',
                        'Type': result['decision'].alert_type.value if result['decision'].should_alert else '-',
                        'Confidence': result['decision'].confidence.value if result['decision'].should_alert else '-'
                    })
                
                progress_bar.progress((idx + 1) / len(stocks))
            
            status_text.text("Analysis complete!")
            
            # Display results
            if results:
                results_df = pd.DataFrame(results)
                
                # Summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    alerts_count = (results_df['Alert'] == '⚠️').sum()
                    st.metric("Stocks with Alerts", f"{alerts_count}/{len(results_df)}")
                
                with col2:
                    avg_change = results_df['Change %'].mean()
                    st.metric("Avg Predicted Change", f"{avg_change:.2f}%")
                
                with col3:
                    high_vol = (results_df['Volatility'] > 0.5).sum()
                    st.metric("High Volatility Stocks", high_vol)
                
                # Table
                st.markdown("---")
                st.dataframe(results_df, use_container_width=True)
                
                # Chart
                st.markdown("---")
                st.subheader("Predicted Changes")
                
                fig = px.bar(
                    results_df,
                    x='Stock',
                    y='Change %',
                    color='Change %',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    title="Predicted Price Changes by Stock"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Click 'Analyze All Stocks' to run portfolio-wide analysis")
    
    with tab4:
        st.header("ℹ️ About the Market Alert Agent")
        
        st.markdown("""
        ### What is This?
        
        The **Market Alert Agent** is an agentic AI system that monitors market data, forecasts movements, 
        and intelligently decides when to trigger alerts.
        
        ### Key Features
        
        - 🔮 **Forecasting**: Predicts next-day price movements using time-series analysis
        - 🤖 **Agentic Decision-Making**: Multi-condition logic determines alert triggers
        - 🧠 **Self-Checking**: Validates confidence before alerting to prevent false alarms
        - 💬 **AI Explanations**: Generates human-readable reasoning for every decision
        - 📊 **Multi-Asset**: Monitors multiple stocks simultaneously
        - 🎚️ **Configurable**: Choose between conservative, moderate, or aggressive rules
        
        ### How It Works
        
        1. **Load Data** → Historical OHLCV market data
        2. **Forecast** → Predict next-day closing price
        3. **Evaluate** → Check if changes exceed thresholds
        4. **Self-Check** → Validate confidence and prevent spam
        5. **Explain** → Generate AI-powered reasoning
        6. **Alert** → Output structured alerts
        
        ### Alert Rules
        
        | Preset | Price Drop | Price Spike | Volatility | Min Confidence |
        |--------|------------|-------------|------------|----------------|
        | Conservative | 5.0% | 6.0% | 0.04 | 75% |
        | Moderate | 4.0% | 5.0% | 0.03 | 65% |
        | Aggressive | 3.0% | 4.0% | 0.02 | 55% |
        
        ### Technology Stack
        
        - **Frontend**: Streamlit
        - **Forecasting**: Moving Average + Linear Trend
        - **Visualization**: Plotly
        - **Data**: Pandas, NumPy
        
        ### Author
        
        **Shaik Shaafiya**  
        Hackathon: Supervity 2026  
        Domain: Finance + Agentic AI
        
        ---
        
        For more information, see the project README.md
        """)


if __name__ == "__main__":
    main()
