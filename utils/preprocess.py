import pandas as pd
import os
from sklearn.preprocessing import MultiLabelBinarizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "DiseaseAndSymptoms.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed_data.csv")

# Load raw data
df = pd.read_csv(RAW_DATA_PATH)

print("📌 Columns:", df.columns.tolist())

# Normalize column names
df.columns = [c.lower() for c in df.columns]

# Disease column
disease_col = "disease"

# Symptom columns (symptom_1 ... symptom_17)
symptom_cols = [c for c in df.columns if c.startswith("symptom")]

# Combine symptoms into list
df["symptoms"] = df[symptom_cols].apply(
    lambda row: [str(s).strip().lower() for s in row if pd.notna(s)],
    axis=1
)

# One-hot encode symptoms
mlb = MultiLabelBinarizer()
encoded = mlb.fit_transform(df["symptoms"])

encoded_df = pd.DataFrame(encoded, columns=mlb.classes_)
encoded_df["disease"] = df[disease_col]

# Save processed data
encoded_df.to_csv(OUTPUT_PATH, index=False)

print("processed_data.csv created successfully")
print(f"Total symptoms encoded: {len(mlb.classes_)}")
