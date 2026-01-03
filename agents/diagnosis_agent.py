import os
import pickle
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_predictor.pkl")

with open(MODEL_PATH, "rb") as f:
    data = pickle.load(f)

model = data["model"]
feature_columns = data["features"]

def predict(symptoms):
    # Build input vector as DataFrame (fixes warning)
    input_dict = {feature: 0 for feature in feature_columns}
    for s in symptoms:
        if s in input_dict:
            input_dict[s] = 1

    input_df = pd.DataFrame([input_dict])

    disease = model.predict(input_df)[0]
    confidence = float(max(model.predict_proba(input_df)[0]))

    # ✅ RETURN EXACTLY TWO VALUES
    return disease, round(confidence, 2)
