from sentence_transformers import SentenceTransformer
import pandas as pd
import pickle

model = SentenceTransformer("all-MiniLM-L6-v2")

df = pd.read_csv("data/disease_symptoms.csv")

texts = df["disease"] + " " + df["symptoms"]
embeddings = model.encode(texts.tolist())

with open("vector_db/embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)
