from pinecone import Pinecone
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from vector_store.embedder import Embedder

class Retriever:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = self.pc.Index(self.index_name)
        self.embedder = Embedder()

    def retrieve(self, query, top_k=3):
        vector = self.embedder.get_embedding(query)
        results = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        return results['matches']

if __name__ == "__main__":
    retriever = Retriever()
    # Mock search
    # print(retriever.retrieve("high fever and headache"))
