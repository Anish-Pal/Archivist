def add_metadata(chunks , metadata):
    for chunk in chunks:
        for key , value in metadata.items():

            chunk.metadata[key] = value

    return chunks
