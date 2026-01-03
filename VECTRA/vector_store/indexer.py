import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import os
import sys
import time

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config.settings import settings
from vector_store.embedder import Embedder


class Indexer:
    def __init__(self):
        # ✅ HARD FAIL if key is missing (prevents silent bugs)
        if not settings.PINECONE_API_KEY:
            raise RuntimeError(" PINECONE_API_KEY not loaded")

        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

        self.index_name = settings.PINECONE_INDEX_NAME
        self.embedder = Embedder()
        self.dimension = 384  # all-MiniLM-L6-v2

    def create_index_if_not_exists(self):
        existing_indexes = [
            idx["name"] for idx in self.pc.list_indexes().get("indexes", [])
        ]

        if self.index_name not in existing_indexes:
            print(f"🚀 Creating Pinecone index: {self.index_name}")

            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

            # ⏳ Wait until index is ready
            while True:
                status = self.pc.describe_index(self.index_name).status
                if status["ready"]:
                    break
                print("⏳ Waiting for index to be ready...")
                time.sleep(2)

            print("✅ Index is ready.")

    def index_data(self):
        kb_path = os.path.join(
            settings.BASE_DIR,
            "knowledge_base",
            "disease_docs.csv"
        )

        if not os.path.exists(kb_path):
            raise FileNotFoundError(
                " Knowledge base not found. Run build_kb.py first."
            )

        df = pd.read_csv(kb_path)

        if df.empty:
            raise ValueError("Knowledge base CSV is empty.")

        self.create_index_if_not_exists()

        index = self.pc.Index(self.index_name)

        batch_size = 100
        for start in range(0, len(df), batch_size):
            end = min(start + batch_size, len(df))
            batch = df.iloc[start:end]

            ids = batch["id"].astype(str).tolist()
            texts = batch["text"].tolist()

            embeddings = self.embedder.get_embeddings(texts)

            # ✅ Store only lightweight metadata
            metadatas = [
                {"source": "disease_kb"}
                for _ in range(len(ids))
            ]

            vectors = [
                (id_, embedding, metadata)
                for id_, embedding, metadata in zip(ids, embeddings, metadatas)
            ]

            index.upsert(vectors=vectors)
            print(f"📌 Indexed records {start} → {end}")

        print("🎉 Knowledge base indexing completed successfully.")


if __name__ == "__main__":
    indexer = Indexer()
    indexer.index_data()
