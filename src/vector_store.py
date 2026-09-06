from langchain_chroma import Chroma
from src.config import CHROMA_DB_PATH , COLLECTION_NAME


def get_vector_store(embedding_model):

    vector_store = Chroma(
        embedding_function = embedding_model,
        collection_name = COLLECTION_NAME,
        persist_directory = CHROMA_DB_PATH
    )
    return vector_store


def add_documents(vector_store , chunks , ids):

    vector_store.add_documents(
        documents = chunks,
        ids = ids
    )



def search_documents(vector_store , query , k=3):

    return vector_store.similarity_search(
        query = query,
        k = k
    )



def get_collection_count(vector_store):

    return vector_store._collection.count()




def delete_document_chunks(vector_store , document_id):

    result = vector_store.get(
        where = {
            "document_id" : document_id
        }
    )

    ids = result["ids"]

    if ids:
        vector_store.delete(
            ids = ids
        )

    return len(ids)    




def is_document_indexed(vector_store, file_hash , user_id):

    result = vector_store.get(
        where = {
            "$and":[
                {"file_hash" : file_hash},
                {"user_id" : user_id} 
            ]
        },
        limit=1
    )

    return len(result["ids"]) > 0