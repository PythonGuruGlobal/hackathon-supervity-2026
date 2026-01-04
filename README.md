# MedGuard: FDA-Label-Grounded Medication Safety Assistant

## Problem Statement

Medication errors are a leading cause of preventable harm in healthcare. Patients frequently misunderstand drug labels, take incorrect doses, ignore food-related instructions, or rely on unreliable online sources. Traditional AI chatbots are unsafe in this domain because they may hallucinate or provide unverified medical advice.

MedGuard solves this by using **Retrieval-Augmented Generation (RAG)** over **official FDA drug labels**. Every response is grounded in regulatory-grade documentation, ensuring that users receive accurate, traceable, and safe medication information.

## Current Status

🚧 **Active Development** - Core RAG backend is working end-to-end (FastAPI + LangChain + ChromaDB). Currently iterating on **data ingestion/chunking strategies** to maximize coverage and answer quality while keeping runtime/cost practical for demos (sampling, targeted drugs, richer FDA section extraction, and retrieval/debug tooling).

## Getting Started

For detailed setup instructions, please refer to [SETUP.md](SETUP.md).

### Quickstart (Windows + Conda)

The full openFDA label dataset is large. For a demo/hackathon, ingest a small subset (4–5 partitions) and cap the total chunks so setup finishes quickly while still proving the end-to-end RAG flow.

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

### System architecture (RAG + safety-first pipeline)
![Architecture flow](Screenshots/Flowchart.jpeg)

### Optional workflow automation (n8n)
![n8n workflow](Screenshots/n8n%20Workflow.jpeg)

### FastAPI docs (endpoints)
![FastAPI docs - endpoints](Screenshots/api-docs-endpoints.png)

Swagger UI showing the available endpoints: `/ask`, `/validate`, `/schedule`.

### FastAPI docs (schemas)
![FastAPI docs - schemas](Screenshots/api-docs-schemas.png)

Request/response schemas used by the API.

### Testing `/ask` in Swagger UI
![Ask request body](Screenshots/testing/ask-request-body.png)

### Grounded behavior when label text is not found
![Ask response example](Screenshots/testing/ask-response-example.png)

Example response: **"This information is not available in the FDA drug label."**

### JSON-only grounded response (successful case)
![Proper JSON response](Screenshots/testing/proper_response.png)

