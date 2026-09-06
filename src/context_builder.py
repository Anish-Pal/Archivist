def build_context(reranked_results):

    context_parts = []

    citations = {}

    for number , result in enumerate(reranked_results , start=1):

        doc = result["chunk"]

        source = doc.metadata.get("source" , "unknown")

        page = doc.metadata.get("page" , "unknown")

        content = doc.page_content

        citations[number] = {
            "source": source,
            "page" : page
        }

        context_parts.append(
            f"""
            [{number}]
            source : {source}
            page : {page}

            {content}
            """
        )


    context = "\n---\n".join(context_parts)

    return context , citations