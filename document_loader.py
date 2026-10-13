import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

RAW_DIR = Path("data/raw")
JSON_PATH = RAW_DIR / "agrisnet_schemes.json"

def _val(record, *keys):
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def load_documents():
    docs = []
    if JSON_PATH.exists():
        payload = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", []))
        if not isinstance(payload, list):
            raise ValueError("Expected a JSON array of Agrisnet records.")
        for i, row in enumerate(payload, start=1):
            if not isinstance(row, dict):
                continue
            fields = [
                ("Scheme", _val(row, "scheme", "scheme_name", "name", "title")),
                ("Department", _val(row, "department")),
                ("Input type", _val(row, "input_type")),
                ("Component", _val(row, "component")),
                ("Scheme description", _val(row, "scheme_description", "description")),
                ("Subsidy", _val(row, "subsidy")),
                ("Eligibility", _val(row, "eligibility")),
                ("Documents required", _val(row, "documents_required", "documents")),
                ("Extracted page text", _val(row, "page_text")),
            ]
            text = "\n\n".join(f"{k}: {v}" for k, v in fields if v)
            if len(text) < 30:
                continue
            docs.append(Document(page_content=text, metadata={
                "source": _val(row, "source_url") or str(JSON_PATH),
                "record_id": str(row.get("record_id", i)),
                "scheme": _val(row, "scheme", "scheme_name", "name", "title") or "Scheme name not captured",
                "department": _val(row, "department") or "Not specified",
                "input_type": _val(row, "input_type"),
                "component": _val(row, "component"),
                "extracted_at": _val(row, "extracted_at"),
                "source_type": "Agrisnet extracted record",
            }))
    else:
        print(f"JSON not found: {JSON_PATH}")

    mnre = RAW_DIR / "scheme_mnre_pm_kusum.txt"
    if mnre.exists():
        for doc in TextLoader(str(mnre), encoding="utf-8").load():
            doc.metadata.update({
                "source": "https://mnre.gov.in/en/pradhan-mantri-kisan-urja-suraksha-evam-utthaan-mahabhiyaan-pm-kusum/",
                "scheme": "PM-KUSUM",
                "department": "Ministry of New and Renewable Energy",
                "source_type": "Official webpage snapshot",
            })
            docs.append(doc)

    for pdf in RAW_DIR.rglob("*.pdf"):
        try:
            for doc in PyPDFLoader(str(pdf)).load():
                doc.metadata.update({"source": str(pdf), "source_type": "PDF"})
                doc.metadata["page_number"] = int(doc.metadata.get("page", 0)) + 1
                docs.append(doc)
        except Exception as exc:
            print(f"Warning: could not load {pdf.name}: {exc}")

    if not docs:
        raise ValueError("No sources found. Add data/raw/agrisnet_schemes.json or PDFs.")
    return docs

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150, add_start_index=True)
    return [d for d in splitter.split_documents(documents) if d.page_content.strip()]
