from src.config import LLM_MODEL
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

def get_llm():

    client = Groq()

    return client


def generate_answer(llm , query , context):

    prompt = f"""
    You are an enterprise document assistant.

    Answer the user's question using ONLY the provided context.

    If the answer cannot be found in the context,
    say that you do not have enough information.

    IMPORTANT CITATION RULES:

    - Every factual statement must have a citation when supported by the context.
    - Citations MUST use exactly this format: 【1】
    - Multiple citations MUST use this format: 【1】【2】
    - NEVER use [1], [2], [1][2], (1), or any other citation format.
    - Only use citation numbers that actually appear in the provided context.
    - Do not invent citation numbers.

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    try:

        response = llm.chat.completions.create(

            model=LLM_MODEL,

            messages=[
                {
                    "role": "system",
                     "content": (
                        "You answer questions using the provided document context. "
                        "Always use citations in exactly the format 【1】 or 【1】【2】."
                )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content


    except Exception as e:

            print(f"LLM API error: {e}")

            return (
                "Sorry, I could not generate an answer "
                "because the language model service is "
                "currently unavailable."
            )
    