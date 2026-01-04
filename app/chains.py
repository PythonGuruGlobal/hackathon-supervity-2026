from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from app.rag import get_vector_store
from operator import itemgetter
import os
import re

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=False)
except Exception:
    pass


def _norm(s: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in (s or "")).split())

# Risk classification rules (deterministic, based on FDA label text).
_WS_RE = re.compile(r"\s+")


def _norm_text(s: str) -> str:
    return _WS_RE.sub(" ", (s or "").lower()).strip()


def compute_risk_level_from_label_text(label_text: str) -> str:
    """
    Rules:
    - HIGH if label mentions bleeding, allergy, pregnancy risk, organ damage, or overdose
    - MEDIUM if mentions mild side effects
    - else LOW
    """
    t = _norm_text(label_text)

    high_terms = [
        # bleeding
        "bleeding",
        "bleed",
        "hemorrhage",
        "haemorrhage",
        # allergy
        "allergy",
        "allergic",
        "hypersensitivity",
        "anaphylaxis",
        # pregnancy risk
        "pregnancy",
        "pregnant",
        "fetal",
        "foetal",
        "teratogenic",
        # organ damage
        "organ damage",
        "liver damage",
        "hepatic injury",
        "hepatotoxic",
        "hepatic failure",
        "kidney damage",
        "renal injury",
        "renal failure",
        # overdose
        "overdose",
        "toxicity",
        "poisoning",
    ]
    if any(term in t for term in high_terms):
        return "HIGH"

    # MEDIUM: mentions mild side effects (keep close to the requirement wording)
    medium_signals = [
        "mild side effect",
        "mild side effects",
        "mild adverse reaction",
        "mild adverse reactions",
    ]
    if any(sig in t for sig in medium_signals):
        return "MEDIUM"

    return "LOW"
# Initialize LLM - using OpenAI only
def get_llm():
    """Get the LLM instance. Uses OpenAI gpt-4o-mini."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Prompts
QA_SYSTEM_PROMPT = (
    "You must only answer using the FDA drug label text provided to you. "
    "Do not use any external medical knowledge. "
    "If the answer is not found in the FDA label text, return this JSON exactly: "
    "{{\"error\":\"Information not found in FDA label\"}}. "
    "Otherwise, return a single-line valid JSON object and NOTHING else. "
    "Do NOT return markdown. Do NOT use bullet symbols. Do NOT include newline characters. "
    "Do NOT include explanations outside JSON."
)

QA_USER_PROMPT = (
    "Drug: {drug}\n"
    "Question: {question}\n"
    "FDA Label Context: {context}\n\n"
    "Required JSON format when answer IS found:\n"
    "{{\"drug\":\"<drug name>\",\"section\":\"<FDA section such as Warnings, Dosage, Contraindications>\","
    "\"key_points\":[\"point 1\",\"point 2\",\"point 3\"],\"risk_level\":\"LOW | MEDIUM | HIGH\"}}\n\n"
    "Rules when answer IS found:\n"
    "- drug MUST equal the provided Drug value exactly\n"
    "- section must be one best matching FDA section from the context (e.g., Warnings, Dosage and Administration, Contraindications)\n"
    "- key_points must be 1-3 short points derived from the context (no bullets, no newlines)\n"
    "- risk_level must be LOW, MEDIUM, or HIGH\n"
    "Return JSON only."
)

VALIDATION_PROMPT = """
Check if the following dosage is safe for the given drug based on the FDA label.
Context:
{context}

Drug: {drug}
Dosage: {dosage}

Return a JSON with "safe": boolean and "reason": string.
"""

SCHEDULE_PROMPT = """
You are a smart scheduler. Your goal is to create a medication reminder schedule list based on the dosage instructions found in the FDA context.

Context:
{context}

Drug: {drug}
Start Time: {start_time} (ISO format or HH:MM)

Instructions:
1. Analyze the context to find the standard frequency for the drug (e.g., "once daily", "every 6 hours", "twice a day").
2. Calculate the specific times for reminders starting from the provided Start Time for the next 24 hours.
3. Return ONLY a JSON object with a key "schedule" containing a list of strings (times).

Example Output:
{{
  "frequency_found": "every 6 hours",
  "schedule": ["08:00", "14:00", "20:00", "02:00"]
}}

If frequency is not found, return empty list.
"""

def retrieve_with_filter(inputs):
    """
    Custom retrieval function to apply metadata filtering for drug name.
    """
    drug_name = inputs.get("drug_name")
    query = inputs.get("question")
    
    vectorstore = get_vector_store()
    
    # search_kwargs filter
    # Note: This assumes drug_name matches exact metadata key "drug_name" in Chroma
    # We add a fallback to empty dict if null content for robustness
    docs = []
    if drug_name:
        # Prefer normalized matching (new ingestion stores drug_name_norm).
        dn = _norm(drug_name)
        try:
            docs = vectorstore.similarity_search(query, k=4, filter={"drug_name_norm": dn})
        except Exception:
            docs = []
        # Back-compat: older collections only have "drug_name"
        if not docs:
            docs = vectorstore.similarity_search(query, k=4, filter={"drug_name": drug_name})
        # Last resort: search without filter then post-filter by parsing the "Drug Name:" prefix.
        if not docs:
            candidates = vectorstore.similarity_search(query, k=12)
            dn_norm = dn
            filtered = []
            for d in candidates:
                text = (d.page_content or "")
                first = text.splitlines()[0] if text else ""
                if first.lower().startswith("drug name:"):
                    name = first.split(":", 1)[1].strip()
                    if _norm(name) == dn_norm or (dn_norm and dn_norm in _norm(name)):
                        filtered.append(d)
            docs = filtered[:4]
    else:
        # If no drug name is provided, search across all.
        docs = vectorstore.similarity_search(query, k=4)
        
    if not docs:
        return "No relevant FDA label data found."

    # Format context using metadata so the LLM sees FDA text + which section it came from.
    parts = []
    for d in docs:
        section = (d.metadata or {}).get("section") or "Unknown"
        text = (d.page_content or "").strip()
        if not text:
            continue
        parts.append(f"Section: {section}\n{text}")
    return "\n\n".join(parts) if parts else "No relevant FDA label data found."


def get_label_context(drug_name: str, question: str) -> str:
    """Convenience wrapper to fetch the same context string used for /ask."""
    return retrieve_with_filter({"drug_name": drug_name, "question": question})

def get_retrieval_chain():
    """
    Returns a runnable that takes a dictionary {drug_name, question} and returns the context string.
    """
    return RunnableLambda(retrieve_with_filter)

def get_qa_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QA_SYSTEM_PROMPT),
            ("human", QA_USER_PROMPT),
        ]
    )
    llm = get_llm()
    
    # The chain expects input: {"drug_name": "...", "question": "..."}
    chain = (
        {
            "context": get_retrieval_chain(),
            "drug": itemgetter("drug_name"),
            "question": itemgetter("question"),
        }
        | prompt
        | llm
        | JsonOutputParser()
    )
    return chain

def get_validation_chain():
    prompt = PromptTemplate.from_template(VALIDATION_PROMPT)
    llm = get_llm()
    
    # We need to construct a "question" for the retriever to find dosage info
    def prepare_retrieval_input(inputs):
        return {
            "drug_name": inputs["drug_name"],
            "question": "dosage and administration maximum daily dose precautions" 
        }

    chain = (
        {
            "context": prepare_retrieval_input | get_retrieval_chain(), 
            "drug": itemgetter("drug_name"),
            "dosage": itemgetter("dosage")
        }
        | prompt
        | llm
        | JsonOutputParser()
    )
    return chain

def get_schedule_chain():
    prompt = PromptTemplate.from_template(SCHEDULE_PROMPT)
    llm = get_llm()
    
    def prepare_retrieval_input(inputs):
        return {
            "drug_name": inputs["drug_name"],
            "question": "dosage and administration frequency schedule" 
        }

    chain = (
        {
            "context": prepare_retrieval_input | get_retrieval_chain(), 
            "drug": itemgetter("drug_name"),
            "start_time": itemgetter("start_time")
        }
        | prompt
        | llm
        | JsonOutputParser()
    )
    return chain
