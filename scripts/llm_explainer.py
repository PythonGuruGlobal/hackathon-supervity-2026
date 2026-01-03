
import os
from typing import Dict, Optional
from dataclasses import dataclass
from agent_logic import AlertDecision, AlertType

# LangChain imports (will be optional if not available)
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


@dataclass
class ExplanationResult:
    """Result of explanation generation."""
    explanation: str
    reasoning_steps: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class LLMExplainer:
    """
    LLM-powered explanation generator for market alerts.
    
    This is what makes the system "agentic" - the LLM provides
    reasoning and context that pure statistical models cannot.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Initialize LLM explainer.
        
        Args:
            provider: "openai", "gemini", or "local"
            model: Model name (e.g., "gpt-4o-mini", "gemini-pro")
            api_key: API key (if not set in environment)
            temperature: Temperature for generation (lower = more deterministic)
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        
        # Set API key
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the LLM based on provider."""
        if not LANGCHAIN_AVAILABLE:
            print("⚠️ LangChain not installed. Using fallback template-based explanations.")
            return None
        
        if self.provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️ OPENAI_API_KEY not set. Using fallback explanations.")
                return None
            
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=api_key
            )
        
        # Add other providers as needed
        else:
            print(f"⚠️ Provider {self.provider} not implemented. Using fallback.")
            return None
    
    def generate_explanation(self, decision: AlertDecision, context: Dict = None) -> ExplanationResult:
        """
        Generate human-readable explanation for an alert decision.
        
        Args:
            decision: AlertDecision from agent
            context: Additional context (e.g., news, historical patterns)
            
        Returns:
            ExplanationResult with explanation text
        """
        if not decision.should_alert:
            return ExplanationResult(
                explanation="No significant market movements detected. All metrics within normal ranges.",
                success=True
            )
        
        # Use LLM if available, otherwise use template
        if self.llm:
            return self._generate_llm_explanation(decision, context)
        else:
            return self._generate_template_explanation(decision, context)
    
    def _generate_llm_explanation(self, decision: AlertDecision, context: Dict) -> ExplanationResult:
        """Generate explanation using LLM."""
        try:
            # Create prompt
            prompt = self._build_prompt(decision, context)
            
            # Call LLM
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            explanation = response.content.strip()
            
            return ExplanationResult(
                explanation=explanation,
                success=True
            )
        
        except Exception as e:
            # Fallback to template if LLM fails
            print(f"⚠️ LLM call failed: {e}. Using fallback.")
            return self._generate_template_explanation(decision, context)
    
    def _build_prompt(self, decision: AlertDecision, context: Dict) -> str:
        """Build prompt for LLM."""
        metrics = decision.metrics
        
        prompt = f"""
Explain the following market alert in simple, professional financial terms.

**Alert Type**: {decision.alert_type.value}
**Confidence**: {decision.confidence.value}
**Reason**: {decision.reason}

**Market Data**:
- Last Closing Price: ${metrics.get('last_close', 0):.2f}
- Predicted Close: ${metrics.get('predicted_close', 0):.2f}
- Percentage Change: {metrics.get('percent_change', 0):+.2f}%
- Current Volatility: {metrics.get('volatility', 0):.4f}
- Trend: {metrics.get('trend', 'unknown')}

**Instructions**:
1. Explain why this alert was triggered in 2-3 sentences
2. Provide context about what this means for market participants
3. Mention potential causes (volatility, trend changes, magnitude)
4. Keep it professional but accessible
5. Do NOT give investment advice

Write a clear, concise explanation:
"""
        return prompt.strip()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM."""
        return """You are a financial market analyst AI that explains trading alerts to portfolio managers and risk teams. 

Your explanations should:
- Be clear and concise (2-3 sentences)
- Use professional financial terminology
- Explain the reasoning, not just the numbers
- Provide context about market implications
- Never give investment advice or recommendations
- Focus on what the data suggests, not predictions

Example good explanation:
"The forecast indicates a sharp 4.5% drop following increased volatility over the last 3 days. This suggests possible market uncertainty or reaction to external events. The elevated volatility amplifies the significance of this predicted movement."

Example bad explanation:
"The stock will drop 4.5%. You should sell immediately and avoid losses."
"""
    
    def _generate_template_explanation(self, decision: AlertDecision, context: Dict) -> ExplanationResult:
        """Generate explanation using templates (fallback when LLM unavailable)."""
        metrics = decision.metrics
        alert_type = decision.alert_type
        
        # Template-based explanations
        templates = {
            AlertType.PRICE_DROP: (
                f"The forecast indicates a significant {abs(metrics.get('percent_change', 0)):.1f}% price decline "
                f"from ${metrics.get('last_close', 0):.2f} to ${metrics.get('predicted_close', 0):.2f}. "
                f"With current volatility at {metrics.get('volatility', 0):.4f}, this movement exceeds normal fluctuations "
                f"and warrants attention from risk management teams."
            ),
            
            AlertType.PRICE_SPIKE: (
                f"The forecast shows an unusual {metrics.get('percent_change', 0):.1f}% price increase "
                f"from ${metrics.get('last_close', 0):.2f} to ${metrics.get('predicted_close', 0):.2f}. "
                f"This sharp upward movement, combined with {metrics.get('trend', 'current')} trend patterns, "
                f"suggests heightened market interest or positive sentiment shift."
            ),
            
            AlertType.VOLATILITY_SPIKE: (
                f"Market volatility has spiked to {metrics.get('volatility', 0):.4f}, "
                f"significantly above normal levels. This increased uncertainty amplifies risk and "
                f"may indicate reaction to market events or upcoming announcements. "
                f"Position sizing and stop-losses should be reviewed."
            ),
            
            AlertType.TREND_REVERSAL: (
                f"Technical analysis indicates a potential trend reversal with the market "
                f"transitioning to a {metrics.get('trend', 'new')} pattern. "
                f"This shift, combined with a {metrics.get('percent_change', 0):+.1f}% forecast change, "
                f"suggests a change in market dynamics that may require strategy adjustment."
            )
        }
        
        explanation = templates.get(alert_type, decision.reason)
        
        return ExplanationResult(
            explanation=explanation,
            success=True
        )
    
    def generate_no_alert_summary(self, metrics: Dict) -> str:
        """Generate summary when no alert is triggered."""
        return (
            f"Market conditions remain stable. Current price at ${metrics.get('last_close', 0):.2f} "
            f"with predicted change of {metrics.get('percent_change', 0):+.1f}% and "
            f"volatility at {metrics.get('volatility', 0):.4f}. All metrics within normal ranges."
        )


def format_explanation_for_output(decision: AlertDecision, explanation: ExplanationResult) -> Dict:
    """
    Format explanation into structured output.
    
    Args:
        decision: AlertDecision from agent
        explanation: ExplanationResult from LLM
        
    Returns:
        Dictionary ready for JSON/CSV output
    """
    return {
        'alert_triggered': decision.should_alert,
        'alert_type': decision.alert_type.value if decision.should_alert else None,
        'confidence': decision.confidence.value,
        'technical_reason': decision.reason,
        'human_explanation': explanation.explanation,
        'suppressed': decision.suppressed,
        'suppression_reason': decision.suppression_reason,
        'metrics': decision.metrics
    }


if __name__ == "__main__":
    # Example usage
    print("=== LLM Explainer Demo ===\n")
    
    # Initialize explainer (will use templates if no API key)
    explainer = LLMExplainer(provider="openai", model="gpt-4o-mini")
    
    # Create a mock alert decision
    from agent_logic import AlertDecision, AlertType, ConfidenceLevel
    
    decision = AlertDecision(
        should_alert=True,
        alert_type=AlertType.PRICE_DROP,
        confidence=ConfidenceLevel.MEDIUM,
        reason="Predicted price drop of 4.5% exceeds threshold",
        metrics={
            'last_close': 155.0,
            'predicted_close': 148.0,
            'percent_change': -4.5,
            'volatility': 0.025,
            'trend': 'downward'
        }
    )
    
    # Generate explanation
    result = explainer.generate_explanation(decision)
    
    print("Alert Decision:")
    print(f"  Type: {decision.alert_type.value}")
    print(f"  Confidence: {decision.confidence.value}")
    print(f"  Technical: {decision.reason}\n")
    
    print("Human Explanation:")
    print(f"  {result.explanation}\n")
    
    # Format for output
    output = format_explanation_for_output(decision, result)
    print("Structured Output:")
    import json
    print(json.dumps(output, indent=2))
