import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from document_loader import load_documents, split_documents

load_dotenv()
INDEX_DIR = Path("data/faiss_index")

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in .env.")
    docs = load_documents()
    chunks = split_documents(docs)
    if not chunks:
        raise RuntimeError("No chunks were created.")
    print(f"Loaded {len(docs)} source records/pages; creating {len(chunks)} chunks.")
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    store = FAISS.from_documents(chunks, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))
    print(f"FAISS index saved to {INDEX_DIR.resolve()}")

if __name__ == "__main__":
    main()
