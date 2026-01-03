import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_store.retriever import Retriever

class RetrievalAgent:
    def __init__(self):
        self.retriever = Retriever()

    def fetch_context(self, symptoms):
        query = ", ".join(symptoms)
        # Setup for RAG: retrieve documents related to the symptoms
        results = self.retriever.retrieve(query, top_k=3)
        
        docs = []
        for match in results:
            if 'metadata' in match:
                docs.append(match['metadata'].get('text', ''))
                
        return docs
