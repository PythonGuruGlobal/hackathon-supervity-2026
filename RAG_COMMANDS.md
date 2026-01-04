# RAG System - Command Reference Card

## Quick Commands

### Setup & Installation
```bash
# Install all dependencies including RAG
pip install -r requirements.txt

# Create knowledge base (first time only)
python scripts/rag_system.py

# Verify installation
python -c "from scripts.rag_system import MarketRAGSystem; print('✅ RAG Ready')"
```

### Running Demos
```bash
# RAG demonstration (5 demos)
python demo_rag.py

# Windows quick launch
launch_rag_demo.bat

# Agentic dashboard (with RAG)
python agentic_system.py

# Real-time dashboard
python realtime_dashboard.py
```

### Testing
```bash
# Run all RAG tests
cd scripts
python test_rag_system.py

# Run specific test
python test_rag_system.py TestRAGSystem.test_retrieve_context

# Verbose mode
python test_rag_system.py -v
```

### Python Usage Patterns

#### Pattern 1: Standalone RAG
```python
from scripts.rag_system import MarketRAGSystem

rag = MarketRAGSystem(use_embeddings=False)
context = rag.retrieve_context(
    current_metrics={'percent_change': -4.0, 'volatility': 0.03},
    alert_type='price_drop',
    stock_symbol='AAPL'
)
print(f"Relevance: {context.relevance_score:.0%}")
```

#### Pattern 2: RAG + LLM
```python
from scripts.llm_explainer import LLMExplainer
from scripts.agent_logic import AlertAgent

agent = AlertAgent()
explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')

decision = agent.evaluate(metrics)
result = explainer.generate_explanation(decision)
print(result.explanation)
```

#### Pattern 3: Full Pipeline
```python
from scripts.forecaster import MarketForecaster, load_market_data
from scripts.agent_logic import AlertAgent
from scripts.llm_explainer import LLMExplainer

# Load & forecast
data = load_market_data('data/stock_market_dataset.csv')
forecaster = MarketForecaster()
forecaster.fit(data, target_col='Close')
forecast = forecaster.forecast(steps=1)
metrics = forecaster.calculate_metrics(data, forecast)

# Decide with agent
agent = AlertAgent()
decision = agent.evaluate(metrics)

# Explain with RAG
explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
result = explainer.generate_explanation(decision)

print(f"Alert: {decision.should_alert}")
print(f"Type: {decision.alert_type.value}")
print(f"Explanation: {result.explanation}")
```

### Configuration

#### Without Embeddings (Fast, No API Key)
```python
from scripts.rag_system import MarketRAGSystem

rag = MarketRAGSystem(use_embeddings=False)
```

#### With OpenAI Embeddings
```python
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'

from scripts.rag_system import MarketRAGSystem
rag = MarketRAGSystem(use_embeddings=True)
```

#### Custom Paths
```python
rag = MarketRAGSystem(
    data_path="my_data.csv",
    alerts_path="my_alerts.json",
    knowledge_base_path="my_kb/",
    use_embeddings=False
)
```

### Knowledge Base Management

#### Create Default KB
```python
from scripts.rag_system import create_default_knowledge_base

create_default_knowledge_base(output_dir="./knowledge_base")
```

#### Add Custom Knowledge
```bash
# Create new markdown file
echo "# My Pattern" > knowledge_base/my_pattern.md
echo "Description..." >> knowledge_base/my_pattern.md

# RAG will auto-index on next initialization
```

### Debugging & Inspection

#### Check RAG Status
```python
from scripts.rag_system import MarketRAGSystem

rag = MarketRAGSystem()
print(f"Historical records: {len(rag.historical_data)}")
print(f"Alert history: {len(rag.alert_history)}")
print(f"Embeddings: {'Enabled' if rag.use_embeddings else 'Disabled'}")
```

#### Inspect Retrieved Context
```python
context = rag.retrieve_context(metrics, 'price_drop', 'AAPL')

print(f"Relevance: {context.relevance_score:.0%}")
print(f"Patterns: {len(context.similar_patterns)}")
print(f"Alerts: {len(context.past_alerts)}")
print(f"Insights: {len(context.market_insights)}")

# View formatted
print("\n" + rag.format_context_for_llm(context))
```

#### Test LLM Integration
```python
from scripts.llm_explainer import LLMExplainer

explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
print(f"RAG enabled: {explainer.use_rag}")
print(f"Has RAG system: {explainer.rag_system is not None}")
```

### Common Tasks

#### Task: Update Historical Data
```bash
# Add new data to CSV
# RAG automatically picks it up on next initialization
python -c "from scripts.rag_system import MarketRAGSystem; rag = MarketRAGSystem(); print('Data reloaded')"
```

#### Task: Clear Alert History
```bash
# Backup first
cp outputs/alerts.json outputs/alerts.json.bak

# Clear
echo "[]" > outputs/alerts.json
```

#### Task: Rebuild Vector Store
```bash
# Delete existing
rm -rf knowledge_base/chroma_db

# Reinitialize
python -c "from scripts.rag_system import MarketRAGSystem; MarketRAGSystem(use_embeddings=True)"
```

#### Task: Export Context for Analysis
```python
import json
from scripts.rag_system import MarketRAGSystem

rag = MarketRAGSystem()
context = rag.retrieve_context(metrics, 'price_drop', 'AAPL')

# Export to JSON
with open('context_export.json', 'w') as f:
    json.dump({
        'relevance': context.relevance_score,
        'patterns': context.similar_patterns,
        'alerts': context.past_alerts,
        'insights': context.market_insights
    }, f, indent=2)
```

### Environment Variables

```bash
# Required for OpenAI LLM
export OPENAI_API_KEY="sk-..."

# Required for Alpha Vantage API
export ALPHAVANTAGE_API_KEY="BEWGGWDHQV07D4GG"

# Verify
python -c "import os; print('OpenAI:', bool(os.getenv('OPENAI_API_KEY'))); print('AlphaVantage:', bool(os.getenv('ALPHAVANTAGE_API_KEY')))"
```

### Performance Tuning

#### Reduce Retrieval Count
```python
# Default: top_k=5
context = rag.retrieve_context(metrics, 'price_drop', 'AAPL', top_k=3)
```

#### Limit Historical Data
```python
# Only load recent data
import pandas as pd
df = pd.read_csv('data/stock_market_dataset.csv')
df_recent = df.tail(1000)  # Last 1000 rows
df_recent.to_csv('data/recent_data.csv', index=False)

# Use in RAG
rag = MarketRAGSystem(data_path='data/recent_data.csv')
```

#### Cache RAG System
```python
# Initialize once, reuse many times
rag = MarketRAGSystem()
explainer = LLMExplainer(use_rag=True)

for decision in decisions:
    result = explainer.generate_explanation(decision)
    # RAG system reused, not reinitialized
```

### Troubleshooting Commands

#### Check Dependencies
```bash
pip list | grep -E "langchain|chromadb|openai"
```

#### Validate Data Files
```bash
# Check CSV exists and has data
python -c "import pandas as pd; df=pd.read_csv('stock_market_dataset.csv'); print(f'{len(df)} rows loaded')"

# Check alerts JSON
python -c "import json; alerts=json.load(open('outputs/alerts.json')); print(f'{len(alerts)} alerts')"
```

#### Test Imports
```python
# Test all RAG imports
try:
    from scripts.rag_system import MarketRAGSystem
    from scripts.llm_explainer import LLMExplainer
    from scripts.agent_logic import AlertAgent
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

### Quick Diagnostics

```bash
# Run full diagnostic
python -c "
from scripts.rag_system import MarketRAGSystem, create_default_knowledge_base
import os

print('=== RAG System Diagnostics ===')
print(f'OpenAI Key: {\"Set\" if os.getenv(\"OPENAI_API_KEY\") else \"Not Set\"}')

try:
    create_default_knowledge_base()
    print('✅ Knowledge base created')
except Exception as e:
    print(f'⚠️  KB creation: {e}')

try:
    rag = MarketRAGSystem(use_embeddings=False)
    print(f'✅ RAG initialized: {len(rag.historical_data)} records')
except Exception as e:
    print(f'❌ RAG init failed: {e}')
"
```

## Documentation Quick Links

- [Full Integration Guide](RAG_INTEGRATION.md)
- [Quick Start](RAG_QUICKSTART.md)
- [Architecture Diagrams](RAG_ARCHITECTURE.md)
- [Implementation Summary](RAG_SUMMARY.md)
- [Main README](README.md)

## Getting Help

1. Check documentation above
2. Run demo: `python demo_rag.py`
3. Run tests: `python scripts/test_rag_system.py`
4. Inspect code: `scripts/rag_system.py`

---

**Pro Tip**: Bookmark this file for quick reference during development!
