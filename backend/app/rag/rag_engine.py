"""
RAG engine: builds and queries a FAISS vector store populated
with carrier performance knowledge and procurement intelligence.
"""
import os
import pickle
import logging
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "../../data/faiss_index")

_vectorstore: FAISS = None


def _build_mock_vectorstore() -> FAISS:
    """Build a FAISS store from in-memory docs (no OpenAI needed for structure testing)."""
    from data.mock_data import CARRIER_KNOWLEDGE
    docs = [Document(page_content=text, metadata={"source": "carrier_intelligence"})
            for text in CARRIER_KNOWLEDGE]
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        vs = FAISS.from_documents(docs, embeddings)
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        vs.save_local(FAISS_INDEX_PATH)
        logger.info("[FAISS] index built and saved.")
        return vs
    except Exception as e:
        logger.warning(f"[WARN] OpenAI embeddings failed, building keyword fallback: {e}")
        return None


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if os.path.exists(FAISS_INDEX_PATH) and settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
            _vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            logger.info("[FAISS] index loaded from disk.")
            return _vectorstore
        except Exception as e:
            logger.warning(f"Failed to load FAISS: {e}")

    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        _vectorstore = _build_mock_vectorstore()
        return _vectorstore

    return None


def query_rag(query: str, k: int = 5) -> List[str]:
    """Query the RAG store; returns relevant text chunks."""
    vs = get_vectorstore()
    if vs is None:
        # Fallback: keyword search over mock data
        from data.mock_data import CARRIER_KNOWLEDGE
        query_lower = query.lower()
        results = [c for c in CARRIER_KNOWLEDGE if any(word in c.lower() for word in query_lower.split())]
        return results[:k] if results else CARRIER_KNOWLEDGE[:k]

    docs = vs.similarity_search(query, k=k)
    return [d.page_content for d in docs]


def build_index_from_documents(texts: List[str]):
    """Add new documents to the FAISS index."""
    global _vectorstore
    docs = [Document(page_content=t) for t in texts]
    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        if _vectorstore:
            _vectorstore.add_documents(docs)
        else:
            _vectorstore = FAISS.from_documents(docs, embeddings)
        _vectorstore.save_local(FAISS_INDEX_PATH)
