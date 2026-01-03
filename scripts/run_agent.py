"""
Quick Agent Runner - Simplified Version
No complex dependencies, just core logic
"""

import sys
import argparse
from datetime import datetime

# Use simple forecaster instead
from simple_forecaster import SimpleForecaster, load_market_data
from agent_logic import AlertAgent, MODERATE_RULES, CONSERVATIVE_RULES, AGGRESSIVE_RULES
from llm_explainer import LLMExplainer, format_explanation_for_output
from alert_system import AlertSystem


def run_agent(data_path: str, stock_symbol: str = "AAPL", rules_preset: str = "moderate"):
    """Run the agent workflow."""
    
    print("="*70)
    print("🚀 MARKET DATA FORECASTER & ALERT AGENT")
    print("="*70)
    print(f"Stock: {stock_symbol}")
    print(f"Rules: {rules_preset}")
    print(f"Data: {data_path}")
    print("="*70)
    print()
    
    # Load data
    print("📊 Step 1: Loading market data...")
    data = load_market_data(data_path)
    print(f"  ✓ Loaded {len(data)} days")
    print(f"  ✓ Date range: {data['Date'].min()} to {data['Date'].max()}\n")
    
    # Initialize components
    print("🔧 Step 2: Initializing agent components...")
    forecaster = SimpleForecaster(window=10)
    
    rules = {
        'conservative': CONSERVATIVE_RULES,
        'moderate': MODERATE_RULES,
        'aggressive': AGGRESSIVE_RULES
    }[rules_preset.lower()]
    
    agent = AlertAgent(**rules)
    explainer = LLMExplainer(provider='openai', model='gpt-4o-mini')
    alert_system = AlertSystem(output_dir='../outputs')
    print("  ✓ All components ready\n")
    
    # Fit and forecast
    print("🔮 Step 3: Generating forecast...")
    forecaster.fit(data)
    forecast = forecaster.forecast(steps=1)
    metrics = forecaster.calculate_metrics(data, forecast)
    
    print(f"  Last Close: ${metrics['last_close']:.2f}")
    print(f"  Predicted:  ${metrics['predicted_close']:.2f}")
    print(f"  Change:     {metrics['percent_change']:+.2f}%")
    print(f"  Volatility: {metrics['volatility']:.4f}")
    print(f"  Trend:      {metrics['trend']}\n")
    
    # Agent decision
    print("🤖 Step 4: Agent decision-making...")
    decision = agent.evaluate(metrics, forecast_confidence=forecast['confidence'])
    
    if decision.should_alert:
        print(f"  ⚠️  ALERT TRIGGERED!")
        print(f"  Type: {decision.alert_type.value}")
        print(f"  Confidence: {decision.confidence.value.upper()}")
        print(f"  Reason: {decision.reason}\n")
    elif decision.suppressed:
        print(f"  🚫 Alert suppressed: {decision.suppression_reason}\n")
    else:
        print(f"  ✅ No alert - market conditions normal\n")
    
    # LLM explanation
    print("💬 Step 5: Generating AI explanation...")
    explanation = explainer.generate_explanation(decision)
    print(f"  {explanation.explanation}\n")
    
    # Save alert
    print("📝 Step 6: Logging alert...")
    alert_data = format_explanation_for_output(decision, explanation)
    alert_system.log_alert(
        alert_data,
        stock_symbol=stock_symbol,
        date=data['Date'].max().strftime("%Y-%m-%d")
    )
    
    print("\n" + "="*70)
    print("✅ AGENT WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"\nOutputs saved to: outputs/")
    print(f"  - alerts.csv")
    print(f"  - alerts.json")
    print()
    
    return decision, explanation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market Alert Agent - Quick Runner")
    parser.add_argument('--data', type=str, required=True, help='Path to market data CSV')
    parser.add_argument('--stock', type=str, default='AAPL', help='Stock symbol')
    parser.add_argument('--rules', type=str, default='moderate', 
                       choices=['conservative', 'moderate', 'aggressive'],
                       help='Alert rules preset')
    
    args = parser.parse_args()
    
    try:
        decision, explanation = run_agent(args.data, args.stock, args.rules)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
