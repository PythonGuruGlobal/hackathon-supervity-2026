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
import time
import math
import re
import heapq
import random
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
import chromadb

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=False)
except Exception:
    pass

DATA_DIR = "./Data"
PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "fda_labels"
DOWNLOAD_INDEX_URL = "https://api.fda.gov/download.json"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_drug_name(value: str) -> str:
    """Normalize drug names for more reliable matching across casing/punctuation."""
    if not value:
        return ""
    v = value.strip().lower()
    v = _NON_ALNUM_RE.sub(" ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


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
    # Some extracted datasets may contain directories named like "*.json" (e.g. a folder
    # called "drug-label-0001-of-0013.json" that contains the actual file). Filter to files.
    existing_files = [p for p in existing_files if os.path.isfile(p)]
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
    
    # Drug Name - try multiple fields + keep aliases for matching
    drug_name = None
    aliases: List[str] = []
    if 'openfda' in entry:
        openfda = entry['openfda']
        if 'brand_name' in openfda and openfda['brand_name']:
            if isinstance(openfda['brand_name'], list):
                aliases.extend([x for x in openfda['brand_name'] if isinstance(x, str)])
                drug_name = openfda['brand_name'][0]
            elif isinstance(openfda['brand_name'], str):
                aliases.append(openfda['brand_name'])
                drug_name = openfda['brand_name']
        elif 'generic_name' in openfda and openfda['generic_name']:
            if isinstance(openfda['generic_name'], list):
                aliases.extend([x for x in openfda['generic_name'] if isinstance(x, str)])
                drug_name = openfda['generic_name'][0]
            elif isinstance(openfda['generic_name'], str):
                aliases.append(openfda['generic_name'])
                drug_name = openfda['generic_name']
        elif 'substance_name' in openfda and openfda['substance_name']:
            if isinstance(openfda['substance_name'], list):
                aliases.extend([x for x in openfda['substance_name'] if isinstance(x, str)])
                drug_name = openfda['substance_name'][0]
            elif isinstance(openfda['substance_name'], str):
                aliases.append(openfda['substance_name'])
                drug_name = openfda['substance_name']
    
    # Also check product_ndc
    if not drug_name and 'product_ndc' in entry:
        drug_name = entry['product_ndc']
        aliases.append(drug_name)
    
    if not drug_name:
        return None  # Skip if no name
    
    info['drug_name'] = drug_name
    # Always include the primary name as an alias
    if drug_name and drug_name not in aliases:
        aliases.insert(0, drug_name)
    # De-dupe aliases while keeping order
    seen = set()
    deduped: List[str] = []
    for a in aliases:
        if not isinstance(a, str):
            continue
        key = normalize_drug_name(a)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(a)
    info["aliases"] = deduped
    
    # Extract label sections. More sections = better coverage in the backend.
    def _as_text(value, max_chars: int = 12000) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            v = value.strip()
            return v[:max_chars] if v else None
        if isinstance(value, list):
            parts = []
            for x in value:
                if isinstance(x, str) and x.strip():
                    parts.append(x.strip())
                if len(parts) >= 3:  # keep it bounded
                    break
            if not parts:
                return None
            joined = "\n".join(parts)
            return joined[:max_chars]
        return None

    # Map openFDA keys -> (output key, human label)
    section_fields = [
        ("boxed_warning", "Boxed Warning"),
        ("warnings", "Warnings"),
        ("warnings_and_precautions", "Warnings and Precautions"),
        ("contraindications", "Contraindications"),
        ("dosage_and_administration", "Dosage and Administration"),
        ("dosage_forms_and_strengths", "Dosage Forms and Strengths"),
        ("indications_and_usage", "Indications and Usage"),
        ("adverse_reactions", "Adverse Reactions"),
        ("drug_interactions", "Drug Interactions"),
        ("use_in_specific_populations", "Use in Specific Populations"),
        ("pregnancy", "Pregnancy"),
        ("lactation", "Lactation"),
        ("pediatric_use", "Pediatric Use"),
        ("geriatric_use", "Geriatric Use"),
        ("overdosage", "Overdosage"),
        ("how_supplied", "How Supplied"),
        ("storage_and_handling", "Storage and Handling"),
        ("patient_counseling_information", "Patient Counseling Information"),
        ("clinical_pharmacology", "Clinical Pharmacology"),
        ("mechanism_of_action", "Mechanism of Action"),
    ]

    text_parts = []
    has_any_section = False
    for key, label in section_fields:
        if key in entry:
            txt = _as_text(entry.get(key))
            if txt:
                info[key] = txt
                text_parts.append(f"{label}: {txt}")
                has_any_section = True

    # Back-compat: keep these common keys used elsewhere
    if "dosage_and_administration" in info and "dosage" not in info:
        info["dosage"] = info["dosage_and_administration"]

    # Full label text (very large) — keep a bounded sample as a last resort
    if not has_any_section and "spl_product_data_elements" in entry:
        spl_txt = _as_text(entry.get("spl_product_data_elements"), max_chars=12000)
        if spl_txt:
            info["full_label"] = spl_txt
            text_parts.append(f"Full Label Text: {spl_txt}")
            has_any_section = True

    if text_parts:
        info["text_content"] = "\n\n".join(text_parts)
    else:
        return None
    
    return info


def create_documents(extracted_data: List[dict]) -> List[Document]:
    """
    Creates LangChain Document objects from extracted drug data.
    """
    documents = []
    for item in extracted_data:
        drug_name = item["drug_name"]
        drug_name_norm = normalize_drug_name(drug_name)
        aliases = item.get("aliases", [])
        # Chroma metadata must be scalar types (no lists/dicts). Keep a compact string for debugging.
        aliases_str = " | ".join([a for a in aliases if isinstance(a, str)][:8])

        # Section-based docs improve retrieval quality vs one huge merged blob.
        # Include many FDA sections for better coverage.
        section_order = [
            ("boxed_warning", "Boxed Warning"),
            ("warnings", "Warnings"),
            ("warnings_and_precautions", "Warnings and Precautions"),
            ("contraindications", "Contraindications"),
            ("dosage_and_administration", "Dosage and Administration"),
            ("dosage_forms_and_strengths", "Dosage Forms and Strengths"),
            ("indications_and_usage", "Indications and Usage"),
            ("adverse_reactions", "Adverse Reactions"),
            ("drug_interactions", "Drug Interactions"),
            ("use_in_specific_populations", "Use in Specific Populations"),
            ("pregnancy", "Pregnancy"),
            ("lactation", "Lactation"),
            ("pediatric_use", "Pediatric Use"),
            ("geriatric_use", "Geriatric Use"),
            ("overdosage", "Overdosage"),
            ("how_supplied", "How Supplied"),
            ("storage_and_handling", "Storage and Handling"),
            ("patient_counseling_information", "Patient Counseling Information"),
            ("clinical_pharmacology", "Clinical Pharmacology"),
            ("mechanism_of_action", "Mechanism of Action"),
            ("full_label", "Full Label Text"),
            ("text_content", "FDA Label Excerpt"),
        ]

        sections: List[tuple[str, str]] = []
        for key, label in section_order:
            txt = item.get(key)
            if isinstance(txt, str) and txt.strip():
                sections.append((label, txt))

        # If we still have nothing, skip
        if not sections:
            continue

        for section_name, section_text in sections:
            # IMPORTANT:
            # Avoid creating header-only chunks. We store the FDA section text as the document body
            # and keep drug/section identifiers in metadata. The retriever will format the context.
            page = section_text
            metadata = {
                "drug_name": drug_name,
                "drug_name_norm": drug_name_norm,
                "section": section_name,
                "aliases": aliases_str,
            }
            documents.append(Document(page_content=page, metadata=metadata))
    
    return documents


def load_and_chunk_data(
    limit_files: Optional[int] = None,
    max_entries_total: Optional[int] = None,
    max_entries_per_file: Optional[int] = None,
    per_file_selection: str = "top",
    random_seed: Optional[int] = 42,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    max_chunks_total: Optional[int] = None,
    include_drugs: Optional[List[str]] = None,
) -> List[Document]:
    """
    Loads JSON files, extracts drug information, and chunks the documents.
    """
    json_files = glob.glob(os.path.join(DATA_DIR, "**/*.json"), recursive=True)
    # Filter out directories that happen to end with ".json"
    json_files = sorted([p for p in json_files if os.path.isfile(p)])

    # If the user requested a limited test run, only process the first N files.
    # Note: `--limit-partitions` historically only affected downloading; we also
    # use it to limit ingestion so test runs don't accidentally embed the full dataset.
    if limit_files is not None:
        json_files = json_files[: max(0, int(limit_files))]
        print(f"Limiting ingestion to first {len(json_files)} JSON file(s) for testing...")
    
    if not json_files:
        print(f"No JSON files found in {DATA_DIR}")
        return []
    
    all_documents = []
    entries_seen = 0
    include_norms = {normalize_drug_name(x) for x in (include_drugs or []) if normalize_drug_name(x)}
    found_targets: set[str] = set()
    
    # Text splitter configuration
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    print(f"Processing {len(json_files)} JSON file(s)...")
    
    for file_path in json_files:
        print(f"  Processing {os.path.basename(file_path)}...")
        per_file_seen = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results = data.get('results', [])
                
                if not results:
                    print(f"    No 'results' found in {file_path}")
                    continue
                
                # If we cap per-file entries, choose *better* entries per file to maximize demo quality.
                # "top" (default): keep the most informative entries (warnings/contraindications/dosage + longer text)
                # "first": take the first K matching entries
                # "random": reservoir sample K matching entries
                extracted_items = []
                k = max_entries_per_file if max_entries_per_file is not None else None
                heap: list[tuple[float, int, dict]] = []  # (score, tie, info)
                tie = 0

                def score_info(info: dict) -> float:
                    score = 0.0
                    if info.get("warnings"):
                        score += 5.0
                    if info.get("warnings_and_precautions"):
                        score += 5.0
                    if info.get("contraindications"):
                        score += 4.0
                    if info.get("boxed_warning"):
                        score += 6.0
                    if info.get("dosage"):
                        score += 2.0
                    if info.get("overdosage"):
                        score += 4.0
                    if info.get("pregnancy") or info.get("lactation"):
                        score += 3.0
                    txt = info.get("text_content") or ""
                    score += min(3.0, len(txt) / 2000.0)
                    return score

                for entry in results:
                    if max_entries_total is not None and entries_seen >= max_entries_total:
                        break
                    info = extract_drug_info(entry)
                    if info:
                        # If an include list is provided, only keep matching entries.
                        if include_norms:
                            aliases = info.get("aliases", [])
                            alias_norms = [normalize_drug_name(a) for a in aliases if isinstance(a, str)]
                            # match if any include appears in any alias (exact or substring)
                            matched = False
                            for inc in include_norms:
                                for an in alias_norms:
                                    # word-boundary-ish match to avoid overly broad substring matches
                                    if an == inc or f" {inc} " in f" {an} ":
                                        matched = True
                                        found_targets.add(inc)
                                        break
                                if matched:
                                    break
                            if not matched:
                                continue

                        if k is None:
                            extracted_items.append(info)
                            entries_seen += 1
                            per_file_seen += 1
                        else:
                            tie += 1
                            if per_file_selection == "first":
                                if per_file_seen < k:
                                    extracted_items.append(info)
                                    entries_seen += 1
                                    per_file_seen += 1
                            elif per_file_selection == "random":
                                if random_seed is not None:
                                    random.seed(random_seed)
                                if per_file_seen < k:
                                    extracted_items.append(info)
                                    entries_seen += 1
                                    per_file_seen += 1
                                else:
                                    j = random.randint(0, tie - 1)
                                    if j < k:
                                        extracted_items[j] = info
                            else:
                                s = score_info(info)
                                if len(heap) < k:
                                    heapq.heappush(heap, (s, tie, info))
                                else:
                                    if s > heap[0][0]:
                                        heapq.heapreplace(heap, (s, tie, info))

                if k is not None and per_file_selection == "top":
                    extracted_items = [t[2] for t in sorted(heap, key=lambda x: (-x[0], x[1]))]
                    entries_seen += len(extracted_items)
                    per_file_seen = len(extracted_items)
                
                if extracted_items:
                    docs = create_documents(extracted_items)
                    all_documents.extend(docs)
                    print(f"    Extracted {len(extracted_items)} drug entries, created {len(docs)} documents")
                
                if max_entries_total is not None and entries_seen >= max_entries_total:
                    print(f"Reached max entries limit ({max_entries_total}). Stopping ingestion early.")
                    break

                if max_entries_per_file is not None and per_file_seen >= max_entries_per_file:
                    print(f"    Reached per-file entry limit ({max_entries_per_file}). Moving to next file...")

                if include_norms and found_targets == include_norms:
                    print("Found all requested demo drugs. Stopping early.")
                    break
                
        except json.JSONDecodeError as e:
            print(f"    Error parsing JSON in {file_path}: {e}")
        except Exception as e:
            print(f"    Error loading {file_path}: {e}")
    
    if not all_documents:
        print("No documents created from the data files.")
        return []
    
    print(f"\nTotal documents before chunking: {len(all_documents)}")
    print(f"Chunking with size={chunk_size}, overlap={chunk_overlap}...")
    
    # Chunk the documents
    chunked_docs = splitter.split_documents(all_documents)

    if max_chunks_total is not None and len(chunked_docs) > max_chunks_total:
        chunked_docs = chunked_docs[: max(0, int(max_chunks_total))]
        print(f"Limiting to first {len(chunked_docs)} chunks for demo run...")
    
    print(f"Total chunks after splitting: {len(chunked_docs)}")
    
    return chunked_docs


def ingest_to_chromadb(
    documents: List[Document],
    embedding_function,
    clear_existing: bool = False,
    batch_size: int = 100,
    max_retries: int = 3,
    retry_wait_seconds: float = 2.0,
):
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
    # Smaller batches reduce rate-limit / timeout risks for embedding APIs.
    total_docs = len(documents)
    total_batches = max(1, math.ceil(total_docs / max(1, batch_size)))
    
    print(f"\nIngesting {total_docs} chunks to ChromaDB...")
    print("This may take a while depending on the number of documents and API rate limits...")
    start_all = time.time()
    
    for batch_idx, i in enumerate(range(0, total_docs, batch_size), start=1):
        batch = documents[i:i + batch_size]
        batch_start = time.time()
        print(f"  [{batch_idx}/{total_batches}] Embedding + storing {len(batch)} chunks...", flush=True)

        success = False
        for attempt in range(1, max_retries + 1):
            try:
                vectorstore.add_documents(batch)
                success = True
                break
            except Exception as e:
                wait = retry_wait_seconds * (2 ** (attempt - 1))
                print(
                    f"    Error on batch {batch_idx} attempt {attempt}/{max_retries}: {e}. "
                    f"Retrying in {wait:.1f}s...",
                    flush=True,
                )
                time.sleep(wait)

        if success:
            done = min(i + batch_size, total_docs)
            elapsed_batch = time.time() - batch_start
            elapsed_all = max(0.001, time.time() - start_all)
            rate = done / elapsed_all
            print(
                f"    Ingested {done}/{total_docs} chunks "
                f"(batch {batch_idx} took {elapsed_batch:.1f}s, avg {rate:.2f} chunks/s)",
                flush=True,
            )
        else:
            print(f"    Giving up on batch {batch_idx} after {max_retries} retries. Skipping...", flush=True)
    
    # Persist the collection (older LangChain Chroma wrappers exposed .persist()).
    # Newer versions persist automatically for persistent clients, so this may not exist.
    if hasattr(vectorstore, "persist"):
        try:
            vectorstore.persist()
        except Exception as e:
            print(f"Warning: failed to call vectorstore.persist(): {e}. Continuing...", flush=True)
    
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
        help="Limit the number of data partitions to download AND the number of local JSON files to ingest (for testing)"
    )
    parser.add_argument(
        "--include-drugs",
        type=str,
        default=None,
        help="Comma-separated list of drug names to ingest (demo mode). Example: \"aspirin,ibuprofen,acetaminophen\""
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Maximum number of drug entries to process total (recommended for a 5-minute demo)"
    )
    parser.add_argument(
        "--max-entries-per-file",
        type=int,
        default=None,
        help="Maximum number of drug entries to process per JSON file (recommended to spread ingestion across many partitions without taking too long)"
    )
    parser.add_argument(
        "--per-file-selection",
        type=str,
        default="top",
        choices=["top", "first", "random"],
        help="How to pick entries within each file when --max-entries-per-file is set. 'top' prefers richer label sections (best quality)."
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed used when --per-file-selection random is chosen."
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Maximum number of chunks to embed/store total (recommended for a 5-minute demo)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help="Chunk size used for splitting label text (larger = fewer chunks)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=CHUNK_OVERLAP,
        help="Chunk overlap used for splitting label text"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding + storage (smaller is safer for rate limits)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per batch on transient API/network errors"
    )
    parser.add_argument(
        "--retry-wait-seconds",
        type=float,
        default=2.0,
        help="Initial wait before retrying a failed batch (uses exponential backoff)"
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
    include_list = None
    if args.include_drugs:
        include_list = [x.strip() for x in args.include_drugs.split(",") if x.strip()]
    documents = load_and_chunk_data(
        limit_files=args.limit_partitions,
        max_entries_total=args.max_entries,
        max_entries_per_file=args.max_entries_per_file,
        per_file_selection=args.per_file_selection,
        random_seed=args.random_seed,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        max_chunks_total=args.max_chunks,
        include_drugs=include_list,
    )
    
    if not documents:
        print("No documents to process. Exiting.")
        sys.exit(1)
    print()
    
    # Step 3: Generate embeddings and store in ChromaDB
    print("Step 3: Generating embeddings and storing in ChromaDB...")
    print("-" * 60)
    ingest_to_chromadb(
        documents,
        embedding_function,
        clear_existing=args.clear_existing,
        batch_size=args.batch_size,
        max_retries=args.max_retries,
        retry_wait_seconds=args.retry_wait_seconds,
    )
    
    print()
    print("=" * 60)
    print("Ingestion process completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

