"""
RAG System Demo & Validation Script
====================================
Demonstrates how RAG enhances market alert explanations with
historical context and domain knowledge.
"""

import sys
from pathlib import Path
import json

# Add scripts to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from rag_system import MarketRAGSystem, create_default_knowledge_base
from llm_explainer import LLMExplainer
from agent_logic import AlertAgent, AlertDecision, AlertType, ConfidenceLevel


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_rag_retrieval():
    """Demo 1: Direct RAG context retrieval."""
    print_section("DEMO 1: RAG Context Retrieval")
    
    # Initialize RAG system
    print("🔧 Initializing RAG system...")
    rag = MarketRAGSystem(use_embeddings=False)
    
    # Example scenario: Sharp price drop
    test_metrics = {
        'last_close': 150.0,
        'predicted_close': 144.0,
        'percent_change': -4.0,
        'volatility': 0.035,
        'trend': 'downward'
    }
    
    print("\n📊 Current Market Situation:")
    print(f"   Last Close: ${test_metrics['last_close']:.2f}")
    print(f"   Predicted: ${test_metrics['predicted_close']:.2f}")
    print(f"   Change: {test_metrics['percent_change']:+.1f}%")
    print(f"   Volatility: {test_metrics['volatility']:.4f}")
    
    # Retrieve context
    print("\n🔍 Retrieving historical context...")
    context = rag.retrieve_context(
        current_metrics=test_metrics,
        alert_type='price_drop',
        stock_symbol='AAPL',
        top_k=5
    )
    
    # Display results
    print(f"\n✅ Context Retrieved!")
    print(f"   Relevance Score: {context.relevance_score:.0%}")
    print(f"   Similar Patterns: {len(context.similar_patterns)}")
    print(f"   Past Alerts: {len(context.past_alerts)}")
    print(f"   Market Insights: {len(context.market_insights)}")
    
    # Show formatted context
    print("\n📋 Formatted Context for LLM:")
    print("-" * 70)
    print(rag.format_context_for_llm(context))
    print("-" * 70)


def demo_comparison_without_rag():
    """Demo 2: Explanation WITHOUT RAG."""
    print_section("DEMO 2: Standard Explanation (No RAG)")
    
    # Create mock decision
    decision = AlertDecision(
        should_alert=True,
        alert_type=AlertType.PRICE_DROP,
        confidence=ConfidenceLevel.HIGH,
        reason="Predicted price drop of 4.5% exceeds threshold",
        metrics={
            'last_close': 155.0,
            'predicted_close': 148.0,
            'percent_change': -4.5,
            'volatility': 0.025,
            'trend': 'downward'
        }
    )
    
    # Generate explanation WITHOUT RAG
    print("🤖 Generating explanation (template-based, no RAG)...\n")
    explainer = LLMExplainer(use_rag=False)
    result = explainer.generate_explanation(decision)
    
    print("📝 Explanation:")
    print("-" * 70)
    print(result.explanation)
    print("-" * 70)
    
    return decision


def demo_comparison_with_rag(decision):
    """Demo 3: Explanation WITH RAG."""
    print_section("DEMO 3: RAG-Enhanced Explanation")
    
    # Generate explanation WITH RAG
    print("🤖 Generating explanation (with RAG context)...\n")
    explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
    result = explainer.generate_explanation(decision)
    
    print("📝 Enhanced Explanation:")
    print("-" * 70)
    print(result.explanation)
    print("-" * 70)
    
    print("\n💡 Notice: The RAG-enhanced version may reference:")
    print("   • Similar historical patterns")
    print("   • Past alert outcomes")
    print("   • Market domain knowledge")
    print("   • Statistical precedents")


def demo_multiple_scenarios():
    """Demo 4: Multiple alert scenarios."""
    print_section("DEMO 4: Multiple Alert Scenarios")
    
    scenarios = [
        {
            'name': 'Price Spike',
            'decision': AlertDecision(
                should_alert=True,
                alert_type=AlertType.PRICE_SPIKE,
                confidence=ConfidenceLevel.MEDIUM,
                reason="Sharp upward movement detected",
                metrics={
                    'last_close': 145.0,
                    'predicted_close': 153.0,
                    'percent_change': 5.5,
                    'volatility': 0.022,
                    'trend': 'upward'
                }
            )
        },
        {
            'name': 'Volatility Spike',
            'decision': AlertDecision(
                should_alert=True,
                alert_type=AlertType.VOLATILITY_SPIKE,
                confidence=ConfidenceLevel.HIGH,
                reason="Volatility exceeds normal ranges",
                metrics={
                    'last_close': 150.0,
                    'predicted_close': 149.0,
                    'percent_change': -0.7,
                    'volatility': 0.042,
                    'trend': 'volatile'
                }
            )
        }
    ]
    
    rag_explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['name']} ---\n")
        
        decision = scenario['decision']
        print(f"Alert Type: {decision.alert_type.value}")
        print(f"Confidence: {decision.confidence.value}")
        print(f"Change: {decision.metrics['percent_change']:+.1f}%")
        
        result = rag_explainer.generate_explanation(decision)
        
        print(f"\nExplanation:")
        print(result.explanation)
        print()


def demo_rag_statistics():
    """Demo 5: RAG system statistics."""
    print_section("DEMO 5: RAG System Statistics")
    
    rag = MarketRAGSystem()
    
    print(f"📊 System Statistics:")
    print(f"   Historical Records: {len(rag.historical_data)}")
    print(f"   Alert History Size: {len(rag.alert_history)}")
    print(f"   Vector Store: {'Enabled' if rag.use_embeddings else 'Disabled (similarity search)'}")
    print(f"   Knowledge Base: {rag.knowledge_base_path}")
    
    # Test retrieval performance
    test_cases = [
        {'percent_change': -4.5, 'volatility': 0.03, 'type': 'price_drop'},
        {'percent_change': 5.2, 'volatility': 0.025, 'type': 'price_spike'},
        {'percent_change': -1.0, 'volatility': 0.05, 'type': 'volatility_spike'},
    ]
    
    print(f"\n🧪 Retrieval Performance Test:")
    
    for i, case in enumerate(test_cases, 1):
        context = rag.retrieve_context(
            current_metrics=case,
            alert_type=case['type'],
            stock_symbol='AAPL'
        )
        print(f"   Test {i}: {case['type']}")
        print(f"      Relevance: {context.relevance_score:.0%}")
        print(f"      Patterns: {len(context.similar_patterns)}")
        print(f"      Insights: {len(context.market_insights)}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  RAG-ENHANCED MARKET ALERT SYSTEM - DEMO")
    print("="*70)
    print("\nThis demo showcases how RAG (Retrieval-Augmented Generation)")
    print("enhances market alert explanations with historical context.\n")
    
    try:
        # Setup: Create knowledge base if needed
        print("🔧 Setup: Creating knowledge base...")
        create_default_knowledge_base()
        print("✅ Knowledge base ready\n")
        
        # Run demos
        demo_rag_retrieval()
        
        decision = demo_comparison_without_rag()
        demo_comparison_with_rag(decision)
        
        demo_multiple_scenarios()
        demo_rag_statistics()
        
        # Summary
        print_section("SUMMARY")
        print("✅ RAG Integration Highlights:")
        print("   • Retrieves similar historical patterns")
        print("   • References past alert outcomes")
        print("   • Incorporates domain knowledge")
        print("   • Reduces LLM hallucinations")
        print("   • Improves explanation accuracy")
        print("\n📚 For more details, see: RAG_INTEGRATION.md")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
