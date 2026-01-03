# Agentic Market Data Forecaster & Alert Management System

Autonomous decisioning for market signals: forecast short-term moves, reason across multi-signal context, and choose when to alert, monitor, or stay silent. The focus is not just prediction but deciding whether a movement is actionable.

## Problem

- Markets emit noisy, high-frequency signals (price, volume, sentiment, macro) that drown analysts in alerts.
- Rule-based systems fire too often and ignore context; prediction-only tools give numbers without guidance.
- The missing piece: a reasoning loop that asks, "Is this move important enough to act on?"

## Solution

An agentic pipeline that:
- Forecasts next-day prices via time-series models (ARIMA/Prophet) with confidence.
- Observes live daily data (Alpha Vantage) plus historical OHLCV, indicators, macro, and sentiment.
- Reasons across signals using an AI agent (LangChain + LLM) to decide: NO ALERT, MONITOR, or ALERT.
- Explains every decision in natural language, suppresses repetitive/low-confidence alerts, and learns from past actions.

## Architecture

Historical + Live Data → Forecasting Model → Agentic Decision Engine → Alert/Monitor/No Alert → Explanation → Memory for future decisions.

## Methodology

1) **Data**: ~50k historical rows with OHLCV, RSI/MACD/SMA/Bollinger, macro (GDP, inflation, rates), sentiment scores; daily live updates via Alpha Vantage.
2) **Forecasting**: ARIMA or Prophet predicts next-day close, emits predicted price and confidence.
3) **Agentic Decision Loop** (Observe → Plan → Reason → Decide → Act → Reflect → Update Memory) weighing price % change, volume spikes, indicators, sentiment, forecast confidence, and past alerts.
4) **Decisions**: NO ALERT, MONITOR (low severity), ALERT (high severity) with human-readable rationale.
5) **Reflection & Memory**: suppress repetitive alerts, adapt thresholds, log outcomes for feedback.

## Example Output

```json
{
	"date": "2026-01-02",
	"stock": "AAPL",
	"decision": "MONITOR",
	"severity": "LOW",
	"reason": "Price declined with moderate confidence and similar alerts were triggered recently.",
	"confidence": 0.71
}
```

## Technologies

- Python (Pandas, NumPy)
- Time-series: statsmodels ARIMA / Prophet
- Agent framework: LangChain + LLM (OpenAI/Claude/Gemini)
- Data API: Alpha Vantage (daily)
- Backend: FastAPI + Swagger UI (minimal UI optional)
- Storage/Memory: CSV/JSON logs

## Repository Layout

```
agentic-market-alert/
├── data/
├── notebooks/
├── ml/
├── agent/
├── llm/
├── evaluation/
├── outputs/
├── README.md
├── requirements.txt
└── run_pipeline.py
```

## Setup

1) Install deps
```bash
pip install -r requirements.txt
```

2) Env vars
```
ALPHAVANTAGE_API_KEY=your_key
OPENAI_API_KEY=your_llm_key
```

3) Run pipeline
```bash
python run_pipeline.py
```

4) API docs
```bash
uvicorn app:app --reload
# then open Swagger UI at http://localhost:8000/docs
```

## Decision Logic (simplified)

- Consider predicted move, % change vs prior close, volume anomaly, RSI/MACD regime, sentiment polarity, and confidence band.
- If low confidence or recent duplicate alert → suppress.
- If moderate signals → MONITOR; strong confluence → ALERT.
- Log rationale + signals for traceability.

## Evaluation & Guardrails

- Forecast: MAE/RMSE.
- Alert quality: precision/recall, false-positive reduction, alert frequency caps.
- Confidence-based suppression; no trading or investment advice.
- Reflection loop to de-duplicate and adjust context weights.

## Demo

A 10-minute narrated walkthrough is expected (screen recording with voice). Include the YouTube link here when ready.

## Notes

- This system is decision-focused, not an auto-trader.
- Memory of past alerts reduces noise over time without retraining.
