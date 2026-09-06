from src.config import EMBEDDING_MODEL
from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model():

    embedding_model = HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL
    )
    return embedding_model
