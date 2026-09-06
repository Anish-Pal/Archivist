from pathlib import Path

from src.embedder import get_embedding_model
from src.vector_store import get_vector_store
from src.reranker import get_reranker
from src.llm import get_llm
from src.query_rewriter import get_query_rewriter
from src.bm25_retriever import build_user_bm25
from src.chunk_store import get_all_chunks



def initialize_rag():


    # =========================
    # Embedding + Vector Store
    # =========================

    embedding_model = get_embedding_model()

    vector_store = get_vector_store(
        embedding_model
    )


    all_chunks = get_all_chunks(
        vector_store
    )

    user_rag = build_user_bm25(
        all_chunks
    )

    # =========================
    # Load Models
    # =========================

    reranker_model = get_reranker()

    llm = get_llm()

    query_rewriter = get_query_rewriter()


    return {
        "vector_store": vector_store,
        "reranker_model": reranker_model,
        "llm": llm,
        "query_rewriter": query_rewriter,
        "user_rag" : user_rag
    }

