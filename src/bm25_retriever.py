import re
from rank_bm25 import BM25Okapi



def tokenize(text):
    return re.findall(r"\b\w+\b" , text.lower())



def create_bm25_retriever(chunks):

    tokenize_documents = [
        tokenize(chunk.page_content)
        for chunk in chunks
    ]

    bm25 = BM25Okapi(tokenize_documents)

    return bm25



def get_user_chunks(chunks , user_id):

    user_chunks = []

    for chunk in chunks:

        if chunk.metadata.get("user_id") == user_id:
            user_chunks.append(chunk)

    return user_chunks



def build_user_bm25(chunks):

    user_rag = {}

    for chunk in chunks:

        user_id = chunk.metadata.get("user_id")

        if user_id is None:
            continue

        if user_id not in user_rag:

            user_rag[user_id] = {
                "chunks" : []
            }

        user_rag[user_id]["chunks"].append(chunk)

    for user_id, data in user_rag.items():

        data["bm25"] = create_bm25_retriever(
            data["chunks"]
        )

    return user_rag




def search_bm25(bm25 , chunks , query , k = 5):

    tokenized_query = tokenize(query)

    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i : scores[i],
        reverse=True
    )[:k]

    results = []

    for index in top_indices:
        results.append({
            "chunk" : chunks[index],
            "scores" : scores[index],
            "index" : index
        })

    return results
