import chromadb
import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=False)
except Exception:
    pass

PERSIST_DIRECTORY = "./chroma_db"

def get_embedding_function():
    """Get OpenAI embedding function."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    return OpenAIEmbeddings(model="text-embedding-3-small")

def get_vector_store():
    embedding_func = get_embedding_function()
    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_func,
        collection_name="fda_labels"
    )
