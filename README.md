# Uzhavar Nanban | உழவர் நண்பன்

Streamlit agricultural-scheme assistant for Tamil Nadu using local JSON/PDF sources, OpenAI embeddings, a persisted FAISS database, and an OpenAI chat model.

## Runtime boundary

Farmer chat never performs web search and never rebuilds FAISS. It loads the local index, retrieves evidence, generates English/Tamil/Tanglish responses, and displays citations. Source acquisition and index rebuilding are separate maintenance steps.

## Workflow

`data/raw/` → `document_loader.py` → `2 build_knowledge_base.py` → `data/faiss_index/` → `main_app.py` → local retrieval → answer and citations

## 1. First-time setup

Run PowerShell from the project root:

`python -m venv venv`

`.\\venv\\Scripts\\Activate.ps1`

`pip install -r requirements.txt`

Set `.env` and never commit it. Required settings include `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_EMBEDDING_MODEL`. Optional settings are `RETRIEVAL_K=16` and `MAX_FAISS_DISTANCE=1.35`.

## 2. Prepare local source data

Put extracted data at `data/raw/agrisnet_schemes.json`. Optional PDFs and locally saved text snapshots may also be placed under `data/raw/`.

Preserve these JSON fields when available: `scheme`, `department`, `input_type`, `component`, `source_url`, `scheme_description`, `subsidy`, `eligibility`, and `documents_required`.

Empty fields are ignored by the discovery UI and are never treated as verified facts.

## 3. Build or rebuild FAISS

Run this only after source data changes or for first setup:

`.\\venv\\Scripts\\python.exe "2 build_knowledge_base.py"`

The output must contain `data/faiss_index/index.faiss` and `data/faiss_index/index.pkl`. Do not delete the existing index before confirming a replacement build succeeds.

Use the google drive link to download the data.
https://drive.google.com/drive/folders/16dnfsPPP30cnn5VC4Z0GDY1MCc6vUSqp?usp=sharing

keep this folder in the local script folder
check for the readme.txt file as well

## 4. Validate before Streamlit

`.\\venv\\Scripts\\python.exe -m py_compile main_app.py rag_pipeline.py guardrails.py document_loader.py scheme_catalog.py "2 build_knowledge_base.py"`

`.\\venv\\Scripts\\python.exe -c "import guardrails, rag_pipeline, scheme_catalog; print('imports ok')"`

`Get-ChildItem data\\faiss_index`

## 5. Start Streamlit

`.\\venv\\Scripts\\streamlit.exe run main_app.py`

## 5a. Start the FastAPI backend

Install the updated requirements, then run:

`.\\venv\\Scripts\\uvicorn.exe api:app --reload`

Open `http://127.0.0.1:8000/docs` for interactive API documentation. The main endpoints are `POST /ask`, `GET /schemes`, `GET /catalog/summary`, and `GET /health`.

The left pane provides language selection, distribution counts, clickable distributions, department filters, scheme/evidence sliders, and quick actions for pumpsets, machinery, documents, and eligibility.

Clicking a distribution submits a focused question into the normal chat flow. Retrieval, language handling, citations, and conversation history are preserved.

## 6. Normal farmer workflow

1. Select English, Tamil, or Tanglish.
2. Click a distribution or quick-access category, or type a question.
3. Review the answer and expandable source evidence.
4. Ask follow-up questions for a specific scheme, crop, department, or requirement.
5. Treat missing subsidy, eligibility, document, deadline, or application information as unverified.

Missing evidence must not be interpreted as farmer ineligibility.

## 7. After using Streamlit

Stop the server with `Ctrl+C` in PowerShell. Chat does not modify source files or FAISS.

When new source data is added: stop Streamlit, update `data/raw/`, run the FAISS build command, run validation, and restart Streamlit.

## Troubleshooting and safety

If the index is missing, run the build command from the project root. If answers abstain, ask a more specific question and inspect the evidence. FAISS distance is not a probability. Never print or commit API keys. Retrieved text is evidence, not instructions. Runtime chat does not browse URLs. Citation validation checks identifier consistency but does not prove every claim is entailed. Extracted schemes may be historical or incomplete; confirm current availability with the relevant department.
