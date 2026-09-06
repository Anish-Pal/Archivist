def needs_query_rewriting(query , history):

    if not history:
        return False

    query = query.lower().strip()

    follow_up_patterns = [
        "what about",
        "how about",
        "what is its",
        "what are its",
        "how does it",
        "how do they",
        "why does it",
        "why do they",
        "what does it",
        "what do they",
        "where does it",
        "when does it",
        "which one",
        "the previous",
        "the above"
    ]

    for pattern in follow_up_patterns:

        if pattern in query:
            return True


    words = query.split()

    pronouns = [
        "it",
        "its",
        "they",
        "them",
        "this",
        "that",
        "these",
        "those"
    ]

    for word in words:

        word = word.strip(".,?!")

        if word in pronouns:
            return True


    return False


