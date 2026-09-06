from src.config import RERANKER_MODEL
from sentence_transformers import CrossEncoder

def get_reranker():

    model = CrossEncoder(
        RERANKER_MODEL
    )

    return model


def rerank(model , query , documents , top_k = 5):

    pairs = [
        (query , doc.page_content)
        for doc in documents
    ]

    scores = model.predict(pairs)

    results = []

    for doc , score in zip(documents , scores):

        results.append({
            "chunk": doc,
            "score": score
        })

    results.sort(
        key = lambda x : x["score"],
        reverse = True
    )

    return results[:top_k]     