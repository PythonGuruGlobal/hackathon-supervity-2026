from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.inference import InferenceEngine
from agents.perception_agent import PerceptionAgent
from agents.reasoning_agent import ReasoningAgent
from agents.decision_agent import DecisionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.explanation_agent import ExplanationAgent
from agents.safety_agent import SafetyAgent
from rag.rag_pipeline import RAGPipeline

app = FastAPI(title="VECTRA API")

# Initialize Agents
perception = PerceptionAgent()
reasoning = ReasoningAgent()
decision = DecisionAgent()
retrieval = RetrievalAgent()
explanation = ExplanationAgent()
safety = SafetyAgent()
rag = RAGPipeline()
inference = InferenceEngine()

class SymptomRequest(BaseModel):
    symptoms: List[str]

class PredictionResponse(BaseModel):
    top_5_predictions: List[tuple]
    confidence: float
    used_llm: bool
    explanation: str
    sources: List[str]
    disclaimer: str

@app.post("/predict", response_model=PredictionResponse)
def predict(request: SymptomRequest):
    # 1. Perception
    clean_symptoms = perception.process_input(request.symptoms)
    
    # 2. Reasoning
    analyzed_symptoms = reasoning.analyze(clean_symptoms)
    
    # 3. Model Inference (Always run to get confidence)
    ml_result = inference.predict(analyzed_symptoms)
    confidence = ml_result["confidence"]
    top_5 = ml_result["top_5"]
    
    # 4. Decision
    route = decision.decide_route(confidence)
    
    used_llm = False
    final_explanation = ""
    sources = []
    
    if route == "ML_DIRECT":
        top_disease = top_5[0][0]
        final_explanation = explanation.format_explanation(top_disease, confidence, analyzed_symptoms)
        used_llm = False
    else:
        # Fallback to RAG
        docs = retrieval.fetch_context(analyzed_symptoms)
        sources = docs # For display purposes
        
        # Generator
        llm_response = rag.generate_diagnosis(analyzed_symptoms, docs)
        final_explanation = explanation.format_rag_explanation(llm_response)
        used_llm = True

    # 5. Safety
    response_data = {
        "top_5_predictions": top_5,
        "confidence": confidence,
        "used_llm": used_llm,
        "explanation": final_explanation,
        "sources": sources
    }
    
    safe_response = safety.attach_disclaimer(response_data)
    
    return safe_response

@app.get("/")
def health_check():
    return {"status": "VECTRA System Ready"}
