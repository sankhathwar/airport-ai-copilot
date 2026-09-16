from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_policy_documents(policy_dir: str) -> list[Document]:

    documents = []

    policy_path = Path(policy_dir)

    for file_path in policy_path.glob("*.md"):

        if file_path.name == "README.md":
            continue

        text = file_path.read_text(encoding="utf-8")

        airport_code = file_path.stem.split("_")[0].upper()

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "file_path": str(file_path),
                "airport": airport_code
            }
        )

        documents.append(document)

    return documents



def split_documents(
    documents: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> list[Document]:
    """
    Split policy documents into smaller chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = splitter.split_documents(documents)

    return chunks