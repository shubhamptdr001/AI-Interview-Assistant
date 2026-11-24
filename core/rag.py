"""
core/rag.py
-----------
Pure Python RAG pipeline using LangChain, FAISS, Sentence Transformers, and Groq.
No UI dependencies.
"""

import logging
from typing import Any, Dict, List, Optional

from core.config import settings
from core.prompts import RAG_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

_embedding_model = None


def get_embedding_model():
    """Lazily load and cache the HuggingFace sentence transformer embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError as e:
                raise ImportError(
                    "Either 'langchain-community' or 'langchain-huggingface' with 'sentence-transformers' is required."
                ) from e

        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
    return _embedding_model


def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[str]:
    """Split text into overlapping semantic chunks using RecursiveCharacterTextSplitter.

    Args:
        text: Plain text to split.
        chunk_size: Maximum characters per chunk (default from settings).
        chunk_overlap: Overlapping characters between adjacent chunks.

    Returns:
        List of non-empty text chunk strings.
    """
    if not text or not text.strip():
        return []

    c_size = chunk_size or settings.CHUNK_SIZE
    c_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=c_size,
        chunk_overlap=c_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_text(text)


def build_resume_index(text: str) -> Any:
    """Build an in-memory FAISS vector index from resume text.

    Args:
        text: Plain text extracted from resume.

    Returns:
        A FAISS vectorstore instance.

    Raises:
        ValueError: If text is empty or no chunks are generated.
    """
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Cannot build vector index from empty text.")

    from langchain_community.vectorstores import FAISS

    embeddings = get_embedding_model()
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store


def search_similar_chunks(
    vector_store: Any, query: str, k: Optional[int] = None
) -> List[str]:
    """Perform similarity search on the FAISS vector index.

    Args:
        vector_store: FAISS vectorstore instance.
        query: User question or search phrase.
        k: Number of most relevant chunks to retrieve.

    Returns:
        List of matching text chunk contents.
    """
    if vector_store is None or not query or not query.strip():
        return []

    top_k = k or settings.RAG_TOP_K
    results = vector_store.similarity_search(query, k=top_k)
    return [doc.page_content for doc in results]


def answer_resume_question(
    vector_store: Any, question: str, k: Optional[int] = None
) -> Dict[str, Any]:
    """Answer a user's question about a resume using RAG and Groq LLM.

    Args:
        vector_store: FAISS vectorstore instance for the resume.
        question: Question asked by the user.
        k: Number of context chunks to retrieve.

    Returns:
        Dictionary with 'answer' (str) and 'sources' (list of context chunks).
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    chunks = search_similar_chunks(vector_store, question, k=k)

    if not chunks:
        return {
            "answer": "Ye information resume mein nahi mili.",
            "sources": [],
        }

    from core.llm import ask_llm

    context_str = "\n\n".join(chunks)
    prompt = RAG_PROMPT_TEMPLATE.format(context=context_str, question=question)

    answer = ask_llm(prompt)
    return {
        "answer": answer,
        "sources": chunks,
    }
