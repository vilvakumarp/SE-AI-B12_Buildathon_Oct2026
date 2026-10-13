# Uzhavar Nanban | உழவர் நண்பன்

A one-day contest MVP: Streamlit + LangChain + OpenAI embeddings + FAISS for agricultural scheme Q&A.

## Runtime boundary
The farmer-facing chat does not use web search. It retrieves only from the locally saved FAISS index. Source acquisition happens separately.

## Windows setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and add your OpenAI API key.

## Add your existing JSON
Copy the JSON produced by your extractor to:
`data/raw/agrisnet_schemes.json`

Optional: add PDFs under `data/raw/`, or save the locally acquired MNRE webpage content as `data/raw/scheme_mnre_pm_kusum.txt`.

## Build FAISS
```powershell
python build_knowledge_base.py
```

## Run the app
```powershell
streamlit run app.py
```

## Notes
- The builder reads the Agrisnet JSON produced by your extraction script and preserves scheme/department/source metadata.
- Records may be incomplete or historical. This prototype does not independently establish current scheme validity.
- The starter FAISS distance threshold in `guardrails.py` must be calibrated with test questions. FAISS distances are not probabilities.
- Citation-marker validation checks that citation IDs correspond to supplied evidence; it does not prove every claim is entailed. Source passages are shown for review.
- Do not commit `.env` or API keys.
- Test pumpset, machinery, eligibility, documents-required, and unrelated questions before the contest.
