"""
Multi-Stock Agent Analysis
Runs the agent on all stocks in the dataset
"""

import pandas as pd
import sys
sys.path.append('.')

from simple_forecaster import SimpleForecaster, load_market_data
from agent_logic import AlertAgent, MODERATE_RULES
from llm_explainer import LLMExplainer, format_explanation_for_output
from alert_system import AlertSystem


def analyze_stock(stock_symbol: str, data: pd.DataFrame, agent, explainer, alert_system):
    """Analyze a single stock."""
    print(f"\n{'='*70}")
    print(f"📊 Analyzing {stock_symbol}")
    print(f"{'='*70}")
    
    try:
        # Prepare data
        stock_data = data[data['Stock'] == stock_symbol].copy()
        stock_data = stock_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        stock_data = stock_data.tail(100)  # Last 100 days
        
        if len(stock_data) < 20:
            print(f"  ⚠️ Insufficient data ({len(stock_data)} days)")
            return None
        
        print(f"  Data: {len(stock_data)} days ({stock_data['Date'].min()} to {stock_data['Date'].max()})")
        
        # Forecast
        forecaster = SimpleForecaster(window=10)
        forecaster.fit(stock_data)
        forecast = forecaster.forecast(steps=1)
        metrics = forecaster.calculate_metrics(stock_data, forecast)
        
        print(f"  Last Close: ${metrics['last_close']:.2f}")
        print(f"  Predicted:  ${metrics['predicted_close']:.2f}")
        print(f"  Change:     {metrics['percent_change']:+.2f}%")
        print(f"  Volatility: {metrics['volatility']:.4f}")
        
        # Decision
        decision = agent.evaluate(metrics)
        
        if decision.should_alert:
            print(f"  ⚠️ ALERT: {decision.alert_type.value} ({decision.confidence.value})")
            print(f"  Reason: {decision.reason}")
            
            # Generate explanation
            explanation = explainer.generate_explanation(decision)
            
            # Log alert
            alert_data = format_explanation_for_output(decision, explanation)
            alert_system.log_alert(
                alert_data,
                stock_symbol=stock_symbol,
                date=stock_data['Date'].max().strftime("%Y-%m-%d")
            )
            
            return {'stock': stock_symbol, 'alert': True, 'type': decision.alert_type.value}
        else:
            print(f"  ✅ No alert")
            return {'stock': stock_symbol, 'alert': False, 'type': None}
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def main():
    print("="*70)
    print("🚀 MULTI-STOCK MARKET ALERT AGENT")
    print("="*70)
    
    # Load full dataset
    print("\n📂 Loading full dataset...")
    df = pd.read_csv('../stock_market_dataset.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    stocks = sorted(df['Stock'].unique())
    print(f"  Found {len(stocks)} stocks: {', '.join(stocks)}")
    
    # Initialize components
    print("\n🔧 Initializing agent components...")
    agent = AlertAgent(**MODERATE_RULES)
    explainer = LLMExplainer()
    alert_system = AlertSystem(output_dir='../outputs')
    print("  ✓ Ready")
    
    # Analyze each stock
    results = []
    for stock in stocks:
        result = analyze_stock(stock, df, agent, explainer, alert_system)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Stocks analyzed: {len(results)}")
    print(f"Alerts triggered: {sum(1 for r in results if r['alert'])}")
    print()
    
    alerts = [r for r in results if r['alert']]
    if alerts:
        print("🚨 Alerts:")
        for alert in alerts:
            print(f"  - {alert['stock']}: {alert['type']}")
    else:
        print("✅ No alerts triggered")
    
    print(f"\n📁 Results saved to: outputs/alerts.csv")
    print("="*70)


if __name__ == "__main__":
    main()
