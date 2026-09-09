from src.bm25_retriever import search_bm25



def reciprocal_rank_fusion(vector_results , bm25_results , rrf_constant = 60):

    scores = {}
    documents = {}

    # -------------------------
    # Vector results
    # -------------------------

    for rank , doc in enumerate(vector_results , start=1):

        doc_id = doc.metadata["id"]

        documents[doc_id] = doc

        scores[doc_id] = scores.get(doc_id , 0) + (1 / (rrf_constant + rank))


    # -------------------------
    # BM25 results
    # -------------------------


    for rank , result in enumerate(bm25_results , start=1):

        doc = result["chunk"]

        doc_id = doc.metadata["id"]

        documents[doc_id] = doc

        scores[doc_id] = scores.get(doc_id, 0) + (1 / (rrf_constant + rank))



    # -------------------------
    # Sort by RRF score
    # -------------------------


    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    results = []


    for doc_id in ranked_ids:

        results.append({
            "chunk" : documents[doc_id],
            "rrf_score" : scores[doc_id]
        })

    return results




def hybrid_retriever(vector_store , bm25 , chunks , query , user_id, k=5 , rrf_constant=60):

    # =========================
    # Vector Search
    # =========================

    vector_results = vector_store.similarity_search(
        query=query,
        k=k,
        filter = {
            "user_id" : user_id
        }
    )

    # =========================
    # BM25 Search
    # =========================

    bm25_results = search_bm25(
        bm25,
        chunks,
        query,
        k=5
    )


    # =========================
    # RRF
    # =======================

    hybrid_results = reciprocal_rank_fusion(
        vector_results,
        bm25_results,
        rrf_constant=rrf_constant
    )

    return hybrid_results[:k]
