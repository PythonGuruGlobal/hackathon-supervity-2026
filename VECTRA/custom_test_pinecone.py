try:
    from pinecone import Pinecone
    print("SUCCESS: Pinecone imported successfully.")
except Exception as e:
    print(f"FAILURE: {e}")
