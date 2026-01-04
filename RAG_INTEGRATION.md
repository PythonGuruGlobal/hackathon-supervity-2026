# RAG Integration in Stock Market Alert System

## Overview

This project now includes **Retrieval-Augmented Generation (RAG)** to enhance the LLM-powered explanations with relevant historical context, similar market patterns, and domain knowledge.

## What is RAG?

RAG combines:
1. **Retrieval**: Finding relevant information from a knowledge base
2. **Augmentation**: Adding that information to the LLM prompt
3. **Generation**: Using LLM to create contextually-aware responses

### Benefits for Market Analysis

- **Grounded in Facts**: Explanations reference actual historical patterns
- **Reduced Hallucinations**: LLM works with real data, not just training memory
- **Better Context**: Similar past situations inform current analysis
- **Improved Accuracy**: Historical precedents validate current predictions

## Architecture

```
┌─────────────────┐
│  Market Data    │
│  + Forecast     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Alert Agent    │──────┐
│  (Decision)     │      │
└────────┬────────┘      │
         │               │
         ▼               ▼
┌─────────────────┐  ┌──────────────────┐
│   RAG System    │  │  Current Metrics │
│                 │  └──────────────────┘
│ - Historical DB │
│ - Vector Store  │
│ - Knowledge Base│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Retrieved Context:             │
│  - Similar past patterns        │
│  - Relevant alerts              │
│  - Market insights              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│   LLM + RAG     │
│   Context       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enhanced       │
│  Explanation    │
└─────────────────┘
```

## Components

### 1. RAG System (`scripts/rag_system.py`)

#### MarketRAGSystem Class

Main RAG orchestrator that:
- Loads historical market data
- Manages alert history
- Performs similarity searches
- Retrieves relevant context

**Key Methods:**

```python
# Retrieve context for current situation
context = rag.retrieve_context(
    current_metrics={'percent_change': -4.5, 'volatility': 0.03},
    alert_type='price_drop',
    stock_symbol='AAPL'
)

# Returns: RetrievedContext with:
# - similar_patterns: Historical similar movements
# - past_alerts: Previous similar alerts
# - market_insights: Domain knowledge
# - relevance_score: Quality metric (0-1)
```

#### Retrieval Methods

1. **Pattern Similarity Search**
   - Compares current metrics to historical data
   - Uses Euclidean distance on normalized features
   - Returns top-K most similar historical days

2. **Alert History Retrieval**
   - Filters past alerts by type
   - Sorts by recency
   - Provides outcomes and explanations

3. **Knowledge Base Search**
   - Semantic search (if embeddings enabled)
   - Fallback keyword matching
   - Market domain knowledge

### 2. Enhanced LLM Explainer

Updated `scripts/llm_explainer.py` to integrate RAG:

```python
# Initialize with RAG
explainer = LLMExplainer(
    provider="openai",
    model="gpt-4o-mini",
    use_rag=True,  # Enable RAG
    stock_symbol="AAPL"
)

# Generate explanation (automatically uses RAG)
result = explainer.generate_explanation(decision)
```

**RAG Enhancement Process:**

1. Agent makes alert decision
2. RAG retrieves relevant context
3. Context added to LLM prompt
4. LLM generates explanation with historical grounding

### 3. Knowledge Base

Located in `knowledge_base/` directory:

- `price_patterns.md`: Price movement analysis
- `volatility_insights.md`: Volatility patterns
- `technical_indicators.md`: Indicator interpretation

**Creating Custom Knowledge:**

```python
from rag_system import create_default_knowledge_base

# Create/expand knowledge base
create_default_knowledge_base(output_dir="./knowledge_base")
```

## Usage

### Basic Usage

```python
from rag_system import MarketRAGSystem
from llm_explainer import LLMExplainer
from agent_logic import AlertAgent, AlertDecision

# 1. Initialize RAG system
rag = MarketRAGSystem(use_embeddings=False)  # True if OpenAI key available

# 2. Make alert decision
agent = AlertAgent()
decision = agent.evaluate(metrics)

# 3. Generate RAG-enhanced explanation
explainer = LLMExplainer(use_rag=True, stock_symbol="AAPL")
explanation = explainer.generate_explanation(decision)

print(explanation.explanation)
```

### Advanced: Direct RAG Queries

```python
# Retrieve context independently
context = rag.retrieve_context(
    current_metrics={
        'last_close': 150.0,
        'predicted_close': 144.0,
        'percent_change': -4.0,
        'volatility': 0.035,
        'trend': 'downward'
    },
    alert_type='price_drop',
    stock_symbol='AAPL',
    top_k=5
)

print(f"Relevance Score: {context.relevance_score:.2f}")
print(f"Found {len(context.similar_patterns)} similar patterns")
print(f"Found {len(context.past_alerts)} relevant alerts")

# Format for display
formatted = rag.format_context_for_llm(context)
print(formatted)
```

## Configuration

### Embedding Options

**Option 1: Without Embeddings (Default)**
```python
rag = MarketRAGSystem(use_embeddings=False)
```
- Uses simple similarity search
- No API key required
- Faster initialization

**Option 2: With OpenAI Embeddings**
```python
import os
os.environ['OPENAI_API_KEY'] = 'your-key-here'

rag = MarketRAGSystem(use_embeddings=True)
```
- Semantic search via vector embeddings
- Better semantic matching
- Requires OpenAI API key

**Option 3: Local Embeddings** (Future)
```python
# Using sentence-transformers (no API key)
rag = MarketRAGSystem(
    use_embeddings=True,
    embedding_model='local'
)
```

### Customization Parameters

```python
rag = MarketRAGSystem(
    data_path="custom_data.csv",           # Historical data
    alerts_path="custom_alerts.json",      # Alert history
    knowledge_base_path="custom_kb/",      # Knowledge files
    use_embeddings=True
)

# Adjust retrieval
context = rag.retrieve_context(
    current_metrics=metrics,
    alert_type='price_drop',
    stock_symbol='AAPL',
    top_k=10  # Number of similar items to retrieve
)
```

## Example Output

### Without RAG
```
The forecast indicates a sharp 4.5% drop following increased volatility 
over the last 3 days. This suggests possible market uncertainty or 
reaction to external events.
```

### With RAG
```
The forecast indicates a sharp 4.5% drop following increased volatility 
over the last 3 days. Historical analysis shows similar patterns on 
2024-03-15 (-4.2%) and 2024-01-22 (-4.8%), both followed by continued 
downward pressure. This movement aligns with typical behavior during 
high volatility periods (>3%), where market uncertainty amplifies 
price swings. Past alerts of this type had a 75% accuracy rate in 
predicting continued short-term weakness.
```

## Performance Metrics

### Relevance Scoring

RAG system calculates relevance (0-1) based on:
- **Pattern similarity** (40%): How close historical patterns match
- **Alert history** (30%): Number of relevant past alerts
- **Knowledge depth** (30%): Available insights

**Interpretation:**
- `< 0.3`: Low relevance, minimal context available
- `0.3-0.7`: Moderate relevance, some context
- `> 0.7`: High relevance, strong context

### Retrieval Statistics

```python
context = rag.retrieve_context(...)

print(f"Relevance: {context.relevance_score:.0%}")
print(f"Patterns: {len(context.similar_patterns)} found")
print(f"Alerts: {len(context.past_alerts)} retrieved")
print(f"Insights: {len(context.market_insights)} available")
```

## Data Requirements

### Historical Data Format

CSV with columns:
```
Date, Stock, Open, High, Low, Close, Volume, RSI, Sentiment_Score
```

### Alert History Format

JSON array:
```json
[
  {
    "timestamp": "2024-01-15T10:30:00",
    "alert_type": "price_drop",
    "stock_symbol": "AAPL",
    "reason": "4.5% predicted drop",
    "explanation": "...",
    "metrics": {...}
  }
]
```

## Deployment Considerations

### Production Checklist

- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Initialize knowledge base: `python -m rag_system`
- [ ] Verify historical data path
- [ ] Test RAG retrieval independently
- [ ] Monitor relevance scores
- [ ] Adjust `top_k` based on latency requirements

### Cost Optimization

1. **Embedding Costs**
   - Use local embeddings (sentence-transformers)
   - Cache embeddings in vector DB
   - Start with `use_embeddings=False`

2. **LLM Costs**
   - RAG reduces hallucinations → better results with cheaper models
   - Consider gpt-4o-mini with RAG vs. gpt-4 without

3. **Latency**
   - Vector search: ~50ms
   - LLM generation: ~1-2s
   - Total overhead: ~100-200ms with RAG

## Testing

### Unit Tests

```bash
cd scripts
python -m pytest test_rag_system.py -v
```

### Integration Test

```python
# Test full pipeline
from rag_system import MarketRAGSystem
from llm_explainer import LLMExplainer

rag = MarketRAGSystem()
explainer = LLMExplainer(use_rag=True)

# Verify RAG integration
assert explainer.rag_system is not None
assert explainer.use_rag == True
```

### Demo Script

```bash
cd scripts
python rag_system.py  # Runs built-in demo
```

## Troubleshooting

### RAG Not Loading

```
⚠️ RAG system initialization failed
```

**Solutions:**
1. Check file paths in constructor
2. Verify CSV format matches expected schema
3. Check permissions on data directories

### Low Relevance Scores

```
Relevance Score: 0.15
```

**Causes:**
- Limited historical data
- No similar patterns in database
- First run (empty alert history)

**Solutions:**
- Accumulate more historical data
- Expand knowledge base
- Lower relevance threshold for prompting

### Embeddings Not Working

```
⚠️ OPENAI_API_KEY not set. Disabling vector embeddings.
```

**Solutions:**
1. Set environment variable: `export OPENAI_API_KEY=sk-...`
2. Use local embeddings (not yet implemented)
3. Continue with similarity search (still effective)

## Future Enhancements

### Planned Features

1. **Local Embeddings**
   - sentence-transformers integration
   - No API key required
   - Offline operation

2. **Multi-Stock Correlation**
   - Retrieve patterns across related stocks
   - Sector-wide trend analysis

3. **Time-Series DTW**
   - Dynamic Time Warping for pattern matching
   - Better capture of shape similarity

4. **News Integration**
   - Scrape relevant financial news
   - Add to context retrieval
   - Link alerts to events

5. **Outcome Tracking**
   - Track alert accuracy
   - Learn from past predictions
   - Improve future retrieval

## References

- **RAG Paper**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
- **LangChain RAG**: https://python.langchain.com/docs/use_cases/question_answering/
- **ChromaDB**: https://docs.trychroma.com/

## Support

For issues or questions about RAG integration:
1. Check this documentation
2. Review `scripts/rag_system.py` comments
3. Run demo: `python scripts/rag_system.py`
4. Test with sample data in `data/` directory

---

**Last Updated**: January 2026  
**Version**: 1.0.0  
**Status**: Production-Ready ✅
