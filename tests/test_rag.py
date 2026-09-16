from src.document_loader import load_policy_documents, split_documents
from src.embeddings import load_embedding_model
from src.vector_store import create_vector_store, retrieve_documents


POLICY_DIR = "data/airport_policies"


def setup_rag():
    """
    Load policies, create chunks, embeddings,
    and initialize the ChromaDB collection.
    """

    documents = load_policy_documents(POLICY_DIR)

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=100
    )

    embedding_model = load_embedding_model()

    embeddings = embedding_model.encode(
        [chunk.page_content for chunk in chunks],
        show_progress_bar=False
    )

    collection = create_vector_store(
        chunks,
        embeddings
    )

    return collection, embedding_model


def test_sfo_surge_policy_retrieval():

    collection, embedding_model = setup_rag()

    results = retrieve_documents(
        collection=collection,
        query="What is the maximum surge allowed at SFO?",
        embedding_model=embedding_model,
        top_k=3
    )

    sources = [
        metadata["source"]
        for metadata in results["metadatas"][0]
    ]

    assert "sfo_pricing.md" in sources


def test_jfk_surge_policy_retrieval():

    collection, embedding_model = setup_rag()

    results = retrieve_documents(
        collection=collection,
        query="What is the maximum surge allowed at JFK?",
        embedding_model=embedding_model,
        top_k=3
    )

    sources = [
        metadata["source"]
        for metadata in results["metadatas"][0]
    ]

    assert "jfk_pricing.md" in sources


def test_sfo_driver_queue_policy_retrieval():

    collection, embedding_model = setup_rag()

    results = retrieve_documents(
        collection=collection,
        query="Can an SFO driver abandon the airport queue?",
        embedding_model=embedding_model,
        top_k=3
    )

    sources = [
        metadata["source"]
        for metadata in results["metadatas"][0]
    ]

    assert "sfo_driver_policy.md" in sources


def test_surge_approval_policy_retrieval():

    collection, embedding_model = setup_rag()

    results = retrieve_documents(
        collection=collection,
        query="Does increasing surge require approval?",
        embedding_model=embedding_model,
        top_k=3
    )

    sources = [
        metadata["source"]
        for metadata in results["metadatas"][0]
    ]

    assert "sfo_pricing.md" in sources