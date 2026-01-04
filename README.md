# Agentic Market Data Forecaster & Alert Management System

Autonomous decisioning for market signals: forecast short-term moves, reason across multi-signal context, and choose when to alert, monitor, or stay silent. The focus is not just prediction but deciding whether a movement is actionable.

## 🆕 RAG Integration

This system now includes **Retrieval-Augmented Generation (RAG)** to enhance LLM explanations with:
- Historical pattern matching
- Past alert outcomes
- Domain knowledge retrieval
- Contextual market insights

### RAG Documentation
- 📖 **[RAG Index](RAG_INDEX.md)** - Start here for complete navigation
- 🚀 **[Quick Start](RAG_QUICKSTART.md)** - 5-minute setup guide
- 📋 **[Commands](RAG_COMMANDS.md)** - Command reference
- 🎯 **[Overview](RAG_README.md)** - Complete overview
- 🏗️ **[Architecture](RAG_ARCHITECTURE.md)** - Visual diagrams
- 📚 **[Full Guide](RAG_INTEGRATION.md)** - Technical documentation

### Quick Demo
```bash
python demo_rag.py
# or on Windows
launch_rag_demo.bat
```

See [RAG_INTEGRATION.md](RAG_INTEGRATION.md) for detailed documentation.

## Problem

- Markets emit noisy, high-frequency signals (price, volume, sentiment, macro) that drown analysts in alerts.
- Rule-based systems fire too often and ignore context; prediction-only tools give numbers without guidance.
- The missing piece: a reasoning loop that asks, "Is this move important enough to act on?"

## Solution

An agentic pipeline that:
- Forecasts next-day prices via time-series models (ARIMA/Prophet) with confidence.
- Observes live daily data (Alpha Vantage) plus historical OHLCV, indicators, macro, and sentiment.
- **Uses RAG to retrieve relevant historical patterns and domain knowledge.**
- Reasons across signals using an AI agent (LangChain + LLM) to decide: NO ALERT, MONITOR, or ALERT.
- Explains every decision in natural language with historical context, suppresses repetitive/low-confidence alerts, and learns from past actions.

## Architecture

Historical + Live Data → Forecasting Model → RAG Context Retrieval → Agentic Decision Engine → Alert/Monitor/No Alert → LLM + RAG Explanation → Memory for future decisions.

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
- **RAG: ChromaDB (vector store), OpenAI Embeddings, semantic search**
- Data API: Alpha Vantage (daily)
- Backend: FastAPI + Flask + Swagger UI
- Storage/Memory: CSV/JSON logs, vector database

## Repository Layout

```
53_shaik_shaafiya/
├── scripts/
│   ├── rag_system.py          ← RAG implementation
│   ├── llm_explainer.py       ← LLM with RAG
│   ├── agent_logic.py         ← Decision logic
│   ├── forecaster.py          ← Time-series models
│   ├── main_agent.py          ← Main orchestrator
│   ├── alert_system.py        ← Alert output
│   └── test_rag_system.py     ← RAG tests
├── data/
│   ├── stock_market_dataset.csv
│   └── sample_stock_data.csv
├── notebooks/
│   └── market_agent_demo.ipynb
├── knowledge_base/            ← RAG knowledge
│   ├── price_patterns.md
│   ├── volatility_insights.md
│   └── technical_indicators.md
├── outputs/
│   ├── alerts.json           ← Alert history for RAG
│   └── alerts.csv
├── templates/
│   └── *.html                ← Dashboard templates
├── agentic_system.py         ← Agentic dashboard
├── realtime_dashboard.py     ← Real-time viewer
├── demo_rag.py               ← RAG demonstration
├── requirements.txt
├── README.md
├── RAG_INTEGRATION.md        ← RAG full docs
├── RAG_QUICKSTART.md         ← RAG quick guide
├── RAG_ARCHITECTURE.md       ← RAG diagrams
└── RAG_SUMMARY.md            ← What was built
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

3) Initialize RAG knowledge base (first time only)
```bash
python scripts/rag_system.py
```

4) Run RAG demo
```bash
python demo_rag.py
```

5) Run main pipeline
```bash
python run_pipeline.py
```

6) Launch dashboards
```bash
# Agentic dashboard
python agentic_system.py

# Real-time dashboard
python realtime_dashboard.py
```

7) API docs (if using FastAPI)
```bash
uvicorn app:app --reload
# then open Swagger UI at http://localhost:8000/docs
```

## Decision Logic (simplified)

- Consider predicted move, % change vs prior close, volume anomaly, RSI/MACD regime, sentiment polarity, and confidence band.
- **Retrieve similar historical patterns via RAG for context.**
- If low confidence or recent duplicate alert → suppress.
- If moderate signals → MONITOR; strong confluence → ALERT.
- **Generate explanation enhanced with historical precedents from RAG.**
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
