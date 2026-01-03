CARE-AGENT
Confidence-Aware Healthcare Triage Agent (Agentic AI)
Problem Statement

Healthcare symptom checkers often suffer from overconfidence, lack of explainability, and unsafe automation, especially when powered purely by large language models.
Blind predictions or chatbot-style responses can mislead users, increase risk, and reduce trust.

Problem

How can we design an AI system that assists users responsibly by:

Handling uncertainty explicitly

Avoiding hallucinated medical advice

Explaining reasoning clearly

Escalating instead of over-automating

Goal

Build a confidence-aware healthcare triage agent that behaves like a digital healthcare coworker, not a diagnostic tool.

Dataset & Data Source

Dataset: Disease–Symptoms Dataset
Source: Kaggle (public, non-PHI)

Data Link:
https://www.kaggle.com/datasets/choongqianzheng/disease-and-symptoms-dataset

Dataset Characteristics

Tabular symptom–disease mapping

Binary / categorical symptom indicators

Suitable for probabilistic classification and explainability

No personal or sensitive patient data

This ensures ethical usage and reproducibility.

System Design (Agentic AI Architecture)

CARE-AGENT is designed as an Agentic AI decision-support system, not a chatbot.

 High-Level Flow
User Symptoms
     ↓
Symptom Encoding
     ↓
ML Prediction Engine
     ↓
Confidence Gate (Agent Decision)
     ↓
┌───────────────┬────────────────────┐
│ High Confidence│ Low Confidence     │
│ Direct Assist  │ Agentic RAG Reason │
└───────────────┴────────────────────┘
     ↓
Ethics & Safety Guardrails
     ↓
Explainable, Human-Readable Output

 Core Components
1. ML Inference Engine

Trained classification model predicts Top-3 probable conditions

Outputs probability distribution and confidence score

Ensures fast, deterministic reasoning

2. Confidence Gate (Key Innovation)

The agent decides whether to act or escalate

Prevents blind reliance on AI

Enables uncertainty-aware decision making

3. Agentic RAG (Semantic Reasoning Layer)

When confidence is low, the agent performs semantic retrieval from a vector database (e.g., Pinecone)

Retrieves disease descriptions and symptom relationships

Grounds LLM explanations in retrieved context

Reduces hallucinations and improves trust

4. Explainability & Guardrails

Human-readable explanations

Non-diagnostic language

Clear safety disclaimers

Encourages professional consultation

 Key Features

Top-3 probabilistic condition prediction

Confidence-based AI routing (Agentic decision making)

 Agentic RAG with semantic search

 Explainable AI outputs

Ethical and safety guardrails by design

 API-based Agent-as-a-Service architecture

 Assumptions & Limitations
Assumptions

Symptoms are self-reported and may be incomplete

The system is used for informational purposes only

Dataset patterns reasonably represent common symptom–disease relationships

Limitations

Not a diagnostic or emergency system

Does not replace medical professionals

Severity estimation is indicative, not clinical

These constraints are explicitly documented to ensure Responsible AI usage.
 Why This Is Innovative

Uses confidence-aware Agentic AI, not blind automation

Combines ML + Agentic RAG + guardrails

Handles uncertainty explicitly (rare in hackathon projects)

Designed for expandability without refactor:

Telemedicine triage

Severity scoring

Public health analytics

Regional disease trends

 Impact & Future Scope

CARE-AGENT can evolve into:

A telemedicine triage assistant

A hospital decision-support tool

A public health trend analysis agent

The same architecture can be reused across multiple enterprise domains, aligning with Agents-as-a-Service platforms.