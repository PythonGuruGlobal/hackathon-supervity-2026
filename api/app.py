from fastapi import FastAPI
from agents.symptom_agent import read_symptoms
from agents.diagnosis_agent import predict
from agents.explanation_agent import explain

app = FastAPI()

@app.get("/")
def root():
    return {"status": "VECTRA API running"}

@app.post("/predict")
def predict_disease(symptoms: str):
    symptom_list = read_symptoms(symptoms)
    disease, confidence = predict(symptom_list)
    return explain(disease, symptom_list, confidence)


