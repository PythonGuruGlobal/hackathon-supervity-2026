VECTRA – Health Assistant

A Safety-Aware Retrieval-Augmented Healthcare AI System

Overview

VECTRA is an AI-powered healthcare decision-support system designed to demonstrate the responsible integration of traditional Machine Learning and Large Language Models (LLMs) in sensitive medical domains.

Unlike conversational symptom checkers or chatbot-style medical assistants, VECTRA follows a guided, guarded, and explainable architecture. The system delivers structured, professional, and non-diagnostic health insights, making it suitable for academic, research, and demonstration purposes.

VECTRA is not a diagnostic tool, not an autonomous agent, and not a replacement for healthcare professionals.

Problem Statement

Many AI-based healthcare assistants rely heavily on LLMs, leading to:

Overconfident or hallucinated medical advice

Poor explainability of predictions

Unsafe automation in high-risk domains

Conversational outputs unsuitable for clinical settings

Pure LLM-driven systems behave like chatbots rather than decision-support tools, which reduces trust and increases risk in healthcare applications.

Proposed Solution

VECTRA introduces a safety-aware hybrid intelligence architecture that:

Separates deterministic prediction from generative explanation

Uses Machine Learning as the primary reasoning engine

Employs Retrieval-Augmented Generation (RAG) in a controlled manner

Enforces strict guardrails at architectural, prompt, and output levels

Degrades gracefully when LLM services are unavailable

The system prioritizes reliability, explainability, and safety over conversational flexibility.

Project Objectives

Demonstrate responsible AI design in healthcare

Maintain professional, clinical output tone

Prevent over-reliance on LLMs

Provide explainable and consistent results

Enforce safety and ethical guardrails by design

Support academic reproducibility and industry demos

High-Level Architecture

End-to-End Flow

User-Provided Symptoms
↓
Symptom Encoding & Validation
↓
Machine Learning Prediction Layer
↓
Semantic Knowledge Retrieval (Vector Database)
↓
Guided RAG Explanation Layer (Optional LLM)
↓
Response Sanitization & Safety Checks
↓
Structured, Professional Output

Core Components
1. Machine Learning Prediction Layer

Model: Random Forest Classifier

Input: Structured symptom indicators

Output:

Probabilistic condition predictions

Confidence-weighted results

Purpose

Fast, deterministic inference

Explainable feature-based reasoning

Eliminates hallucinations in core medical reasoning

The ML layer remains independent of LLM availability.

2. Knowledge Base & Vector Store

Curated symptom–disease medical documents

Text embeddings stored in Pinecone

Semantic retrieval ensures context relevance

Why Pinecone

Production-ready vector database

Low-latency semantic search

Scalable and reliable

This layer ensures all explanations are grounded in verified knowledge.

3. Guided and Guarded RAG Pipeline

VECTRA uses controlled RAG, not free-form generation.

Retrieval

Semantic search retrieves top relevant documents

Context size strictly limited

Prompt Guidance
Prompts enforce:

Clinical and educational tone

No conversational language

No emojis or markdown

No diagnosis, treatment, or medication advice

LLM Role

Used only for explanation coherence

Cannot introduce new medical facts

Fully constrained by retrieved context

4. Fail-Safe & Fallback Mechanism

If:

OPENAI_API_KEY is missing

LLM service is unavailable

LLM call fails

Then:

System falls back to retrieval-only responses

No crashes or broken outputs

Full functionality retained

This ensures system reliability and reproducibility.

5. Response Sanitization & Safety Layer

Before output delivery:

Responses are checked for unsafe claims

Tone and structure are validated

Consistency with ML predictions is enforced

This aligns outputs with clinical communication standards.

Guardrails & Safety Design

VECTRA enforces multi-layer guardrails:

Architectural Guardrails

No autonomous diagnosis

Decision-support only

ML Guardrails

Deterministic, explainable predictions

No stochastic reasoning

Retrieval Guardrails

Curated, closed knowledge base

No open internet access

Prompt Guardrails

Strict clinical language enforcement

No conversational or chatbot tone

Output Guardrails

Structured, professional format

No emojis or markdown

Fail-Safe Guardrails

LLM optionality

Graceful degradation

These guardrails make VECTRA aligned with Responsible AI principles.

Key Features

Hybrid ML + RAG architecture

Safety-aware design

Explainable predictions

Professional, clinical outputs

LLM-optional execution

Fail-safe fallback behavior

Academic and enterprise ready

Dataset & Ethics

Public, non-PHI symptom–disease datasets

No personal or sensitive patient data

Ethical and reproducible usage

Technology Stack
Backend

Python 3.9+

FastAPI

Scikit-learn

Pinecone

OpenAI API (optional)

Frontend

Node.js 16+

React / Vite

Form-based UI (non-chat)

Installation & Setup
Clone Repository
git clone https://github.com/your-username/vectra.git
cd vectra

Backend Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

Environment Configuration

Create a .env file:

PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=vectra-health
OPENAI_API_KEY=optional_openai_key

Knowledge Base Indexing
python knowledge_base/build_kb.py
python vector_store/indexer.py

Frontend Setup
cd ui/frontend
npm install
npm run dev

Running the Application
Backend
python -m uvicorn api.vectra_api:app --reload

Frontend
npm run dev

Assumptions & Limitations
Assumptions

Symptoms are self-reported

Used only for educational purposes

Limitations

Not a diagnostic system

Not an emergency tool

No treatment recommendations

These constraints are explicit by design.

Innovation Highlights

Safety-first RAG, not blind LLM usage

Deterministic ML core

Guardrails at every layer

Professional healthcare-grade outputs

Future Scope

Confidence-aware routing (Agentic upgrade)

Severity estimation

Telemedicine triage support

Public health analytics

Regional disease trend analysis

Disclaimer

VECTRA is intended strictly for educational, academic, and research purposes.
It does not provide medical diagnosis, treatment, or emergency guidance.
Users must consult qualified healthcare professionals for medical decisions.
