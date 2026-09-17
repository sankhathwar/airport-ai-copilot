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
Grounded Response + Retrieved Sources
"""

import os

from dotenv import load_dotenv
from google import genai

from src.prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT,
)
from src.vector_store import retrieve_documents

import os

SYSTEM_CA = "/etc/ssl/certs/ca-certificates.crt"

os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA
os.environ["SSL_CERT_FILE"] = SYSTEM_CA
os.environ["CURL_CA_BUNDLE"] = SYSTEM_CA

print("Using certificate bundle:", SYSTEM_CA)

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

    Returns a consistent dictionary containing:
    - answer
    - retrieved_documents
    """

    # ----------------------------------------
    # 1. Validate user query
    # ----------------------------------------

    if not query or not query.strip():

        return {
            "answer": (
                "I didn't receive a question. Please ask me "
                "about airport operations, policies, queues, "
                "pricing, cancellations, or approvals."
            ),
            "retrieved_documents": []
        }

    query = query.strip()

    # ----------------------------------------
    # 2. Conversation history
    # ----------------------------------------

    if memory is not None:
        conversation_history = memory.format_history()
    else:
        conversation_history = "No previous conversation."

    # ----------------------------------------
    # 3. Retrieve policy documents
    # ----------------------------------------

    try:

        results = retrieve_documents(
            collection=collection,
            query=query,
            embedding_model=embedding_model,
            top_k=3
        )

    except Exception:

        return {
            "answer": (
                "I couldn't retrieve the relevant airport "
                "policy information right now. I don't want "
                "to guess or provide unsupported information."
            ),
            "retrieved_documents": []
        }

    # ----------------------------------------
    # 4. Extract retrieved documents
    # ----------------------------------------

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    # ----------------------------------------
    # 5. Check retrieval result
    # ----------------------------------------

    if not documents:

        return {
            "answer": (
                "I couldn't find a relevant policy in the "
                "current airport knowledge base. I don't want "
                "to make up an answer without supporting "
                "policy information."
            ),
            "retrieved_documents": []
        }

    # ----------------------------------------
    # 6. Build structured retrieved documents
    # ----------------------------------------

    retrieved_documents = []

    for index, document in enumerate(documents):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        source = metadata.get(
            "source",
            "Unknown source"
        )

        airport = metadata.get(
            "airport",
            "Unknown airport"
        )

        retrieved_documents.append(
            {
                "source": source,
                "airport": airport,
                "content": document,
                "distance": distance
            }
        )

    # ----------------------------------------
    # 7. Build policy context for Gemini
    # ----------------------------------------

    context_parts = []

    for document in retrieved_documents:

        context_parts.append(
            f"Source: {document['source']}\n"
            f"Airport: {document['airport']}\n"
            f"Policy:\n{document['content']}"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    # ----------------------------------------
    # 8. Construct Gemini prompts
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
    # 9. Check Gemini API key
    # ----------------------------------------

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return {
            "answer": (
                "I retrieved the relevant airport policy, "
                "but the response service is not configured "
                "right now. I can't safely generate the final "
                "answer without the required service "
                "configuration."
            ),
            "retrieved_documents": retrieved_documents
        }

    # ----------------------------------------
    # 10. Call Gemini
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

            return {
                "answer": (
                    "I retrieved the relevant policy "
                    "information, but I wasn't able to "
                    "generate a response right now."
                ),
                "retrieved_documents": retrieved_documents
            }

        answer = response.text

        # ----------------------------------------
        # 11. Update conversation memory
        # ----------------------------------------

        if memory is not None:

            memory.add_turn(
                user_message=query,
                assistant_message=answer
            )

        # ----------------------------------------
        # 12. Return answer + actual sources
        # ----------------------------------------

        return {
            "answer": answer,
            "retrieved_documents": retrieved_documents
        }

    except Exception as e:

        return {
            "answer": (
                "I retrieved the relevant airport policy, "
                "but I couldn't generate the final response "
                "right now. I don't want to guess or provide "
                "unsupported information."
            ),
            "retrieved_documents": retrieved_documents,
            "error": str(e)
        }