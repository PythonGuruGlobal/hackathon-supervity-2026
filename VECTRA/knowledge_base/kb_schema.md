# Knowledge Base Schema

## Document Structure
Each document in the vector store represents a disease instance or description.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (DiseaseName_Index) |
| disease | string | Name of the disease |
| text | string | Full text description for embedding (Disease + Symptoms) |
| symptoms | string | Comma-separated list of symptoms |

## Metadata
- source: "disease_symptoms.csv"
- type: "disease_profile"
