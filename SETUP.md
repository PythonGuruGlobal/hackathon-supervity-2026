# Local Setup Guide

## ⚠️ Important: Python Version Requirement

**ChromaDB requires Python 3.8-3.12**. Python 3.13+ may have compatibility issues.

If you're using Python 3.14, please use **Python 3.11 or 3.12** instead. See `LOCAL_SETUP.md` for details.

## Prerequisites

- Python 3.8-3.12 (3.11 or 3.12 recommended)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Virtual environment (recommended)

## Step-by-Step Setup

### 1. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set OpenAI API Key

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Or create a `.env` file** (recommended for persistence):
```env
OPENAI_API_KEY=your-api-key-here
```

Then install `python-dotenv` and load it:
```bash
pip install python-dotenv
```

### 4. Run Data Ingestion (First Time Only)

This populates your ChromaDB with drug label data:

```bash
# For testing (downloads 1 partition - faster, ~5-10 minutes)
python ingest_cloud_embeddings.py --limit-partitions 1

# For full dataset (downloads all partitions - slower, ~30-60 minutes)
python ingest_cloud_embeddings.py
```

**Note:** This only needs to be run once. The data persists in `./chroma_db/` directory.

### 5. Start the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 6. Test the API

Visit http://localhost:8000/docs to test the endpoints interactively, or use curl:

```bash
# Test question answering
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"drug_name": "Aspirin", "query": "What are the side effects?"}'
```

## Troubleshooting

### Missing Dependencies

If you get import errors, make sure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

### API Key Not Found

Make sure the environment variable is set:
```powershell
# Check if set (PowerShell)
$env:OPENAI_API_KEY

# Check if set (Linux/Mac)
echo $OPENAI_API_KEY
```

### ChromaDB Errors

If you get ChromaDB errors, try clearing and re-ingesting:
```bash
python ingest_cloud_embeddings.py --clear-existing --limit-partitions 1
```

### Port Already in Use

If port 8000 is in use, specify a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## Project Structure

```
supervity/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── chains.py        # LangChain chains (QA, validation, schedule)
│   └── rag.py           # Vector store configuration
├── ingest_cloud_embeddings.py  # Data ingestion script
├── requirements.txt     # Python dependencies
├── chroma_db/          # ChromaDB database (created after ingestion)
└── Data/               # Downloaded FDA data (created after ingestion)
```

## Next Steps

1. ✅ Set up environment
2. ✅ Install dependencies
3. ✅ Set API key
4. ✅ Run ingestion
5. ✅ Start server
6. 🎉 Use the API!

