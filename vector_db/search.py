import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

with open("vector_db/embeddings.pkl", "rb") as f:
    embeddings = pickle.load(f)

def semantic_search(query):
    query_vec = model.encode([query])[0]
    scores = np.dot(embeddings, query_vec)
    best_match = scores.argmax()
    return int(best_match)
