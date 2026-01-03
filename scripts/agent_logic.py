"""
Agent Decision Logic
====================
Rule-based decision system that determines when to trigger alerts.
Includes self-checking mechanisms to prevent alert spam.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class AlertType(Enum):
    """Types of alerts that can be triggered."""
    PRICE_DROP = "price_drop"
    PRICE_SPIKE = "price_spike"
    VOLATILITY_SPIKE = "volatility_spike"
    TREND_REVERSAL = "trend_reversal"
    NONE = "none"


class ConfidenceLevel(Enum):
    """Confidence levels for alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AlertDecision:
    """Result of agent decision-making process."""
    should_alert: bool
    alert_type: AlertType
    confidence: ConfidenceLevel
    reason: str
    metrics: Dict[str, float]
    suppressed: bool = False
    suppression_reason: Optional[str] = None


class AlertAgent:
    """
    Agentic decision-making system for market alerts.
    
    This agent:
    1. Evaluates forecast metrics against thresholds
    2. Makes decisions about alert triggers
    3. Self-checks to avoid spam
    4. Tracks alert history
    """
    
    def __init__(
        self,
        price_drop_threshold: float = 4.0,
        price_spike_threshold: float = 5.0,
        volatility_threshold: float = 0.03,
        min_confidence_threshold: float = 0.6,
        alert_cooldown_hours: int = 24
    ):
        """
        Initialize alert agent with configurable thresholds.
        
        Args:
            price_drop_threshold: Percentage drop to trigger alert
            price_spike_threshold: Percentage spike to trigger alert
            volatility_threshold: Volatility level to trigger alert
            min_confidence_threshold: Minimum confidence to send alert
            alert_cooldown_hours: Hours to wait before repeating similar alert
        """
        self.price_drop_threshold = price_drop_threshold
        self.price_spike_threshold = price_spike_threshold
        self.volatility_threshold = volatility_threshold
        self.min_confidence_threshold = min_confidence_threshold
        self.alert_cooldown_hours = alert_cooldown_hours
        
        # Alert history for self-checking
        self.alert_history: List[Dict] = []
        
    def evaluate(self, metrics: Dict[str, float], forecast_confidence: float = 0.95) -> AlertDecision:
        """
        Main decision-making method.
        
        Args:
            metrics: Dictionary with forecast metrics
            forecast_confidence: Confidence level from forecast model
            
        Returns:
            AlertDecision with trigger decision and reasoning
        """
        # Step 1: Check all alert conditions
        alert_type, reason = self._check_alert_conditions(metrics)
        
        # Step 2: Calculate confidence level
        confidence = self._calculate_confidence(metrics, forecast_confidence, alert_type)
        
        # Step 3: Initial decision
        should_alert = alert_type != AlertType.NONE
        
        # Step 4: Self-check (prevent spam and low-confidence alerts)
        if should_alert:
            suppressed, suppression_reason = self._self_check(alert_type, confidence, metrics)
            if suppressed:
                return AlertDecision(
                    should_alert=False,
                    alert_type=alert_type,
                    confidence=confidence,
                    reason=reason,
                    metrics=metrics,
                    suppressed=True,
                    suppression_reason=suppression_reason
                )
        
        # Step 5: Record alert if triggered
        if should_alert:
            self._record_alert(alert_type, confidence, metrics)
        
        return AlertDecision(
            should_alert=should_alert,
            alert_type=alert_type,
            confidence=confidence,
            reason=reason,
            metrics=metrics
        )
    
    def _check_alert_conditions(self, metrics: Dict[str, float]) -> Tuple[AlertType, str]:
        """
        Check all alert conditions and return the most critical one.
        
        Args:
            metrics: Dictionary with forecast metrics
            
        Returns:
            Tuple of (AlertType, reason string)
        """
        pct_change = metrics.get('percent_change', 0)
        volatility = metrics.get('volatility', 0)
        trend = metrics.get('trend', 'stable')
        
        # Priority 1: Significant price drop
        if pct_change <= -self.price_drop_threshold:
            return (
                AlertType.PRICE_DROP,
                f"Predicted price drop of {abs(pct_change):.1f}% exceeds threshold"
            )
        
        # Priority 2: Significant price spike
        if pct_change >= self.price_spike_threshold:
            return (
                AlertType.PRICE_SPIKE,
                f"Predicted price spike of {pct_change:.1f}% exceeds threshold"
            )
        
        # Priority 3: Volatility spike
        if volatility >= self.volatility_threshold:
            return (
                AlertType.VOLATILITY_SPIKE,
                f"Volatility spike detected ({volatility:.4f} > {self.volatility_threshold})"
            )
        
        # Priority 4: Trend reversal after stability
        # This is a more complex condition - checks for reversal
        # You could enhance this with more sophisticated logic
        if self._detect_trend_reversal(metrics):
            return (
                AlertType.TREND_REVERSAL,
                f"Trend reversal detected: moving to {trend} pattern"
            )
        
        return (AlertType.NONE, "No significant alerts")
    
    def _detect_trend_reversal(self, metrics: Dict[str, float]) -> bool:
        """
        Detect if a trend reversal is happening.
        
        This is a simplified version. In production, you'd track
        historical trends and detect changes.
        """
        # For now, use a simple heuristic
        pct_change = metrics.get('percent_change', 0)
        trend = metrics.get('trend', 'stable')
        
        # If previously stable/upward and now showing downward movement
        if trend == 'downward' and abs(pct_change) > 2.0:
            return True
            
        return False
    
    def _calculate_confidence(
        self,
        metrics: Dict[str, float],
        forecast_confidence: float,
        alert_type: AlertType
    ) -> ConfidenceLevel:
        """
        Calculate confidence level for the alert.
        
        Considers:
        - Forecast model confidence
        - Magnitude of the signal
        - Volatility (higher volatility = lower confidence)
        """
        if alert_type == AlertType.NONE:
            return ConfidenceLevel.LOW
        
        # Start with base confidence from model
        confidence_score = forecast_confidence
        
        # Adjust based on signal strength
        pct_change = abs(metrics.get('percent_change', 0))
        if pct_change > 7.0:  # Very strong signal
            confidence_score *= 1.1
        elif pct_change < 3.0:  # Weak signal
            confidence_score *= 0.9
        
        # Adjust based on volatility
        volatility = metrics.get('volatility', 0)
        if volatility > 0.05:  # High volatility = less confidence
            confidence_score *= 0.85
        
        # Map to confidence level
        if confidence_score >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _self_check(
        self,
        alert_type: AlertType,
        confidence: ConfidenceLevel,
        metrics: Dict[str, float]
    ) -> Tuple[bool, Optional[str]]:
        """
        Self-check mechanism to prevent alert spam.
        
        Returns:
            Tuple of (should_suppress, reason)
        """
        # Check 1: Confidence too low?
        if confidence == ConfidenceLevel.LOW:
            return (True, "Confidence level too low")
        
        # Check 2: Similar alert recently fired?
        if self._has_recent_similar_alert(alert_type):
            return (True, f"Similar alert fired within last {self.alert_cooldown_hours}h")
        
        # Check 3: Too many alerts today?
        if self._exceeds_daily_limit():
            return (True, "Daily alert limit reached")
        
        return (False, None)
    
    def _has_recent_similar_alert(self, alert_type: AlertType) -> bool:
        """Check if similar alert was recently triggered."""
        cutoff_time = datetime.now() - timedelta(hours=self.alert_cooldown_hours)
        
        for alert in self.alert_history:
            if alert['type'] == alert_type and alert['timestamp'] > cutoff_time:
                return True
        
        return False
    
    def _exceeds_daily_limit(self, max_alerts: int = 5) -> bool:
        """Check if daily alert limit is exceeded."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_alerts = [
            alert for alert in self.alert_history
            if alert['timestamp'] >= today_start
        ]
        
        return len(today_alerts) >= max_alerts
    
    def _record_alert(self, alert_type: AlertType, confidence: ConfidenceLevel, metrics: Dict):
        """Record alert in history for self-checking."""
        self.alert_history.append({
            'type': alert_type,
            'confidence': confidence,
            'timestamp': datetime.now(),
            'metrics': metrics.copy()
        })
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alert history."""
        return {
            'total_alerts': len(self.alert_history),
            'alerts_today': self._count_alerts_today(),
            'last_alert': self.alert_history[-1] if self.alert_history else None
        }
    
    def _count_alerts_today(self) -> int:
        """Count alerts triggered today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return len([a for a in self.alert_history if a['timestamp'] >= today_start])


# Decision rules configuration presets
CONSERVATIVE_RULES = {
    'price_drop_threshold': 5.0,
    'price_spike_threshold': 6.0,
    'volatility_threshold': 0.04,
    'min_confidence_threshold': 0.75,
    'alert_cooldown_hours': 48
}

MODERATE_RULES = {
    'price_drop_threshold': 4.0,
    'price_spike_threshold': 5.0,
    'volatility_threshold': 0.03,
    'min_confidence_threshold': 0.65,
    'alert_cooldown_hours': 24
}

AGGRESSIVE_RULES = {
    'price_drop_threshold': 3.0,
    'price_spike_threshold': 4.0,
    'volatility_threshold': 0.02,
    'min_confidence_threshold': 0.55,
    'alert_cooldown_hours': 12
}


if __name__ == "__main__":
    # Example usage
    print("=== Alert Agent Demo ===\n")
    
    # Initialize agent with moderate rules
    agent = AlertAgent(**MODERATE_RULES)
    
    # Simulate different scenarios
    scenarios = [
        {
            'name': 'Major Drop',
            'metrics': {
                'last_close': 155.0,
                'predicted_close': 148.0,
                'percent_change': -4.5,
                'volatility': 0.025,
                'trend': 'downward'
            }
        },
        {
            'name': 'Minor Drop',
            'metrics': {
                'last_close': 155.0,
                'predicted_close': 152.0,
                'percent_change': -1.9,
                'volatility': 0.015,
                'trend': 'stable'
            }
        },
        {
            'name': 'High Volatility',
            'metrics': {
                'last_close': 155.0,
                'predicted_close': 156.0,
                'percent_change': 0.6,
                'volatility': 0.045,
                'trend': 'stable'
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        decision = agent.evaluate(scenario['metrics'])
        
        print(f"  Alert: {'YES' if decision.should_alert else 'NO'}")
        if decision.should_alert:
            print(f"  Type: {decision.alert_type.value}")
            print(f"  Confidence: {decision.confidence.value}")
            print(f"  Reason: {decision.reason}")
        elif decision.suppressed:
            print(f"  Suppressed: {decision.suppression_reason}")
        print()
