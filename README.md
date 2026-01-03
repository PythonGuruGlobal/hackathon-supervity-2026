# MedGuard: FDA-Label-Grounded Medication Safety Assistant

## Problem Statement

Medication errors are a leading cause of preventable harm in healthcare. Patients frequently misunderstand drug labels, take incorrect doses, ignore food-related instructions, or rely on unreliable online sources. Traditional AI chatbots are unsafe in this domain because they may hallucinate or provide unverified medical advice.

MedGuard solves this by using **Retrieval-Augmented Generation (RAG)** over **official FDA drug labels**. Every response is grounded in regulatory-grade documentation, ensuring that users receive accurate, traceable, and safe medication information.

## Current Status

🚧 **Active Development** - Currently implementing and optimizing the RAG pipeline with FDA drug label data. Core infrastructure (FastAPI backend, ChromaDB vector store, LangChain integration) is in place. Actively working on data ingestion, embedding generation, and safety validation features.

## Getting Started

For detailed setup instructions, please refer to [SETUP.md](SETUP.md).

### Quickstart (Windows + Conda)

Prereqs:
- Install Miniconda/Anaconda
- Create a conda env named `medguard` (Python 3.10–3.12 recommended)
- Have an OpenAI API key

#### 1) Install dependencies into the conda env

```powershell
conda run -n medguard pip install -r requirements.txt
```

#### 2) Set your OpenAI API key

PowerShell (current terminal session):

```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

#### 3) Ingest FDA label data (first time only)

This creates `./chroma_db/` locally.

```powershell
conda run -n medguard python ingest_cloud_embeddings.py --limit-partitions 1
```

#### 4) Start the API server

Recommended (PowerShell-safe, uses `conda run`):

```powershell
.\start_server.ps1
```

Or:

```powershell
conda run -n medguard uvicorn app.main:app --reload
```

#### 5) Open the docs

- `http://localhost:8000/docs`

Troubleshooting notes:
- In Windows PowerShell, use `;` to chain commands (not `&&`).
- If you see `OPENAI_API_KEY environment variable is required`, set it in the same terminal where you run ingestion/server.

## System Architecture

MedGuard follows a safety-first Retrieval-Augmented Generation (RAG) pipeline:

1. The user submits a medication-related question along with optional patient context (age, pregnancy, etc.).

2. The system retrieves relevant sections (Dosage, Warnings, Contraindications, ADRs) from FDA drug labels stored in ChromaDB.

3. A Safety & Conflict Analyzer checks for contradictions or risk factors.

4. The retrieved FDA text is passed to the LLM via LangChain.

5. The LLM generates a grounded answer and a structured reminder plan.

6. The system returns a JSON response with citations and confidence.

This architecture ensures that every output is verifiable, explainable, and compliant with medical safety requirements.

## Technology Stack

| Layer        | Technology |
|--------------|------------|
| Language     | Python |
| LLM          | OpenAI GPT / Google Gemini |
| Framework    | LangChain |
| Vector Store | ChromaDB |
| API Layer    | FastAPI |
| Data Source  | openFDA Drug Label Dataset |
| Validation   | Pydantic |

## System Flow

1. The user submits a medication-related question.

2. The system enriches the query with basic patient context (age, pregnancy, etc.).

3. Relevant sections from FDA drug labels are retrieved from the vector database.

4. Safety and conflict checks are applied to validate dosage and warnings.

5. The LLM generates a grounded response using only the retrieved FDA data.

6. A structured medication reminder plan is created from the dosage instructions.

7. The final answer is returned as a JSON response with citations and confidence.

## Screenshots

### API Documentation Interface
![API Documentation](Screenshots/Screenshot%202026-01-03%20223028.png)

The FastAPI interactive documentation interface showing available endpoints for the MedGuard API. This interface allows developers and users to test the medication safety endpoints directly in the browser.

### API Response Example
![API Response](Screenshots/Screenshot%202026-01-03%20223113.png)

Example of the API response showing how MedGuard provides grounded medication information with proper citations from FDA drug labels, ensuring safety and traceability of all medical advice.

