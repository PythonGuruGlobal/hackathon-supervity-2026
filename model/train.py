import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# Absolute paths (CRITICAL FIX)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "disease_predictor.pkl")

print("📂 Reading data from:", DATA_PATH)

# Load data
df = pd.read_csv(DATA_PATH)

X = df.drop("disease", axis=1)
y = df["disease"]

print("📊 Training samples:", X.shape)

# Train model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X, y)

# Ensure model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Save model + feature names
with open(MODEL_PATH, "wb") as f:
    pickle.dump(
        {
            "model": model,
            "features": X.columns.tolist()
        },
        f
    )

print(" MODEL SAVED SUCCESSFULLY AT:")
print(MODEL_PATH)
