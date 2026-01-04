import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

def train_model():
    data_path = os.path.join(settings.DATA_DIR, "raw", "disease_symptoms.csv")
    if not os.path.exists(data_path):
        print("Data file not found.")
        return

    df = pd.read_csv(data_path)
    
    # Preprocessing
    # Assuming cols are Disease, Symptom_1, Symptom_2, ...
    # We need to one-hot encode symptoms for the model
    
    cols = [c.strip() for c in df.columns]
    df.columns = cols
    
    # Get all unique symptoms
    symptom_cols = [c for c in df.columns if c != 'Disease']
    unique_symptoms = set()
    for col in symptom_cols:
        unique_symptoms.update(df[col].dropna().unique())
        
    unique_symptoms = sorted(list(unique_symptoms))
    print(f"Found {len(unique_symptoms)} unique symptoms.")
    
    # Create empty dataframe for encoded data
    encoded_data = []
    
    for _, row in df.iterrows():
        disease = row['Disease']
        symptoms = []
        for col in symptom_cols:
            val = row[col]
            if pd.notna(val):
                symptoms.append(val)
        
        # Vectorize
        vector = {s: 0 for s in unique_symptoms}
        for s in symptoms:
            if s in vector:
                vector[s] = 1
                
        vector['Disease'] = disease
        encoded_data.append(vector)
        
    encoded_df = pd.DataFrame(encoded_data)
    
    # X and y
    X = encoded_df.drop('Disease', axis=1)
    y = encoded_df['Disease']
    
    # Train
    print("Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    # Save artifacts
    model_data = {
        "model": clf,
        "features": list(X.columns),
        "classes": list(clf.classes_)
    }
    
    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
    with open(settings.MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)
        
    print(f"Model saved to {settings.MODEL_PATH}")

if __name__ == "__main__":
    train_model()
