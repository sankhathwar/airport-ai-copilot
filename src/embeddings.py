from sentence_transformers import SentenceTransformer

import os

SYSTEM_CA = "/etc/ssl/certs/ca-certificates.crt"

os.environ["REQUESTS_CA_BUNDLE"] = SYSTEM_CA
os.environ["SSL_CERT_FILE"] = SYSTEM_CA
os.environ["CURL_CA_BUNDLE"] = SYSTEM_CA

print("Using certificate bundle:", SYSTEM_CA)

MODEL_NAME = "all-MiniLM-L6-v2"


def load_embedding_model():
    """
    Load the Sentence Transformer embedding model.
    """

    model = SentenceTransformer(MODEL_NAME)

    return model


def create_embeddings(texts: list[str]):
    """
    Convert a list of text chunks into numerical vectors.
    """

    model = load_embedding_model()

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    return embeddings