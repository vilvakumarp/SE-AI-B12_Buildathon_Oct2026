import streamlit as st
from dotenv import load_dotenv
from guardrails import valid_input
from rag_pipeline import answer_question
from scheme_catalog import summary, filtered_rows, key_factors, load_catalog, subsidy_evidence_rows

load_dotenv()
st.set_page_config(page_title="Uzhavar Nanban | உழவர் நண்பன்", page_icon="🌾", layout="wide")
st.markdown("""
<style>
.stApp {background:linear-gradient(180deg,#f2f8ed 0%,#fffdf6 55%,#f7faf2 100%);}
.block-container {max-width:1080px;padding-top:1.4rem;}
.hero {background:linear-gradient(120deg,#14532d,#328052);padding:1.45rem 1.7rem;border-radius:22px;color:white;margin-bottom:1rem;}
.hero h1 {color:white;margin:0;font-size:2rem;}
.hero p {color:#e7f5e8;margin:.45rem 0 0;}
div[data-testid="stChatMessage"] {border:1px solid #e1eadb;border-radius:16px;background:rgba(255,255,255,.85);}
div.stButton>button {border-radius:12px;border:1px solid #c9dec6;background:white;}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<div class="hero">
<h1>🌾 உழவர் நண்பன் | Uzhavar Nanban</h1>
<p>Your agricultural scheme assistant · விவசாயத் திட்டங்களை எளிதாக அறியுங்கள்</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🌱 Farmer help")
    language = st.selectbox("Language / மொழி", ["English", "தமிழ்", "Tanglish"])
    st.caption("Answers use the locally indexed documents only. No web search is used in chat.")
    st.divider()
    st.markdown("### Explore scheme verticals")
    catalog = load_catalog()
    vertical_counts = summary(catalog)
    st.markdown("**Indexed records by distribution**")
    for name, count in vertical_counts.most_common():
        st.progress(min(count / max(vertical_counts.values()), 1.0), text=f"{name}: {count}")
    st.markdown("**Ask about a distribution**")
    distribution_buttons = list(vertical_counts.keys())
    for start in range(0, len(distribution_buttons), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            index = start + offset
            if index >= len(distribution_buttons):
                break
            name = distribution_buttons[index]
            with col:
                if st.button(name, key=f"ask_distribution_{index}", use_container_width=True):
                    st.session_state.pending_question = (
                        f"What agricultural schemes and assistance are available under {name}? "
                        "Explain the key benefits, documented eligibility, application steps, and required documents."
                    )
    vertical = st.selectbox("Area / துறை", ["All areas"] + sorted(vertical_counts), key="catalog_vertical")
    department = st.selectbox("Department", ["All departments"] + sorted({str(r.get("department")) for r in catalog if r.get("department")}), key="catalog_department")
    max_cards = st.slider("Schemes to preview", 3, 20, 8, key="catalog_max_cards")
    detail_level = st.slider("Evidence detail", 1, 3, 2, help="Controls how much indexed text is shown in the catalogue preview.", key="catalog_detail")
    st.caption("These are discovery filters over the local JSON. Eligibility and benefits must be verified from cited evidence.")
    st.markdown("**Try asking**")
    suggestions = [
        ("Pumpset schemes", "What schemes are available for pumpsets?"),
        ("Farm machinery", "Is there assistance for farm machinery?"),
        ("Documents required", "What documents are required to apply?"),
        ("Eligibility", "Who is eligible for this scheme?"),
    ]
    for label, query in suggestions:
        if st.button(label, use_container_width=True):
            st.session_state.pending_question = query

st.subheader("How can we help your farm today?")
st.write("Ask about pumpsets, irrigation, farm machinery, eligibility, subsidies, or application documents.")
with st.expander("Browse indexed scheme areas", expanded=False):
    st.write("The raw JSON contains 1,766 records. Many records have department, input type and crop/component information, but the separate eligibility, subsidy and documents fields are currently empty. The assistant therefore treats those details as unverified unless present in the indexed text.")
    chosen_vertical = None if vertical == "All areas" else vertical
    chosen_department = None if department == "All departments" else department
    matching_rows = filtered_rows(chosen_vertical, chosen_department)
    preview = matching_rows[:max_cards]
    if chosen_vertical:
        st.markdown(f"### {vertical}")
        st.caption(f"{len(matching_rows)} indexed records match this distribution and department.")
        subsidy_rows = subsidy_evidence_rows(matching_rows)
        if subsidy_rows:
            st.markdown("**Top 3 records with explicit subsidy/assistance wording**")
            st.caption("This is an evidence ranking, not a highest-subsidy claim. Amounts are shown only when present in the local record.")
            for row in subsidy_rows:
                st.write(f"• {row.get('scheme') or 'Unnamed scheme'} — {row.get('subsidy') or row.get('input_type') or 'assistance wording found; amount not separately captured'}")
        else:
            st.info("No verified subsidy amount is available for this distribution in the raw JSON. Ask a specific scheme question to inspect its indexed evidence.")
    if not preview:
        st.info("No records match these filters.")
    for row in preview:
        with st.container(border=True):
            st.markdown(f"**{row.get('scheme') or 'Unnamed scheme'}**")
            st.caption(f"Verticals: {', '.join(__import__('scheme_catalog').verticals(row))}")
            for label, value in key_factors(row)[:detail_level + 2]:
                st.write(f"**{label}:** {value}")
            st.caption(f"Source: {row.get('source_url') or 'Local extracted record'}")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

def show_sources(sources):
    if sources:
        with st.expander("📚 View source evidence"):
            for i, doc in enumerate(sources, 1):
                md = doc.metadata
                st.markdown(f"**Source {i}: {md.get('scheme', 'Scheme record')}**")
                st.caption(f"Department: {md.get('department', 'Not specified')} · Source: {md.get('source', 'Not recorded')}")
                st.write(doc.page_content[:1600])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🌾" if msg["role"] == "assistant" else "👨‍🌾"):
        st.markdown(msg["content"])
        show_sources(msg.get("sources", []))
        if msg.get("metrics"):
            with st.expander("RAG diagnostics"):
                st.json(msg["metrics"])

question = st.chat_input("Ask your agriculture scheme question…")
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question:
    ok, reason = valid_input(question)
    if not ok:
        st.warning(reason)
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="👨‍🌾"):
            st.markdown(question)
        history = st.session_state.messages[:-1]
        with st.chat_message("assistant", avatar="🌾"):
            with st.spinner("Searching the scheme knowledge base…"):
                try:
                    answer, sources, metrics = answer_question(question, language, history)
                except Exception as exc:
                    answer = ("I couldn't complete the search. Check that the FAISS index exists and "
                              "your API settings are configured.\\n\\nTechnical detail: " + str(exc))
                    sources, metrics = [], {"verification": "runtime_error"}
            st.markdown(answer)
            show_sources(sources)
            with st.expander("RAG diagnostics"):
                st.json(metrics)
        st.session_state.messages.append({
            "role": "assistant", "content": answer, "sources": sources, "metrics": metrics
        })

st.caption("Prototype only. Extracted records may be incomplete or historical. Verify current scheme status with the relevant government department.")
