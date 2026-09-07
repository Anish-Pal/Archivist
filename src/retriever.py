
def get_retriever(vector_store , k = 3):
    retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs={
            "k": k
        }
    )

    return retriever


def get_mmr_retriever(vector_store , k = 3 , lambda_mult = 0.5):
    retriever = vector_store.as_retriever(
        search_type = "mmr",
        search_kwargs={
            "k" : k,
            "lamda_mult" : lambda_mult
        }
    )

    return retriever
