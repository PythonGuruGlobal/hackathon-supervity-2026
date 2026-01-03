"""
Main Agent Orchestrator
=======================
Coordinates all components: forecasting, decision-making, LLM explanation, and alerting.
This is the production entry point for the agentic system.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Import our modules
from forecaster import MarketForecaster, load_market_data
from agent_logic import AlertAgent, MODERATE_RULES, CONSERVATIVE_RULES, AGGRESSIVE_RULES
from llm_explainer import LLMExplainer, format_explanation_for_output
from alert_system import AlertSystem


class MarketAlertAgent:
    """
    Main orchestrator for the Market Data Forecaster & Alert Agent.
    
    This coordinates the full agentic workflow:
    1. Load market data
    2. Generate forecast
    3. Agent evaluates forecast
    4. LLM generates explanation
    5. Alert system outputs results
    """
    
    def __init__(
        self,
        data_path: str,
        output_dir: str = "../outputs",
        rules_preset: str = "moderate",
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        stock_symbol: str = "SAMPLE"
    ):
        """
        Initialize the agent system.
        
        Args:
            data_path: Path to market data CSV
            output_dir: Directory for outputs
            rules_preset: "conservative", "moderate", or "aggressive"
            llm_provider: LLM provider for explanations
            llm_model: LLM model name
            stock_symbol: Stock ticker symbol
        """
        self.data_path = data_path
        self.stock_symbol = stock_symbol
        
        # Initialize components
        print("🔧 Initializing Market Alert Agent...")
        
        # 1. Forecaster
        self.forecaster = MarketForecaster(model_type="arima")
        print("  ✓ Forecaster initialized")
        
        # 2. Decision agent
        rules = self._get_rules_preset(rules_preset)
        self.agent = AlertAgent(**rules)
        print(f"  ✓ Decision agent initialized ({rules_preset} rules)")
        
        # 3. LLM explainer
        self.explainer = LLMExplainer(provider=llm_provider, model=llm_model)
        print(f"  ✓ LLM explainer initialized ({llm_provider}/{llm_model})")
        
        # 4. Alert system
        self.alert_system = AlertSystem(output_dir=output_dir)
        print(f"  ✓ Alert system initialized")
        print()
    
    def _get_rules_preset(self, preset: str) -> dict:
        """Get alert rules based on preset."""
        presets = {
            'conservative': CONSERVATIVE_RULES,
            'moderate': MODERATE_RULES,
            'aggressive': AGGRESSIVE_RULES
        }
        return presets.get(preset.lower(), MODERATE_RULES)
    
    def run(self) -> dict:
        """
        Execute the full agent workflow.
        
        Returns:
            Dictionary with execution results
        """
        print("🚀 Starting Agent Workflow...\n")
        
        # Step 1: Load data
        print("📊 Step 1: Loading market data...")
        try:
            data = load_market_data(self.data_path)
            print(f"  ✓ Loaded {len(data)} days of data")
            print(f"  ✓ Date range: {data['Date'].min()} to {data['Date'].max()}\n")
        except Exception as e:
            print(f"  ❌ Error loading data: {e}")
            return {'success': False, 'error': str(e)}
        
        # Step 2: Fit forecasting model
        print("🔮 Step 2: Fitting forecast model...")
        try:
            self.forecaster.fit(data, target_col="Close")
            print("  ✓ Model fitted successfully\n")
        except Exception as e:
            print(f"  ❌ Error fitting model: {e}")
            return {'success': False, 'error': str(e)}
        
        # Step 3: Generate forecast
        print("📈 Step 3: Generating forecast...")
        try:
            forecast = self.forecaster.forecast(steps=1)
            metrics = self.forecaster.calculate_metrics(data, forecast)
            
            print(f"  ✓ Forecast complete:")
            print(f"    Last Close: ${metrics['last_close']:.2f}")
            print(f"    Predicted: ${metrics['predicted_close']:.2f}")
            print(f"    Change: {metrics['percent_change']:+.2f}%")
            print(f"    Volatility: {metrics['volatility']:.4f}")
            print(f"    Trend: {metrics['trend']}\n")
        except Exception as e:
            print(f"  ❌ Error generating forecast: {e}")
            return {'success': False, 'error': str(e)}
        
        # Step 4: Agent decision
        print("🤖 Step 4: Agent decision-making...")
        try:
            decision = self.agent.evaluate(metrics, forecast_confidence=forecast['confidence'])
            
            if decision.should_alert:
                print(f"  ⚠️  ALERT TRIGGERED")
                print(f"    Type: {decision.alert_type.value}")
                print(f"    Confidence: {decision.confidence.value}")
                print(f"    Reason: {decision.reason}")
            elif decision.suppressed:
                print(f"  🚫 Alert suppressed: {decision.suppression_reason}")
            else:
                print(f"  ✅ No alert - conditions normal")
            print()
        except Exception as e:
            print(f"  ❌ Error in decision logic: {e}")
            return {'success': False, 'error': str(e)}
        
        # Step 5: LLM explanation
        print("💬 Step 5: Generating LLM explanation...")
        try:
            explanation = self.explainer.generate_explanation(decision)
            print(f"  ✓ Explanation generated")
            print(f"    \"{explanation.explanation[:100]}...\"\n")
        except Exception as e:
            print(f"  ⚠️  Error generating explanation: {e}")
            # Continue with template explanation
            explanation = None
        
        # Step 6: Output alert
        print("📝 Step 6: Logging alert...")
        try:
            # Format output
            alert_data = format_explanation_for_output(decision, explanation)
            
            # Log to all outputs
            self.alert_system.log_alert(
                alert_data,
                stock_symbol=self.stock_symbol,
                date=data['Date'].max().strftime("%Y-%m-%d")
            )
            
            print(f"  ✓ Alert logged successfully\n")
        except Exception as e:
            print(f"  ❌ Error logging alert: {e}")
            return {'success': False, 'error': str(e)}
        
        # Success
        print("✨ Agent workflow completed successfully!\n")
        
        return {
            'success': True,
            'alert_triggered': decision.should_alert,
            'alert_type': decision.alert_type.value if decision.should_alert else None,
            'confidence': decision.confidence.value,
            'metrics': metrics,
            'explanation': explanation.explanation if explanation else None
        }
    
    def run_batch(self, window_size: int = 30) -> list:
        """
        Run agent on multiple time windows (simulates daily monitoring).
        
        Args:
            window_size: Size of rolling window for forecasting
            
        Returns:
            List of results for each window
        """
        print(f"🔄 Running batch analysis with {window_size}-day windows...\n")
        
        # Load full data
        data = load_market_data(self.data_path)
        
        results = []
        
        # Iterate through windows
        for i in range(window_size, len(data)):
            window_data = data.iloc[:i]
            date = data.iloc[i]['Date']
            
            print(f"Analyzing window ending {date}...")
            
            # Fit and forecast
            self.forecaster.fit(window_data)
            forecast = self.forecaster.forecast(steps=1)
            metrics = self.forecaster.calculate_metrics(window_data, forecast)
            
            # Decision
            decision = self.agent.evaluate(metrics)
            
            # Explanation
            explanation = self.explainer.generate_explanation(decision)
            
            # Log
            alert_data = format_explanation_for_output(decision, explanation)
            self.alert_system.log_alert(
                alert_data,
                stock_symbol=self.stock_symbol,
                date=date.strftime("%Y-%m-%d")
            )
            
            results.append({
                'date': date,
                'alert': decision.should_alert,
                'type': decision.alert_type.value if decision.should_alert else None
            })
        
        print(f"\n✓ Batch analysis complete: {len(results)} windows analyzed")
        return results


def main():
    """Command-line interface for the agent."""
    parser = argparse.ArgumentParser(
        description="Market Data Forecaster & Alert Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main_agent.py --data ../data/sample_stock_data.csv
  
  # With specific rules
  python main_agent.py --data ../data/sample_stock_data.csv --rules aggressive
  
  # Batch mode
  python main_agent.py --data ../data/sample_stock_data.csv --batch --window 30
        """
    )
    
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Path to market data CSV file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='../outputs',
        help='Output directory for alerts (default: ../outputs)'
    )
    
    parser.add_argument(
        '--rules',
        type=str,
        choices=['conservative', 'moderate', 'aggressive'],
        default='moderate',
        help='Alert rules preset (default: moderate)'
    )
    
    parser.add_argument(
        '--stock',
        type=str,
        default='SAMPLE',
        help='Stock ticker symbol (default: SAMPLE)'
    )
    
    parser.add_argument(
        '--llm-provider',
        type=str,
        default='openai',
        help='LLM provider (default: openai)'
    )
    
    parser.add_argument(
        '--llm-model',
        type=str,
        default='gpt-4o-mini',
        help='LLM model name (default: gpt-4o-mini)'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Run in batch mode (analyze multiple windows)'
    )
    
    parser.add_argument(
        '--window',
        type=int,
        default=30,
        help='Window size for batch mode (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = MarketAlertAgent(
        data_path=args.data,
        output_dir=args.output,
        rules_preset=args.rules,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        stock_symbol=args.stock
    )
    
    # Run
    if args.batch:
        results = agent.run_batch(window_size=args.window)
        print(f"\n📊 Batch Results: {sum(r['alert'] for r in results)} alerts triggered")
    else:
        result = agent.run()
        
        if not result['success']:
            print(f"❌ Agent failed: {result['error']}")
            sys.exit(1)
    
    print("\n🎉 Done! Check outputs directory for results.")


if __name__ == "__main__":
    main()
