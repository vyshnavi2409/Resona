import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    TextLoader
)

def load_document(file_path: str) -> List[Document]:
    """
    Loads a document from the given file path based on its extension.
    Supported formats: .pdf, .docx, .csv, .txt
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path)
    elif ext == ".txt":
        # Handle potential encoding issues with generic text files
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load()
        except UnicodeDecodeError:
            loader = TextLoader(file_path, encoding="latin-1")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    return loader.load()

def clean_document_text(documents: List[Document]) -> List[Document]:
    """
    Cleans the text content of the loaded documents.
    """
    for doc in documents:
        # Example cleaning: removing excessive whitespace and newlines
        doc.page_content = " ".join(doc.page_content.split())
    return documents

def process_document(file_path: str) -> List[Document]:
    """
    Loads and cleans a document.
    """
    documents = load_document(file_path)
    return clean_document_text(documents)
