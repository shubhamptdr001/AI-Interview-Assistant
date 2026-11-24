"""
core package
------------
Clean, decoupled core business logic for AI Interview Assistant.
Independent of UI frameworks (Streamlit/FastAPI/MCP).
"""

from core.config import settings, Settings
from core.prompts import PROMPT_VERSION
from core.resume import (
    parse_resume,
    extract_skills,
    get_word_count,
    analyze_resume,
)
from core.rag import (
    chunk_text,
    get_embedding_model,
    build_resume_index,
    search_similar_chunks,
    answer_resume_question,
)
from core.llm import (
    get_groq_client,
    resolve_model,
    ask_llm,
    generate_questions,
    generate_interview_question,
    score_answer,
    get_coding_help,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    "PROMPT_VERSION",
    # Resume
    "parse_resume",
    "extract_skills",
    "get_word_count",
    "analyze_resume",
    # RAG
    "chunk_text",
    "get_embedding_model",
    "build_resume_index",
    "search_similar_chunks",
    "answer_resume_question",
    # LLM
    "get_groq_client",
    "resolve_model",
    "ask_llm",
    "generate_questions",
    "generate_interview_question",
    "score_answer",
    "get_coding_help",
]
