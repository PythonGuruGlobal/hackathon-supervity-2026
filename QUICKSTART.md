# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```powershell
# Navigate to project directory
cd 53_shaik_shaafiya

# Install Python packages
pip install -r requirements.txt
```

### 2. Set Up API Key (Optional)

For LLM-powered explanations, set your OpenAI API key:

```powershell
# Option 1: Environment variable
$env:OPENAI_API_KEY="your-key-here"

# Option 2: Create .env file
Copy-Item .env.template .env
# Then edit .env with your key
```

**Note:** The system works without an API key using template-based explanations.

### 3. Run the Agent

```powershell
# Basic run
python scripts/main_agent.py --data data/sample_stock_data.csv

# With specific rules
python scripts/main_agent.py --data data/sample_stock_data.csv --rules aggressive

# Batch mode (analyze multiple windows)
python scripts/main_agent.py --data data/sample_stock_data.csv --batch --window 30
```

### 4. View Results

Check the `outputs/` directory:
- `alerts.csv` - Structured alert records
- `alerts.json` - JSON format (one per line)

### 5. Explore in Jupyter

```powershell
# Launch Jupyter
jupyter notebook notebooks/market_agent_demo.ipynb
```

---

## 📊 Expected Output

### Console Output
```
🔧 Initializing Market Alert Agent...
  ✓ Forecaster initialized
  ✓ Decision agent initialized (moderate rules)
  ✓ LLM explainer initialized (openai/gpt-4o-mini)
  ✓ Alert system initialized

🚀 Starting Agent Workflow...

📊 Step 1: Loading market data...
  ✓ Loaded 64 days of data
  ✓ Date range: 2024-01-01 to 2024-03-29

🔮 Step 2: Fitting forecast model...
  ✓ Model fitted successfully

📈 Step 3: Generating forecast...
  ✓ Forecast complete:
    Last Close: $157.50
    Predicted: $159.20
    Change: +1.08%
    Volatility: 0.0158
    Trend: upward

🤖 Step 4: Agent decision-making...
  ✅ No alert - conditions normal

💬 Step 5: Generating LLM explanation...
  ✓ Explanation generated

📝 Step 6: Logging alert...
  ✓ Alert logged successfully

✨ Agent workflow completed successfully!
```

### Alert Output (when triggered)
```
======================================================================
[2024-03-29 10:30:15] MARKET ALERT
======================================================================
⚠️  ALERT TRIGGERED
   Type: price_drop
   Confidence: MEDIUM

📊 Market Data:
   Last Close: $155.00
   Predicted: $148.00
   Change: -4.52%
   Volatility: 0.0250
   Trend: downward

📝 Explanation:
   The forecast indicates a sharp 4.5% drop following increased 
   volatility over the last 3 days. This suggests possible market 
   uncertainty or reaction to external events.

======================================================================
```

---

## 🎯 What to Check

1. **Forecast Accuracy**: Compare predicted vs actual prices
2. **Alert Frequency**: Should be 10-20% of days (moderate rules)
3. **Explanation Quality**: Should be clear and professional
4. **No Spam**: Similar alerts should be suppressed within 24h

---

## 🛠️ Troubleshooting

### Issue: "Module not found"
```powershell
# Make sure you're in the right directory
cd 53_shaik_shaafiya

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "OPENAI_API_KEY not set"
```powershell
# Set environment variable
$env:OPENAI_API_KEY="sk-..."

# Or use .env file
Copy-Item .env.template .env
# Edit .env with your key
```

### Issue: "Forecast model not converging"
- Try more data (at least 30 days)
- Check for missing values in CSV
- Consider using Prophet instead of ARIMA

### Issue: "Too many/few alerts"
```powershell
# Adjust rules preset
python scripts/main_agent.py --data data/sample_stock_data.csv --rules conservative  # Fewer alerts
python scripts/main_agent.py --data data/sample_stock_data.csv --rules aggressive   # More alerts
```

---

## 📝 Next Steps

1. **Use Your Own Data**: Replace `data/sample_stock_data.csv` with real market data
2. **Tune Parameters**: Adjust thresholds in `scripts/agent_logic.py`
3. **Add More Features**: Extend with sentiment analysis, news feeds, etc.
4. **Deploy**: Set up scheduled runs (cron job or Windows Task Scheduler)

---

## 🎓 Understanding the System

### Architecture
```
Market Data → Forecaster → Agent → LLM → Alert System
                ↓           ↓       ↓         ↓
            ARIMA/Prophet  Rules  Explain   CSV/JSON
```

### Key Components

1. **Forecaster** (`forecaster.py`)
   - ARIMA time-series model
   - Predicts next-day closing price
   - Calculates volatility and trends

2. **Agent** (`agent_logic.py`)
   - Evaluates forecast against rules
   - Makes alert decisions
   - Self-checks to prevent spam

3. **LLM Explainer** (`llm_explainer.py`)
   - Generates human-readable explanations
   - Uses OpenAI or fallback templates
   - Provides context for decisions

4. **Alert System** (`alert_system.py`)
   - Logs alerts to CSV/JSON
   - Provides console output
   - Tracks alert history

5. **Main Orchestrator** (`main_agent.py`)
   - Coordinates all components
   - Handles CLI arguments
   - Runs full workflow

---

## 🔍 Example Use Cases

### Daily Monitoring
```powershell
# Run daily at market close
python scripts/main_agent.py --data daily_market_data.csv --stock AAPL
```

### Portfolio Analysis
```powershell
# Analyze multiple stocks
foreach ($stock in @("AAPL", "GOOGL", "MSFT")) {
    python scripts/main_agent.py --data "data/${stock}.csv" --stock $stock
}
```

### Backtesting
```powershell
# Analyze historical performance
python scripts/main_agent.py --data historical_2023.csv --batch --window 30
```

---

## 💡 Tips

- **Start Conservative**: Use moderate or conservative rules initially
- **Monitor False Positives**: If too many alerts, increase thresholds
- **Use Batch Mode**: Test on historical data before production
- **Check Volatility**: High volatility = less reliable forecasts
- **Tune for Your Data**: Each market/stock has different characteristics

---

## 📚 Further Reading

- [README.md](README.md) - Full project documentation
- [EVALUATION.md](EVALUATION.md) - Metrics and testing
- [GUIDELINES.md](GUIDELINES.md) - Hackathon rules
- Notebooks: Interactive exploration and visualization

---

**Questions?** Check the code comments or run with `--help`:
```powershell
python scripts/main_agent.py --help
```
