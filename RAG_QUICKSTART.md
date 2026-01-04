# RAG Quick Reference Guide

## What You Need to Know

### What is RAG?
**Retrieval-Augmented Generation** = Retrieve relevant facts + Augment LLM prompt + Generate informed response

### Why RAG for Stock Alerts?
- ✅ Grounds explanations in historical data
- ✅ Reduces AI hallucinations
- ✅ Provides factual precedents
- ✅ Improves explanation quality

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize System
```python
from scripts.rag_system import MarketRAGSystem, create_default_knowledge_base

# First time: create knowledge base
create_default_knowledge_base()

# Initialize RAG
rag = MarketRAGSystem(use_embeddings=False)
```

### 3. Use with LLM Explainer
```python
from scripts.llm_explainer import LLMExplainer

# Enable RAG
explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')

# Generate explanation (RAG auto-applied)
result = explainer.generate_explanation(decision)
```

## Key Features

### Feature 1: Historical Pattern Matching
Finds similar past market conditions:
```python
context = rag.retrieve_context(
    current_metrics={'percent_change': -4.0, 'volatility': 0.03},
    alert_type='price_drop',
    stock_symbol='AAPL'
)

# Returns similar days with comparable movements
print(context.similar_patterns)
```

### Feature 2: Past Alert Retrieval
References previous alerts:
```python
# Automatically retrieves alerts of same type
# Shows how past situations played out
print(context.past_alerts)
```

### Feature 3: Domain Knowledge
Accesses market expertise:
```python
# Semantic search through knowledge base
# Returns relevant market insights
print(context.market_insights)
```

## Configuration Options

### Without Embeddings (Fast, No API Key)
```python
rag = MarketRAGSystem(use_embeddings=False)
```
- Uses similarity search
- No API costs
- Good for most use cases

### With Embeddings (Better Semantic Search)
```python
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'

rag = MarketRAGSystem(use_embeddings=True)
```
- Vector-based search
- Better semantic matching
- Requires OpenAI API key

## Customization

### Custom Data Sources
```python
rag = MarketRAGSystem(
    data_path="my_data.csv",
    alerts_path="my_alerts.json",
    knowledge_base_path="my_kb/"
)
```

### Adjust Retrieval Count
```python
context = rag.retrieve_context(
    current_metrics=metrics,
    alert_type='price_drop',
    stock_symbol='AAPL',
    top_k=10  # Retrieve more items
)
```

### Expand Knowledge Base
Add markdown files to `knowledge_base/`:
```markdown
# My Custom Knowledge

## Pattern X
Description of pattern...

## Indicator Y
How to interpret...
```

## Understanding Outputs

### Relevance Score
- **0.0 - 0.3**: Low (limited context)
- **0.3 - 0.7**: Moderate (decent context)
- **0.7 - 1.0**: High (strong context)

### Similar Patterns
```python
{
    'date': '2024-03-15',
    'close': 150.25,
    'change': -4.2,
    'volatility': 0.032,
    'similarity_score': 0.8  # Lower is more similar
}
```

### Past Alerts
```python
{
    'timestamp': '2024-03-15T10:30:00',
    'alert_type': 'price_drop',
    'reason': '4.2% predicted drop',
    'explanation': '...'
}
```

## Common Patterns

### Pattern 1: Basic Usage
```python
# Initialize once
rag = MarketRAGSystem()
explainer = LLMExplainer(use_rag=True)

# Use many times
for decision in decisions:
    explanation = explainer.generate_explanation(decision)
    print(explanation.explanation)
```

### Pattern 2: Inspect Retrieved Context
```python
explainer = LLMExplainer(use_rag=True)

# Manually retrieve context to inspect
rag = explainer.rag_system
context = rag.retrieve_context(metrics, 'price_drop', 'AAPL')

print(f"Relevance: {context.relevance_score:.0%}")
print(f"Patterns: {len(context.similar_patterns)}")
print(f"Insights: {len(context.market_insights)}")
```

### Pattern 3: Formatted Context
```python
# Get human-readable context
formatted = rag.format_context_for_llm(context)
print(formatted)

# Output:
# **Similar Historical Patterns:**
# 1. 2024-03-15: -4.2% change (volatility: 0.032)
# 2. 2024-01-22: -4.8% change (volatility: 0.028)
# ...
```

## Troubleshooting

### Issue: "RAG system initialization failed"
**Solution**: Check file paths, ensure CSV format is correct

### Issue: Low relevance scores
**Solution**: 
- Accumulate more historical data
- Expand knowledge base
- Normal for first few runs

### Issue: "OPENAI_API_KEY not set"
**Solution**: Either:
- Set environment variable: `export OPENAI_API_KEY=sk-...`
- Use without embeddings: `use_embeddings=False`

### Issue: Slow retrieval
**Solution**:
- Reduce `top_k` parameter
- Use `use_embeddings=False`
- Limit historical data size

## Testing

### Run Tests
```bash
cd scripts
python test_rag_system.py
```

### Run Demo
```bash
python demo_rag.py
# or
launch_rag_demo.bat  # Windows
```

## Integration Checklist

- [ ] Install RAG dependencies (`chromadb`, `langchain-openai`)
- [ ] Create knowledge base (`create_default_knowledge_base()`)
- [ ] Initialize RAG system (`MarketRAGSystem()`)
- [ ] Enable in LLM explainer (`use_rag=True`)
- [ ] Test retrieval (`retrieve_context()`)
- [ ] Verify explanations improved
- [ ] Monitor relevance scores
- [ ] Expand knowledge base as needed

## Best Practices

1. **Start Simple**: Use `use_embeddings=False` initially
2. **Accumulate Data**: More historical data → better retrieval
3. **Expand Knowledge**: Add domain-specific insights to KB
4. **Monitor Quality**: Track relevance scores over time
5. **Iterate**: Refine based on explanation quality

## Performance Tips

- Cache RAG system (initialize once, reuse)
- Batch process alerts when possible
- Use embeddings only if needed
- Prune old/irrelevant alerts periodically

## Next Steps

1. Run demo: `python demo_rag.py`
2. Read full docs: `RAG_INTEGRATION.md`
3. Inspect code: `scripts/rag_system.py`
4. Customize knowledge base
5. Integrate into your workflow

## Resources

- Full Documentation: [RAG_INTEGRATION.md](RAG_INTEGRATION.md)
- RAG System Code: [scripts/rag_system.py](scripts/rag_system.py)
- LLM Integration: [scripts/llm_explainer.py](scripts/llm_explainer.py)
- Tests: [scripts/test_rag_system.py](scripts/test_rag_system.py)

---

**Quick Help**: For issues, check troubleshooting section or run `python demo_rag.py` to verify setup.
