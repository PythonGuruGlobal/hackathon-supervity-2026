"""
Script to download openFDA drug label data, chunk it, generate embeddings
using OpenAI (cloud-based), and store them in ChromaDB.
"""

import json
import glob
import os
import sys
import argparse
import requests
import zipfile
import io
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
import chromadb

# Configuration
DATA_DIR = "./Data"
PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "fda_labels"
DOWNLOAD_INDEX_URL = "https://api.fda.gov/download.json"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_embedding_function():
    """
    Returns an embedding function using OpenAI.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("ERROR: OPENAI_API_KEY environment variable is required!")
        print("Please set OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    print("Using OpenAI embeddings (text-embedding-3-small)")
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model="text-embedding-3-small")


def download_data(limit_partitions: Optional[int] = None):
    """
    Downloads OpenFDA drug label data if not present.
    
    Args:
        limit_partitions: If set, only download this many partitions (for testing)
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Check if we already have JSON files
    existing_files = glob.glob(os.path.join(DATA_DIR, "**/*.json"), recursive=True)
    if existing_files:
        print(f"Found {len(existing_files)} existing JSON files in {DATA_DIR}. Skipping download.")
        return
    
    print("Fetching OpenFDA download index...")
    try:
        response = requests.get(DOWNLOAD_INDEX_URL, timeout=30)
        response.raise_for_status()
        index_data = response.json()
        
        # Navigate to drug -> label
        partitions = index_data.get('results', {}).get('drug', {}).get('label', {}).get('partitions', [])
        
        if not partitions:
            print("No partitions found in OpenFDA index.")
            return
        
        # Limit partitions if specified (for testing)
        if limit_partitions:
            partitions = partitions[:limit_partitions]
            print(f"Limiting to first {limit_partitions} partition(s) for testing...")
        
        print(f"Found {len(partitions)} partition(s). Downloading...")
        
        for idx, part in enumerate(partitions, 1):
            download_url = part['file']
            file_name = os.path.basename(download_url)
            save_path = os.path.join(DATA_DIR, file_name)
            
            # Skip if already exists
            if os.path.exists(save_path):
                print(f"  [{idx}/{len(partitions)}] {file_name} already exists, skipping...")
                continue
            
            print(f"  [{idx}/{len(partitions)}] Downloading {file_name}...")
            file_resp = requests.get(download_url, stream=True, timeout=60)
            file_resp.raise_for_status()
            
            # OpenFDA files are often Zipped JSONs
            if download_url.endswith('.zip') or file_name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(file_resp.content)) as z:
                    z.extractall(DATA_DIR)
                    print(f"    Extracted to {DATA_DIR}")
            else:
                with open(save_path, 'wb') as f:
                    for chunk in file_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"    Saved to {save_path}")
        
        print("Download complete.")
        
    except Exception as e:
        print(f"Failed to download data: {e}")
        raise


def extract_drug_info(entry):
    """
    Extracts relevant fields from a single drug entry.
    """
    info = {}
    
    # Drug Name - try multiple fields
    drug_name = None
    if 'openfda' in entry:
        openfda = entry['openfda']
        if 'brand_name' in openfda and openfda['brand_name']:
            drug_name = openfda['brand_name'][0] if isinstance(openfda['brand_name'], list) else openfda['brand_name']
        elif 'generic_name' in openfda and openfda['generic_name']:
            drug_name = openfda['generic_name'][0] if isinstance(openfda['generic_name'], list) else openfda['generic_name']
        elif 'substance_name' in openfda and openfda['substance_name']:
            drug_name = openfda['substance_name'][0] if isinstance(openfda['substance_name'], list) else openfda['substance_name']
    
    # Also check product_ndc
    if not drug_name and 'product_ndc' in entry:
        drug_name = entry['product_ndc']
    
    if not drug_name:
        return None  # Skip if no name
    
    info['drug_name'] = drug_name
    
    # Extract text fields - build comprehensive text content
    text_parts = []
    
    # Dosage
    if 'dosage_and_administration' in entry:
        dosage = entry['dosage_and_administration']
        if isinstance(dosage, list) and dosage:
            info['dosage'] = dosage[0]
            text_parts.append(f"Dosage and Administration: {dosage[0]}")
        elif isinstance(dosage, str):
            info['dosage'] = dosage
            text_parts.append(f"Dosage and Administration: {dosage}")
    
    # Warnings
    if 'warnings' in entry:
        warnings = entry['warnings']
        if isinstance(warnings, list) and warnings:
            info['warnings'] = warnings[0]
            text_parts.append(f"Warnings: {warnings[0]}")
        elif isinstance(warnings, str):
            info['warnings'] = warnings
            text_parts.append(f"Warnings: {warnings}")
    
    # Contraindications
    if 'contraindications' in entry:
        contraindications = entry['contraindications']
        if isinstance(contraindications, list) and contraindications:
            info['contraindications'] = contraindications[0]
            text_parts.append(f"Contraindications: {contraindications[0]}")
        elif isinstance(contraindications, str):
            info['contraindications'] = contraindications
            text_parts.append(f"Contraindications: {contraindications}")
    
    # Indications
    if 'indications_and_usage' in entry:
        indications = entry['indications_and_usage']
        if isinstance(indications, list) and indications:
            text_parts.append(f"Indications and Usage: {indications[0]}")
        elif isinstance(indications, str):
            text_parts.append(f"Indications and Usage: {indications}")
    
    # Adverse Reactions
    if 'adverse_reactions' in entry:
        adverse = entry['adverse_reactions']
        if isinstance(adverse, list) and adverse:
            text_parts.append(f"Adverse Reactions: {adverse[0]}")
        elif isinstance(adverse, str):
            text_parts.append(f"Adverse Reactions: {adverse}")
    
    # Drug Interactions
    if 'drug_interactions' in entry:
        interactions = entry['drug_interactions']
        if isinstance(interactions, list) and interactions:
            text_parts.append(f"Drug Interactions: {interactions[0]}")
        elif isinstance(interactions, str):
            text_parts.append(f"Drug Interactions: {interactions}")
    
    # Full label text (if available)
    if 'spl_product_data_elements' in entry:
        spl_text = entry['spl_product_data_elements']
        if isinstance(spl_text, list) and spl_text:
            text_parts.append(f"Full Label Text: {spl_text[0]}")
        elif isinstance(spl_text, str):
            text_parts.append(f"Full Label Text: {spl_text}")
    
    # If we have any text content, include it
    if text_parts:
        info['text_content'] = "\n\n".join(text_parts)
    else:
        # If no structured fields, skip this entry
        return None
    
    return info


def create_documents(extracted_data: List[dict]) -> List[Document]:
    """
    Creates LangChain Document objects from extracted drug data.
    """
    documents = []
    for item in extracted_data:
        # Build the full text
        text_parts = [f"Drug Name: {item['drug_name']}"]
        
        if 'text_content' in item:
            text_parts.append(item['text_content'])
        
        full_text = "\n\n".join(text_parts)
        
        # Create metadata
        metadata = {
            "drug_name": item['drug_name']
        }
        
        # Add other metadata if available
        if 'dosage' in item:
            metadata['has_dosage'] = True
        if 'warnings' in item:
            metadata['has_warnings'] = True
        if 'contraindications' in item:
            metadata['has_contraindications'] = True
        
        documents.append(Document(page_content=full_text, metadata=metadata))
    
    return documents


def load_and_chunk_data() -> List[Document]:
    """
    Loads JSON files, extracts drug information, and chunks the documents.
    """
    json_files = glob.glob(os.path.join(DATA_DIR, "**/*.json"), recursive=True)
    
    if not json_files:
        print(f"No JSON files found in {DATA_DIR}")
        return []
    
    all_documents = []
    
    # Text splitter configuration
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    print(f"Processing {len(json_files)} JSON file(s)...")
    
    for file_path in json_files:
        print(f"  Processing {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results = data.get('results', [])
                
                if not results:
                    print(f"    No 'results' found in {file_path}")
                    continue
                
                extracted_items = []
                for entry in results:
                    info = extract_drug_info(entry)
                    if info:
                        extracted_items.append(info)
                
                if extracted_items:
                    docs = create_documents(extracted_items)
                    all_documents.extend(docs)
                    print(f"    Extracted {len(extracted_items)} drug entries, created {len(docs)} documents")
                
        except json.JSONDecodeError as e:
            print(f"    Error parsing JSON in {file_path}: {e}")
        except Exception as e:
            print(f"    Error loading {file_path}: {e}")
    
    if not all_documents:
        print("No documents created from the data files.")
        return []
    
    print(f"\nTotal documents before chunking: {len(all_documents)}")
    print(f"Chunking with size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}...")
    
    # Chunk the documents
    chunked_docs = splitter.split_documents(all_documents)
    
    print(f"Total chunks after splitting: {len(chunked_docs)}")
    
    return chunked_docs


def ingest_to_chromadb(documents: List[Document], embedding_function, clear_existing: bool = False):
    """
    Stores documents with embeddings in ChromaDB.
    
    Args:
        documents: List of Document objects to ingest
        embedding_function: Embedding function to use
        clear_existing: If True, clear existing collection before ingesting
    """
    if not documents:
        print("No documents to ingest.")
        return
    
    print(f"\nInitializing ChromaDB at {PERSIST_DIRECTORY}...")
    
    # Create or get the vector store
    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME
    )
    
    # Check if collection already has data
    existing_count = vectorstore._collection.count()
    if existing_count > 0:
        print(f"Collection '{COLLECTION_NAME}' already has {existing_count} documents.")
        
        if clear_existing:
            print("Clearing existing collection and re-ingesting...")
            # Delete the collection and recreate
            chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
            try:
                chroma_client.delete_collection(COLLECTION_NAME)
            except:
                pass
            vectorstore = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embedding_function,
                collection_name=COLLECTION_NAME
            )
        else:
            print("Appending to existing collection...")
    
    # Batch add documents
    batch_size = 100  # Smaller batches for API rate limits
    total_docs = len(documents)
    
    print(f"\nIngesting {total_docs} chunks to ChromaDB...")
    print("This may take a while depending on the number of documents and API rate limits...")
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        try:
            vectorstore.add_documents(batch)
            print(f"  Ingested {min(i + batch_size, total_docs)}/{total_docs} chunks")
        except Exception as e:
            print(f"  Error ingesting batch {i//batch_size + 1}: {e}")
            # Continue with next batch
            continue
    
    # Persist the collection
    vectorstore.persist()
    
    final_count = vectorstore._collection.count()
    print(f"\nIngestion complete! Total documents in ChromaDB: {final_count}")


def main():
    """
    Main function to orchestrate the entire ingestion process.
    """
    parser = argparse.ArgumentParser(
        description="Download openFDA drug label data, chunk it, generate embeddings, and store in ChromaDB"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing ChromaDB collection before ingesting"
    )
    parser.add_argument(
        "--limit-partitions",
        type=int,
        default=None,
        help="Limit the number of data partitions to download (for testing)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OpenFDA Drug Label Data Ingestion with Cloud Embeddings")
    print("=" * 60)
    print()
    
    # Check for API key
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("ERROR: OPENAI_API_KEY environment variable is required!")
        print("Please set OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    # Get embedding function
    embedding_function = get_embedding_function()
    print()
    
    # Step 1: Download data
    print("Step 1: Downloading OpenFDA drug label data...")
    print("-" * 60)
    try:
        download_data(limit_partitions=args.limit_partitions)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)
    print()
    
    # Step 2: Load and chunk data
    print("Step 2: Loading and chunking data...")
    print("-" * 60)
    documents = load_and_chunk_data()
    
    if not documents:
        print("No documents to process. Exiting.")
        sys.exit(1)
    print()
    
    # Step 3: Generate embeddings and store in ChromaDB
    print("Step 3: Generating embeddings and storing in ChromaDB...")
    print("-" * 60)
    ingest_to_chromadb(documents, embedding_function, clear_existing=args.clear_existing)
    
    print()
    print("=" * 60)
    print("Ingestion process completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

