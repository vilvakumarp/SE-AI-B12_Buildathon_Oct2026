import streamlit as st
from dotenv import load_dotenv
from guardrails import valid_input
from rag_pipeline import answer_question

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
