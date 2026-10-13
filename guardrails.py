import os
import re
from langchain_core.documents import Document

# Starter threshold for FAISS squared-L2 distance; calibrate with real test questions.
MAX_FAISS_DISTANCE = float(os.getenv("MAX_FAISS_DISTANCE", "1.35"))

def valid_input(question):
    q = (question or "").strip()
    if not q:
        return False, "Please enter your agriculture-related question."
    if len(q) > 1000:
        return False, "Please keep your question under 1,000 characters."
    if len(re.sub(r"\\W", "", q, flags=re.UNICODE)) < 2:
        return False, "Please enter a little more detail."
    return True, ""

def has_sufficient_evidence(docs: list[Document], best_distance):
    return bool(docs) and best_distance is not None and best_distance <= MAX_FAISS_DISTANCE

def citations_valid(answer, docs):
    ids = re.findall(r"\[Source\s+(\d+)\]", answer, flags=re.I)
    valid = {str(i) for i in range(1, len(docs) + 1)}
    return bool(ids) and all(i in valid for i in ids)

def citation_ids(answer):
    return [int(i) for i in re.findall(r"\[Source\s+(\d+)\]", answer or "", flags=re.I)]

def strip_invalid_citations(answer, docs):
    valid = {str(i) for i in range(1, len(docs) + 1)}
    return re.sub(r"\[Source\s+(\d+)\]", lambda m: m.group(0) if m.group(1) in valid else "", answer or "", flags=re.I).strip()
