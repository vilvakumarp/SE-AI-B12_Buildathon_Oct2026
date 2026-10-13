"""Small, local catalogue view over the extracted JSON (no web access)."""
import json
from pathlib import Path
from collections import Counter
import re

RAW_PATH = Path("data/raw/agrisnet_schemes.json")

VERTICAL_RULES = {
    "Agriculture": ("agriculture", "crop", "paddy", "pulse", "seed", "farmers"),
    "Horticulture": ("horticulture", "fruit", "vegetable", "nursery", "plantation", "protected cultivation"),
    "Agricultural Engineering": ("engineering", "machinery", "mechanisation", "mechanization", "pump", "irrigation"),
    "Seeds & planting material": ("seed", "planting material", "seedling", "nursery"),
    "Livestock / cattle": ("cattle", "livestock", "dairy", "goat", "sheep", "poultry", "animal", "fodder"),
    "Agricultural education / TNAU": ("university", "college", "training", "skill development", "awareness"),
    "Water / watershed": ("watershed", "micro irrigation", "irrigation", "water", "drip", "sprinkler"),
    "Marketing / agri-business": ("marketing", "agri business", "value addition", "post harvest", "storage"),
}

def load_catalog():
    if not RAW_PATH.exists(): return []
    payload = json.loads(RAW_PATH.read_text(encoding="utf-8-sig"))
    rows = payload if isinstance(payload, list) else payload.get("data", payload.get("records", []))
    # Ignore empty/incomplete JSON records in the discovery UI. They remain
    # untouched in the raw source and can still be rebuilt into the index if
    # the ingestion process later enriches them.
    useful = ("scheme", "scheme_name", "name", "title", "department", "input_type", "component", "scheme_description", "subsidy", "eligibility", "documents_required")
    return [r for r in rows if isinstance(r, dict) and any(str(r.get(k) or "").strip() for k in useful)]

def _haystack(row):
    # page_text contains the whole portal's dropdown vocabulary, so using it
    # would incorrectly classify every record into every vertical.
    return " ".join(str(row.get(k) or "") for k in ("department", "input_type", "component", "scheme", "scheme_description", "subsidy", "eligibility", "documents_required")).lower()

def verticals(row):
    text = _haystack(row); found = []
    for name, terms in VERTICAL_RULES.items():
        if any(term in text for term in terms): found.append(name)
    return found or ["Other agricultural support"]

def summary(rows=None):
    rows = rows if rows is not None else load_catalog(); counts = Counter(v for r in rows for v in verticals(r))
    return counts

def filtered_rows(vertical=None, department=None, item=None):
    rows = load_catalog(); out=[]
    for row in rows:
        if vertical and vertical not in verticals(row): continue
        if department and str(row.get("department") or "") != department: continue
        if item and item.lower() not in _haystack(row): continue
        out.append(row)
    return out

def key_factors(row):
    text = _haystack(row)
    factors = []
    labels = (("Department", row.get("department")), ("Support area", row.get("input_type")), ("Crop / component", row.get("component")))
    for label, value in labels:
        if value: factors.append((label, str(value)))
    if any(x in text for x in ("subsidy", "assistance", "support", "distribution")): factors.append(("Benefit", "Assistance or distribution is mentioned in the indexed record"))
    if any(x in text for x in ("farmer", "farm women", "small", "marginal", "sc", "st", "women")): factors.append(("Beneficiary signal", "Farmer / farmer group / category eligibility may apply; verify the exact condition in the source"))
    if any(x in text for x in ("training", "awareness", "skill")): factors.append(("Delivery mode", "Training, awareness, or skill development"))
    factors.append(("Evidence status", "Eligibility, subsidy, and document fields are not separately populated in this JSON; do not assume them unless the evidence text states them."))
    return factors

def subsidy_evidence_rows(rows, limit=3):
    """Rank only explicit subsidy/assistance evidence; never infer a highest amount."""
    scored = []
    for row in rows:
        text = " ".join(str(row.get(k) or "") for k in ("scheme", "input_type", "component", "subsidy", "scheme_description", "eligibility", "documents_required"))
        hits = len(re.findall(r"subsidy|assistance|support|grant|financial|rs\.?\s?[\d,]+|\d+\s?%", text, re.I))
        if hits:
            scored.append((hits, row))
    return [row for _, row in sorted(scored, key=lambda x: x[0], reverse=True)[:limit]]
