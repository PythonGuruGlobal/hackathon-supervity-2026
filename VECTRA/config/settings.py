import os
from dotenv import load_dotenv

# 🔑 Explicitly point to .env in project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "vectra-health")
    PINECONE_HOST = os.getenv("PINECONE_HOST")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = os.path.join(BASE_DIR, "data")
    MODEL_PATH = os.path.join(BASE_DIR, "models", "symptom_model.pkl")

    # 🔍 TEMP DEBUG
    print("DEBUG | PINECONE_API_KEY:", PINECONE_API_KEY)

settings = Settings()
