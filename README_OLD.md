# Hackathon Supervity 2026

## F1: Automated MD&A Draft from Financials (RAG + Summarization)

### Problem Statement

Generate first-draft MD&A (Management Discussion & Analysis) style narrative from tabular financial statement extracts.

### Dataset

**Financial Statement Extracts (SEC)**  
https://www.kaggle.com/datasets/securities-exchange-commission/financial-statement-extracts

### Outcome (24h)

Develop a Notebook + script that:

1. **Data Processing**
   - Loads financial statements
   - Computes Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) deltas
   - Calculates key performance indicators (KPIs)

2. **Document Processing**
   - Chunks filings for efficient retrieval

3. **Narrative Generation**
   - Produces sectioned markdown draft covering:
     - Trends analysis
     - Revenue drivers
     - Risk factors
   - Generates content via LLM with citations to source chunks

### Suggested Tech Stack

- **Python** - Core programming language
- **Pandas** - Data manipulation and analysis
- **LangChain** - LLM orchestration framework
- **Embeddings** - text-embedding-3-small (or similar)
- **Chat Model** - OpenAI/Gemini/Claude or local alternatives
- **Vector Store** - ChromaDB or FAISS
- **Schema Validation** - Pydantic

### Project Structure

```
.
├── README.md
├── GUIDELINES.md
├── notebooks/          # Jupyter notebooks for exploration
├── scripts/            # Python scripts for automation
├── data/               # Financial statement data
├── output/             # Generated MD&A drafts
└── requirements.txt    # Project dependencies
```

### Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Download the dataset from Kaggle
4. Run the notebook/script to generate MD&A drafts

### License

MIT License

---

**Hackathon Duration:** 24 hours  
**Project Goal:** Automate financial narrative generation with RAG-based summarization
