from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.chains import (
    get_qa_chain,
    get_validation_chain,
    get_schedule_chain,
    get_label_context,
    compute_risk_level_from_label_text,
)
from app.rag import get_vector_store

app = FastAPI(title="MedGuard", description="Label-safe Medication Reminder Chatbot")

class ChatRequest(BaseModel):
    drug_name: str # Added drug_name as it's required for our specific retrieval
    query: str

class ValidationRequest(BaseModel):
    drug_name: str
    dosage: str

class ScheduleRequest(BaseModel):
    drug_name: str
    start_time: str

@app.get("/")
async def root():
    return {"message": "MedGuard API is running. Access docs at /docs"}

@app.get("/debug/chroma")
async def debug_chroma(sample: int = 25, scan: int = 2000):
    """
    Debug endpoint: shows what's inside the Chroma collection so you can pick valid drug_name values.

    Notes:
    - Each drug can generate many chunks, so the "first N" records often all belong to the same drug.
    - This endpoint scans up to `scan` records (paged) to collect up to `sample` unique drug names.
    """
    try:
        vs = get_vector_store()
        col = vs._collection
        total = int(col.count())

        target_unique = max(0, min(int(sample), 100))
        scan_limit = max(0, min(int(scan), 20000))
        if target_unique == 0:
            return {"count": total, "scan": scan_limit, "sample_drugs": []}

        drugs: list[str] = []
        seen: set[str] = set()

        offset = 0
        page_size = 500
        scanned = 0
        while scanned < scan_limit and len(drugs) < target_unique and offset < total:
            page = min(page_size, scan_limit - scanned)
            res = col.get(limit=page, offset=offset, include=["metadatas"])
            metas = res.get("metadatas", []) or []
            for m in metas:
                if not isinstance(m, dict):
                    continue
                dn = m.get("drug_name")
                if isinstance(dn, str) and dn and dn not in seen:
                    seen.add(dn)
                    drugs.append(dn)
                    if len(drugs) >= target_unique:
                        break
            offset += page
            scanned += page

        return {"count": total, "scan": scanned, "sample_drugs": drugs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/search_drug")
async def debug_search_drug(name: str, k: int = 12):
    """
    Debug endpoint: search the vector store and return the drug names that appear in the top results.
    Useful when you want to test a drug (e.g. "aspirin") and confirm if it's present.
    """
    try:
        kk = max(1, min(int(k), 50))
        vs = get_vector_store()
        docs = vs.similarity_search(name, k=kk)
        out = []
        seen = set()
        for d in docs:
            dn = (d.metadata or {}).get("drug_name")
            if isinstance(dn, str) and dn and dn not in seen:
                seen.add(dn)
                out.append(dn)
        return {"query": name, "k": kk, "matches": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    """
    answers questions about a specific drug based on its FDA label.
    """
    chain = get_qa_chain()
    try:
        response = chain.invoke({"drug_name": request.drug_name, "question": request.query})

        # If model says "not found", return the required error JSON as-is.
        if isinstance(response, dict) and response.get("error") == "Information not found in FDA label":
            return response

        # Deterministically override risk_level based on FDA label text.
        label_context = get_label_context(request.drug_name, request.query)
        risk = compute_risk_level_from_label_text(label_context)

        if isinstance(response, dict):
            response["risk_level"] = risk
            # Ensure drug echoes the requested drug name (schema requirement)
            response["drug"] = request.drug_name
            return response

        # Fallback: if parser didn't return dict, return a safe error.
        return {"error": "Information not found in FDA label"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate")
async def validate_dosage(request: ValidationRequest):
    """
    Validates if a dosage is safe according to the FDA label.
    """
    chain = get_validation_chain()
    try:
        result = chain.invoke({"drug_name": request.drug_name, "dosage": request.dosage})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule")
async def generate_schedule(request: ScheduleRequest):
    """
    Generates a generic reminder schedule based on FDA frequency recommendations.
    """
    chain = get_schedule_chain()
    try:
        result = chain.invoke({"drug_name": request.drug_name, "start_time": request.start_time})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
