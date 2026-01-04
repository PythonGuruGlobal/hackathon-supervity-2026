# Evaluation & Testing Notes

## Evaluation Metrics

### 1. Forecasting Accuracy

**Metrics Used:**
- **RMSE (Root Mean Squared Error)**: Measures prediction error magnitude
- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and actual
- **MAPE (Mean Absolute Percentage Error)**: Percentage-based error metric

**Benchmark:**
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Example evaluation
actual = test_data['Close']
predicted = forecasts
rmse = np.sqrt(mean_squared_error(actual, predicted))
mae = mean_absolute_error(actual, predicted)
mape = np.mean(np.abs((actual - predicted) / actual)) * 100

print(f"RMSE: ${rmse:.2f}")
print(f"MAE: ${mae:.2f}")
print(f"MAPE: {mape:.2f}%")
```

**Expected Performance:**
- RMSE: < $5.00 (depends on price range)
- MAPE: < 3% for stable markets, < 5% for volatile markets

### 2. Alert Precision & Recall

**Definitions:**
- **Precision**: Of all alerts triggered, how many were correct?
- **Recall**: Of all true events, how many did we catch?
- **F1-Score**: Harmonic mean of precision and recall

**Manual Labeling:**
After running the system, manually label each alert:
- True Positive (TP): Alert triggered, significant event occurred
- False Positive (FP): Alert triggered, no significant event
- False Negative (FN): No alert, but significant event occurred
- True Negative (TN): No alert, no event (correctly ignored)

**Calculation:**
```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Target Performance:**
- Precision: > 70% (minimize false positives)
- Recall: > 60% (catch most important events)
- F1-Score: > 65%

### 3. False Positive Rate

**Critical Metric:** Too many false positives = alert fatigue

**Target:** < 20% false positive rate

**Evaluation:**
Run system on 30 days of data, manually review each alert:
```
False Positive Rate = FP / (FP + TN)
```

### 4. LLM Explanation Quality

**Evaluation Method:** Human evaluation (qualitative)

**Rubric (1-5 scale):**
1. **Clarity**: Is the explanation easy to understand?
2. **Accuracy**: Does it correctly describe the situation?
3. **Relevance**: Does it provide useful context?
4. **Professionalism**: Is it appropriate for financial professionals?
5. **Actionability**: Does it help with decision-making?

**Process:**
- Sample 20 alerts
- Rate each explanation on all criteria
- Calculate average scores

**Target:** Average score > 4.0 on all criteria

---

## Guardrails

### 1. Threshold Validation

**Purpose:** Prevent oversensitive or undersensitive alerts

**Implementation:**
- **Price drop threshold:** 4% (configurable)
- **Price spike threshold:** 5% (configurable)
- **Volatility threshold:** 0.03 (configurable)

**Testing:**
```python
# Test with different thresholds
for threshold in [2.0, 3.0, 4.0, 5.0, 6.0]:
    agent = AlertAgent(price_drop_threshold=threshold)
    # Run on test data
    # Measure alert frequency
```

### 2. Confidence Scoring

**Purpose:** Suppress low-confidence alerts

**Implementation:**
- Low confidence alerts are suppressed
- Confidence based on:
  - Model confidence (ARIMA confidence intervals)
  - Signal strength (magnitude of change)
  - Volatility (higher = lower confidence)

**Testing:**
```python
# Verify confidence calculation
metrics_low = {'percent_change': -2.0, 'volatility': 0.06}
metrics_high = {'percent_change': -7.0, 'volatility': 0.02}

# Low signal + high volatility = LOW confidence
# High signal + low volatility = HIGH confidence
```

### 3. Deduplication Logic

**Purpose:** Avoid alert spam for ongoing situations

**Implementation:**
- Track alert history
- Cooldown period: 24 hours (configurable)
- Similar alerts within cooldown are suppressed

**Testing:**
```python
# Simulate repeated alerts
agent = AlertAgent(alert_cooldown_hours=24)

# First alert should trigger
decision1 = agent.evaluate(metrics)
assert decision1.should_alert == True

# Second alert within 24h should be suppressed
decision2 = agent.evaluate(metrics)
assert decision2.suppressed == True
```

### 4. Rate Limiting

**Purpose:** Maximum alerts per day (prevent spam)

**Implementation:**
- Max 5 alerts per day (configurable)
- After limit, additional alerts are suppressed

**Testing:**
```python
# Trigger 6 alerts in one day
for i in range(6):
    decision = agent.evaluate(high_alert_metrics)
    if i < 5:
        assert decision.should_alert
    else:
        assert decision.suppressed
        assert "daily limit" in decision.suppression_reason
```

---

## Test Cases

### Test Case 1: Major Price Drop
```python
metrics = {
    'last_close': 155.0,
    'predicted_close': 145.0,
    'percent_change': -6.45,
    'volatility': 0.02,
    'trend': 'downward'
}

decision = agent.evaluate(metrics)
assert decision.should_alert == True
assert decision.alert_type == AlertType.PRICE_DROP
assert decision.confidence in [ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]
```

### Test Case 2: Minor Movement (No Alert)
```python
metrics = {
    'last_close': 155.0,
    'predicted_close': 154.0,
    'percent_change': -0.65,
    'volatility': 0.015,
    'trend': 'stable'
}

decision = agent.evaluate(metrics)
assert decision.should_alert == False
```

### Test Case 3: High Volatility
```python
metrics = {
    'last_close': 155.0,
    'predicted_close': 156.0,
    'percent_change': 0.6,
    'volatility': 0.045,
    'trend': 'stable'
}

decision = agent.evaluate(metrics)
assert decision.should_alert == True
assert decision.alert_type == AlertType.VOLATILITY_SPIKE
```

### Test Case 4: Alert Suppression (Duplicate)
```python
# First alert
decision1 = agent.evaluate(high_alert_metrics)
assert decision1.should_alert == True

# Immediate duplicate
decision2 = agent.evaluate(high_alert_metrics)
assert decision2.suppressed == True
```

---

## Limitations

### 1. Data Limitations
- **Historical data only**: Not real-time streaming
- **Single asset**: Doesn't analyze portfolio correlations
- **No external data**: Doesn't incorporate news, sentiment, economic indicators

### 2. Model Limitations
- **ARIMA assumptions**: Assumes stationarity, may not capture regime changes
- **Short-term focus**: Optimized for 1-day forecasts
- **No multi-step forecasting**: Doesn't predict multiple days ahead

### 3. Agent Limitations
- **Rule-based decisions**: Not adaptive (could use ML-based anomaly detection)
- **Fixed thresholds**: Doesn't adapt to changing market conditions
- **No learning**: Doesn't improve from feedback

### 4. LLM Limitations
- **Post-hoc explanations**: Explains after decision, not part of decision
- **No causal reasoning**: Correlational, not causal
- **API dependency**: Requires external API (cost, latency, availability)

---

## Assumptions

1. **Market Efficiency**: Assumes markets are somewhat predictable in short term
2. **Stationarity**: Assumes price series is stationary after differencing
3. **Normal Distribution**: Assumes returns follow approximately normal distribution
4. **No External Shocks**: Doesn't account for black swan events
5. **Linear Relationships**: ARIMA assumes linear dependencies
6. **Consistent Volatility**: Assumes volatility changes gradually

---

## Future Improvements

### Short-term
1. Add Prophet model as alternative to ARIMA
2. Implement backtesting framework
3. Add more alert types (momentum, support/resistance)
4. Integrate real-time data feeds (Alpha Vantage, Yahoo Finance API)

### Medium-term
1. Multi-asset portfolio monitoring
2. Sentiment analysis from news/social media
3. ML-based anomaly detection (Isolation Forest, Autoencoders)
4. Adaptive thresholds based on historical performance

### Long-term
1. Reinforcement learning for alert optimization
2. Multi-step forecasting with uncertainty quantification
3. Causal inference for root cause analysis
4. Integration with trading platforms

---

## Running Evaluations

### Quick Evaluation
```bash
# Run on sample data
python scripts/main_agent.py --data data/sample_stock_data.csv

# Check outputs
cat outputs/alerts.csv
```

### Batch Evaluation
```bash
# Analyze multiple windows
python scripts/main_agent.py --data data/sample_stock_data.csv --batch --window 30

# Generate summary
python -c "
from scripts.alert_system import AlertSystem
alert_sys = AlertSystem('outputs')
print(alert_sys.generate_summary_report())
"
```

### Notebook Evaluation
```bash
# Interactive evaluation
jupyter notebook notebooks/market_agent_demo.ipynb
```

---

## Conclusion

This evaluation framework ensures:
- ✅ **Forecasting accuracy** is measured and monitored
- ✅ **Alert quality** is quantified (precision/recall)
- ✅ **Guardrails** prevent spam and errors
- ✅ **Limitations** are documented and understood
- ✅ **Improvements** are planned and prioritized

The system is **production-ready** with clear metrics and quality controls.
