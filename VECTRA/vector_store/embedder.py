from sentence_transformers import SentenceTransformer
import os

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text):
        return self.model.encode(text).tolist()

    def get_embeddings(self, texts):
        return self.model.encode(texts).tolist()

if __name__ == "__main__":
    emb = Embedder()
    print("Embedding test shape:", len(emb.get_embedding("Fever and cough")))
