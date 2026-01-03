# Hackathon Supervity 2026

## Market Data Forecaster & Alert Agent (Agentic AI Project)

### Problem Statement

**Real-world pain**: In finance and fintech companies, market data flows continuously but humans cannot monitor everything. Most price movements are noise, yet missing critical signals causes losses, late decisions, and poor risk management.

**Example**: "The stock dropped 6% yesterday — why didn't anyone flag this earlier?"

This project solves this by building an **AI agent that watches market data, forecasts movement, decides when something unusual is happening, and alerts with clear explanations**.

### What This Project Is

This is **not a trading bot** and **not just a prediction model**.

It is an **agentic AI system** that:
- ✅ Forecasts market movement using time-series models
- ✅ Makes intelligent decisions using rule-based logic
- ✅ Generates human-readable explanations using LLMs
- ✅ Self-checks to avoid alert spam
- ✅ Outputs actionable insights in production-ready format

**In one line**: "An AI agent that forecasts market movement, decides if something unusual or important is happening, and alerts with a clear explanation."

### System Architecture

```
Market Data → Forecast Model → Agent Decision Logic → LLM Explanation → Alert Output
```

**Step-by-step flow**:

1. **Data Input**: Historical stock data (Date, Open, High, Low, Close, Volume)
2. **Forecasting**: ARIMA/Prophet predicts next-day price and trend
3. **Decision Rules**: Agent evaluates if predicted changes meet alert thresholds
4. **AI Explanation**: LLM generates context-aware reasoning for alerts
5. **Self-Check**: Prevents repetitive/low-confidence alerts
6. **Output**: Structured CSV/JSON + human-readable explanations

### Dataset

**Sample Market Data**: Historical stock prices with OHLCV format
- Date, Open, High, Low, Close, Volume
- Source: Yahoo Finance API or similar (sample data provided in `/data`)

### Why This is Agentic AI

This project exhibits all agent characteristics:

| Agent Trait | Implementation |
|-------------|----------------|
| **Tool Usage** | Uses forecasting models as tools |
| **Decision-Making** | Rule-based logic determines alert triggers |
| **Conditional Actions** | Acts only when thresholds are met |
| **Self-Checking** | Validates alerts before sending |
| **Explanation** | LLM generates reasoning for decisions |

The LLM is **not the boss** — it's the assistant. The agent orchestrates everything.

### Key Features

✅ **Time-series forecasting** (ARIMA/Prophet)  
✅ **Multi-condition alert logic** (drop %, volatility spike, trend reversal)  
✅ **LLM-powered explanations** (OpenAI/Gemini/Claude)  
✅ **Alert deduplication** (prevents spam)  
✅ **Production-ready output** (CSV/JSON format)  
✅ **No UI required** (batch processing simulation)

### Tech Stack

- **Python 3.10+** - Core language
- **Pandas** - Data manipulation
- **Statsmodels/Prophet** - Time-series forecasting
- **NumPy** - Mathematical operations
- **LangChain** - LLM orchestration
- **OpenAI/Gemini API** - Explanation generation
- **Pydantic** - Data validation
- **Jupyter** - Interactive exploration

### Project Structure

```
.
├── README.md              # This file
├── GUIDELINES.md          # Hackathon rules
├── requirements.txt       # Python dependencies
├── data/
│   └── sample_stock_data.csv  # Historical market data
├── scripts/
│   ├── forecaster.py      # ARIMA/Prophet forecasting
│   ├── agent_logic.py     # Decision rules & self-check
│   ├── llm_explainer.py   # LLM explanation generation
│   ├── alert_system.py    # Alert output manager
│   └── main_agent.py      # Main orchestrator
├── notebooks/
│   └── market_agent_demo.ipynb  # Interactive demo
└── outputs/
    ├── alerts.csv         # Alert records
    └── alerts.json        # Structured output
```

### How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key** (for LLM explanations):
   ```bash
   set OPENAI_API_KEY=your-key-here
   # or use .env file
   ```

3. **Run the agent**:
   ```bash
   python scripts/main_agent.py --data data/sample_stock_data.csv --output outputs/
   ```

4. **Explore in notebook**:
   ```bash
   jupyter notebook notebooks/market_agent_demo.ipynb
   ```

### Sample Output

**Console**:
```
[2024-01-10] Analyzing stock data...
[2024-01-10] Forecast: Price drop from 155 → 148 (-4.5%)
[2024-01-10] ⚠️ ALERT TRIGGERED: High volatility + predicted drop
[2024-01-10] Confidence: Medium
```

**alerts.json**:
```json
{
  "date": "2024-01-10",
  "stock": "AAPL",
  "alert": true,
  "predicted_close": 148,
  "actual_close": 155,
  "drop_percent": 4.5,
  "confidence": "medium",
  "reason": "High volatility + predicted drop",
  "explanation": "The forecast indicates a sharp 4.5% drop following increased volatility over the last 3 days. This suggests possible market uncertainty or reaction to external events."
}
```

### Evaluation & Guardrails

**Metrics**:
- Forecast accuracy (RMSE, MAE)
- Alert precision/recall
- False positive rate
- Explanation quality (human eval)

**Guardrails**:
- Threshold validation (prevents oversensitive alerts)
- Confidence scoring (suppresses low-confidence predictions)
- Deduplication logic (avoids alert spam)
- Rate limiting (max alerts per day)

### Limitations & Assumptions

- Uses historical data only (not real-time streaming)
- Simplified alert rules (production would use ML-based anomaly detection)
- Single-stock analysis (can be extended to portfolios)
- LLM explanations are post-hoc (not causal analysis)

### Innovation Highlights

🚀 **Agentic Architecture**: Not just prediction—decision-making + reasoning  
🚀 **Self-Awareness**: Agent checks its own outputs before alerting  
🚀 **Hybrid AI**: Combines statistical forecasting + LLM reasoning  
🚀 **Production-Ready**: Designed for real ops teams, not demos

### Future Enhancements

- Real-time streaming data integration
- Multi-asset portfolio monitoring
- ML-based anomaly detection
- Sentiment analysis from news/social media
- Adaptive threshold learning

---

**Author**: Shaik Shaafiya  
**Hackathon**: Supervity 2026  
**Domain**: Finance + Agentic AI
