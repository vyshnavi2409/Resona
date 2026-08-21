from langchain_core.documents import Document
from backend.core.chunking import split_documents

def test_split_documents():
    doc = Document(page_content="This is a test document. " * 100, metadata={"source": "test.txt"})
    chunks = split_documents([doc], chunk_size=100, chunk_overlap=20)
    
    assert len(chunks) > 1
    assert chunks[0].metadata["source"] == "test.txt"
