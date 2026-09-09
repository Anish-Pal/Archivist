from pathlib import Path

from src.hashing import calculate_file_hash
from src.loaders import load_documents
from src.splitter import split_documents
from src.metadata import add_metadata
from src.vector_store import add_documents , is_document_indexed


def ingest_file(file_path , vector_store , user_id , document_id , original_filename):

    file_path = Path(file_path)

    file_hash = calculate_file_hash(file_path)

    if is_document_indexed(vector_store, file_hash , user_id):
        print("Document already indexed.")
        return "duplicate"

    documents = load_documents(file_path)

    chunks = split_documents(documents)

    metadata = {
        "file_hash": file_hash,
        "source": original_filename,
        "user_id" : user_id,
        "document_id" : document_id
    }

    chunks = add_metadata(chunks, metadata)

    ids = []

    for i, chunk in enumerate(chunks):

        chunk_id =  f"{user_id}_{file_hash}_chunk_{i}"

        chunk.metadata["id"] = chunk_id

        ids.append(chunk_id)

    add_documents(
        vector_store,
        chunks,
        ids
    )

    print("Document indexed successfully.")
    print("Chunks added:", len(chunks))

    return "indexed"
