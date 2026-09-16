"""
RAG pipeline for the Airport Operations AI Copilot.

Flow:

User Query
    ↓
Semantic Retrieval
    ↓
Relevant Policy Chunks
    ↓
Prompt Construction
    ↓
Gemini
    ↓
Grounded Response
"""

import os

from dotenv import load_dotenv
from google import genai

from src.embeddings import load_embedding_model
from src.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from src.vector_store import retrieve_documents


load_dotenv()


MODEL_NAME = "gemini-3.6-flash"


def create_rag_answer(
    query: str,
    collection,
    embedding_model,
    memory=None
):
    """
    Retrieve relevant policy chunks and generate a
    grounded answer using Gemini.
    """

    # ----------------------------------------
    # 1. Validate the user query
    # ----------------------------------------

    if not query or not query.strip():

        return (
            "Answer:\n"
            "I didn't receive a question. Please ask me about "
            "airport operations, policies, queues, pricing, "
            "cancellations, or approvals.\n\n"
            "Sources:\n"
            "- No applicable policy source found"
        )

    query = query.strip()

    # ----------------------------------------
    # Conversation history
    # ----------------------------------------

    if memory is not None:
        conversation_history = memory.format_history()
    else:
        conversation_history = "No previous conversation."   

    # ----------------------------------------
    # 2. Retrieve relevant documents
    # ----------------------------------------

    try:

        results = retrieve_documents(
            collection=collection,
            query=query,
            embedding_model=embedding_model,
            top_k=3
        )

    except Exception:

        return (
            "Answer:\n"
            "I couldn't retrieve the relevant airport policy "
            "information right now. I don't want to guess or "
            "give you an unsupported answer. Please try the "
            "question again, or ask about another airport "
            "operations policy.\n\n"
            "Sources:\n"
            "- No applicable policy source found"
        )

    # ----------------------------------------
    # 3. Check whether retrieval returned data
    # ----------------------------------------

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:

        return (
            "Answer:\n"
            "I couldn't find a relevant policy in the current "
            "airport knowledge base. I don't want to make up "
            "an answer without supporting policy information.\n\n"
            "I can help with airport operations, driver queues, "
            "pickup and drop-off rules, surge pricing, "
            "cancellations, incentives, and operational approvals.\n\n"
            "Sources:\n"
            "- No applicable policy source found"
        )

    # ----------------------------------------
    # 4. Build policy context
    # ----------------------------------------

    context_parts = []

    for document, metadata in zip(documents, metadatas):

        source = metadata.get(
            "source",
            "Unknown source"
        )

        airport = metadata.get(
            "airport",
            "Unknown airport"
        )

        context_parts.append(
            f"Source: {source}\n"
            f"Airport: {airport}\n"
            f"Policy:\n{document}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # ----------------------------------------
    # 5. Construct the Gemini prompt
    # ----------------------------------------

    system_prompt = RAG_SYSTEM_PROMPT.format(
        context=context
    )

    user_prompt = RAG_USER_PROMPT.format(
        query=query,
        conversation_history=conversation_history
    )

    final_prompt = (
        system_prompt
        + "\n\n"
        + user_prompt
    )

    # ----------------------------------------
    # 6. Check Gemini API key
    # ----------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return (
            "Answer:\n"
            "I retrieved the relevant airport policy, but "
            "the response service is not configured right now. "
            "I can't safely generate the final answer without "
            "the required service configuration.\n\n"
            "Sources:\n"
            "- Policy information was retrieved successfully"
        )

    # ----------------------------------------
    # 7. Call Gemini
    # ----------------------------------------

    try:

        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=final_prompt
        )

        if not response or not response.text:

            return (
                "Answer:\n"
                "I retrieved the relevant policy information, "
                "but I wasn't able to generate a response right "
                "now. Please try the question again.\n\n"
                "Sources:\n"
                "- Policy information was retrieved successfully"
            )

        answer = response.text

        if memory is not None:
                memory.add_turn(
                user_message=query,
                assistant_message=answer
            )

        return answer

    except Exception:

        return (
            "Answer:\n"
            "I found the relevant airport policy, but I couldn't "
            "generate the final response right now. I don't want "
            "to guess or provide unsupported information.\n\n"
            "Please try again in a moment, or ask another airport "
            "operations question.\n\n"
            "Sources:\n"
            "- Policy information was retrieved successfully"
        )