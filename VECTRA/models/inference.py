import pickle
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

class InferenceEngine:
    def __init__(self):
        self.model = None
        self.features = []
        self._load_model()
        
    def _load_model(self):
        if not os.path.exists(settings.MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {settings.MODEL_PATH}. Run train.py first.")
            
        with open(settings.MODEL_PATH, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.features = data["features"]

    def predict(self, symptoms):
        """
        Args:
            symptoms: List of symptom strings
        Returns:
            dict: {
                "top_5": [(disease, prob), ...],
                "confidence": float
            }
        """
        # Vectorize input
        input_vector = {f: 0 for f in self.features}
        for s in symptoms:
            # Simple matching, in production would need fuzzy match or consistent normalization
            # Trying exact match first
            if s in input_vector:
                input_vector[s] = 1
            else:
                # Try simple variations (strip, lower) - though training should align
                for f in self.features:
                    if s.lower().strip() == f.lower().strip():
                        input_vector[f] = 1
        
        df = pd.DataFrame([input_vector])
        
        # Predict
        probs = self.model.predict_proba(df)[0]
        classes = self.model.classes_
        
        # Get top 5
        class_probs = list(zip(classes, probs))
        class_probs.sort(key=lambda x: x[1], reverse=True)
        top_5 = class_probs[:5]
        
        confidence = float(top_5[0][1])
        
        return {
            "top_5": top_5,
            "confidence": confidence
        }

if __name__ == "__main__":
    engine = InferenceEngine()
    # print(engine.predict(["Fever", "Cough"]))
