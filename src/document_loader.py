from pathlib import Path
from langchain_core.documents import Document


def load_policy_documents(policy_dir: str) -> list[Document]:
    """
    Load all Markdown policy files from the policy directory.
    """

    documents = []

    policy_path = Path(policy_dir)

    for file_path in policy_path.glob("*.md"):

        text = file_path.read_text(encoding="utf-8")

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "file_path": str(file_path)
            }
        )

        documents.append(document)

    return documents