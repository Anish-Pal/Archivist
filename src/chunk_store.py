from langchain_core.documents import Document


def get_all_chunks(vector_store):

    data = vector_store.get(
        include = [
            "documents",
            "metadatas"
        ]
    )

    chunks = []

    for content , metadata in zip(data["documents"] , data["metadatas"]):

        chunks.append(
            Document(
                page_content = content,
                metadata = metadata
            )
        )

    return chunks




def get_user_chunk_from_store(vector_store , user_id):

    result = vector_store.get(
        where = {
            "user_id" : user_id
        }
    )

    chunks = []

    for i in range(len(result["ids"])):

        chunks.append(
            Document(
                page_content=result["documents"][i],
                metadata=result["metadatas"][i]
            )
        )

    return chunks    

