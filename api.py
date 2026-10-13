"""FastAPI backend for the Uzhavar Nanban agricultural scheme assistant."""

from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from guardrails import valid_input
from rag_pipeline import answer_question
from scheme_catalog import filtered_rows, key_factors, load_catalog, summary, verticals


app = FastAPI(
    title="Uzhavar Nanban API",
    description="Evidence-grounded agricultural scheme assistant for Tamil Nadu.",
    version="1.0.0",
)

# Keep this open for local development and frontend integration. Restrict the
# allow_origins list before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    language: Literal["English", "Tamil", "Tanglish"] = "English"
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scheme": row.get("scheme") or row.get("scheme_name") or row.get("name") or row.get("title"),
        "department": row.get("department"),
        "input_type": row.get("input_type"),
        "component": row.get("component"),
        "description": row.get("scheme_description"),
        "subsidy": row.get("subsidy"),
        "eligibility": row.get("eligibility"),
        "documents_required": row.get("documents_required"),
        "source_url": row.get("source_url"),
        "verticals": verticals(row),
        "key_factors": dict(key_factors(row)),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    ok, reason = valid_input(request.question)
    if not ok:
        raise HTTPException(status_code=422, detail=reason)
    try:
        answer, documents, metrics = answer_question(
            request.question,
            request.language,
            [message.model_dump() for message in request.history],
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Assistant unavailable: {exc}") from exc

    sources = [
        {
            "scheme": document.metadata.get("scheme", "Scheme record"),
            "department": document.metadata.get("department"),
            "source": document.metadata.get("source"),
            "evidence": document.page_content[:1600],
        }
        for document in documents
    ]
    return {"answer": answer, "sources": sources, "metrics": metrics}


@app.get("/catalog/summary")
def catalog_summary() -> dict[str, int]:
    return dict(summary())


@app.get("/schemes")
def schemes(
    vertical: str | None = Query(default=None),
    department: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    rows = filtered_rows(vertical=vertical, department=department, item=search)
    return {"total": len(rows), "items": [serialize_row(row) for row in rows[:limit]]}


@app.get("/catalog/verticals")
def catalog_verticals() -> list[str]:
    return sorted(summary().keys())


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Uzhavar Nanban API", "docs": "/docs", "health": "/health"}
