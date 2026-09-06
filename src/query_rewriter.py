from src.config import QUERY_REWRITER_MODEL
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_query_rewriter():

    client = Groq()

    return client


def rewrite_query(llm , history , query):

    prompt = f"""
    You are a query rewriting assistant for an enterprise document search system.

    Your job is to rewrite the user's latest question into a standalone
    search query that can be understood without the conversation history.

    Rules:

    - Use the conversation history only to resolve references such as
    "it", "this", "that", "they", "those", etc.
    - Preserve the user's original intent.
    - Do not answer the question.
    - Do not add information that is not present in the conversation.
    - If the question is already standalone, return it unchanged.
    - Return ONLY the rewritten query.
    - Do not add explanations.
    - Do not use quotation marks.

    Conversation history:
    {history}

    Latest user question:
    {query}

    Standalone query:
    """
    try:
            response = llm.chat.completions.create(

            model = QUERY_REWRITER_MODEL,

            messages = [
                {
                    "role" : "system",
                    "content": (
                        "You rewrite conversational questions "
                        "into standalone search queries."
                    )
                },
                {
                    "role" : "user",
                    "content" : prompt
                }
            ],

            max_completion_tokens = 100,

            reasoning_effort = "low",

            include_reasoning=False
            )

            return response.choices[0].message.content.strip()

    except Exception as e:
            print(
            f"Query rewriting failed: {e}"
            )

            return query





