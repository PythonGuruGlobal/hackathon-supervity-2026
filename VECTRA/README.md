# VECTRA: Agentic Healthcare AI

VECTRA is an advanced multi-agent disease prediction system that combines robust Machine Learning with Semantic Search and Large Language Models (RAG).

## Features
- **Hybrid Reasoning**: Uses Random Forest for high-confidence predictions and LLM+RAG for complex cases.
- **Multi-Agent Architecture**: Specialized agents for Perception, Reasoning, Decision, Retrieval, and Safety.
- **Explainable AI**: Provides clear explanations for every diagnosis.
- **Safety First**: Integrated medical disclaimers and guardrails.

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

3. **Data & Training**
   Build the knowledge base and train the model:
   ```bash
   python knowledge_base/build_kb.py
   python vector_store/indexer.py  # Requires valid Pinecone Key
   python models/train.py
   ```

4. **Run Server**
   ```bash
   uvicorn api.vectra_api:app --reload
   ```

5. **Run Frontend**
   (Requires React setup - instructions generic)
   The `ui/frontend` folder contains the source components.

## API Usage
POST `/predict`
```json
{
  "symptoms": ["fever", "cough", "fatigue"]
}
```

## Disclaimer
This system is for educational purposes only. Please consult a licensed medical professional.
