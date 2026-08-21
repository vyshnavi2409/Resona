import os
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Define the persistence directory for ChromaDB
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

_vector_store_instance = None
_embeddings_instance = None

def get_embeddings_model():
    """
    Returns the embedding model. Defaulting to Google Generative AI Embeddings.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return _embeddings_instance

def get_vector_store() -> Chroma:
    """
    Initializes and returns the Chroma vector store.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        embeddings = get_embeddings_model()
        
        # Check if the directory exists and initialize Chroma
        _vector_store_instance = Chroma(
            collection_name="rag_documents",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
    return _vector_store_instance

def add_documents_to_vector_store(documents: List[Document]) -> Chroma:
    """
    Adds a list of chunked documents to the Chroma vector store.
    """
    vector_store = get_vector_store()
    
    # Adding documents in batches if necessary, but Chroma handles standard sizes well.
    # We assign UUIDs or let Chroma auto-assign. We'll let Chroma auto-assign.
    vector_store.add_documents(documents)
    return vector_store

def clear_vector_store():
    """
    Clears the vector store by deleting the collection from ChromaDB.
    """
    global _vector_store_instance
    try:
        vector_store = get_vector_store()
        vector_store.delete_collection()
    except Exception as e:
        # Collection might not exist yet, that's fine
        pass
    finally:
        _vector_store_instance = None
