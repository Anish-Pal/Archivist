#=================================
# Project Configuration
#=================================

import os

#Folder Paths
# Overridable so the app can point at a mounted persistent volume in
# deployment (e.g. /data on Hugging Face Spaces) while defaulting to the
# local project directories during development.
DATA_FOLDER = os.getenv("DATA_FOLDER", "data")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "chroma_db")

#Text splitter
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

#Embedding Model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

#Reranking Model
RERANKER_MODEL = "BAAI/bge-reranker-base"

#LLM MODELs
LLM_MODEL = "openai/gpt-oss-120b"

QUERY_REWRITER_MODEL = "openai/gpt-oss-20b"


#chroma collection
COLLECTION_NAME = "enterprise_documents"

#supported file types
SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".txt",
    ".csv"
]
