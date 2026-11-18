"""
modules/rag_engine.py
----------------------
Text ko chunks mein todna, embeddings banana, FAISS se search karna.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embedding_model


def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)


def build_vector_store(text):
    chunks = chunk_text(text)
    embeddings = get_embedding_model()
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store


def search_similar_chunks(vector_store, query, k=3):
    results = vector_store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]