from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader ,
    TextLoader ,
    CSVLoader
)


def load_documents(file_path):

    file_path = Path(file_path)

    if file_path.suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))

    elif file_path.suffix == ".txt":
        loader = TextLoader(str(file_path))

    elif file_path.suffix == ".csv":
        loader = CSVLoader(str(file_path))

    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    return loader.load()
