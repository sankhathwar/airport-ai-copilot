import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "airport_policies"


def create_vector_store(chunks, embeddings):
    """
    Store policy chunks, embeddings, and metadata in ChromaDB.
    """

    client = chromadb.PersistentClient(
        path=".chroma"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    documents = [
        chunk.page_content
        for chunk in chunks
    ]

    metadatas = [
        chunk.metadata
        for chunk in chunks
    ]

    ids = [
        f"chunk_{i}"
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    return collection

def retrieve_documents(
    collection,
    query: str,
    embedding_model,
    top_k: int = 3
):
    """
    Retrieve the most relevant policy chunks for a user query.
    """

    query_embedding = embedding_model.encode(
        [query]
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    return results