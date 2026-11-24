"""
modules/rag_engine.py
----------------------
Backward-compatibility adapter forwarding to core.rag.
"""

from core.rag import (
    get_embedding_model,
    chunk_text,
    build_resume_index,
    search_similar_chunks,
    answer_resume_question,
)

# Alias for backwards compatibility
build_vector_store = build_resume_index

__all__ = [
    "get_embedding_model",
    "chunk_text",
    "build_vector_store",
    "build_resume_index",
    "search_similar_chunks",
    "answer_resume_question",
]
