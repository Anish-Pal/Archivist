from src.query_detector import needs_query_rewriting
from src.query_rewriter import rewrite_query

from src.hybrid_retriever import hybrid_retriever
from src.reranker import rerank
from src.context_builder import build_context
from src.llm import generate_answer
from src.citations import get_citations




def process_query(
    query,
    history,
    vector_store,
    chunks,
    bm25,
    reranker_model,
    llm,
    query_rewriter,
    user_id
):

    # =========================
    # Query Rewriting
    # =========================

    if needs_query_rewriting(
        query,
        history
    ):

        search_query = rewrite_query(
            query_rewriter,
            history,
            query
        )

        print(
            f"\nRewritten query: {search_query}"
        )

    else:

        search_query = query


    # =========================
    # Hybrid Retrieval
    # =========================

    results = hybrid_retriever(
        vector_store,
        bm25,
        chunks,
        search_query,
        user_id,
        k=10
    )


    # =========================
    # Candidate Documents
    # =========================

    candidate_documents = [
        result["chunk"]
        for result in results
    ]


    # =========================
    # Reranking
    # =========================

    reranked_results = rerank(
        reranker_model,
        search_query,
        candidate_documents,
        top_k=5
    )


    # =========================
    # Build Context
    # =========================

    context, citations = build_context(
        reranked_results
    )


    # =========================
    # Generate Answer
    # =========================

    answer = generate_answer(
        llm,
        search_query,
        context
    )


    # =========================
    # Get Citations
    # =========================

    sources = get_citations(
        answer,
        citations
    )


    return answer, sources
