"""
modules/llm_engine.py
----------------------
Backward-compatibility adapter forwarding to core.llm.
"""

from typing import Tuple
from core.llm import (
    ask_llm,
    generate_interview_question,
    score_answer,
    get_coding_help,
    resolve_model,
    get_groq_client,
)
from core.prompts import (
    RAG_PROMPT_TEMPLATE,
    COMPANY_QUESTIONS_PROMPT_TEMPLATE,
)


def generate_rag_answer(context_chunks, question):
    context = "\n\n".join(context_chunks)
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
    return ask_llm(prompt)


def generate_company_questions(company, role):
    prompt = COMPANY_QUESTIONS_PROMPT_TEMPLATE.format(
        company=company, role=role, count=5, difficulty="Medium"
    )
    return ask_llm(prompt, max_tokens=800)


def evaluate_interview_answer(role, question, answer) -> Tuple[int, str]:
    res = score_answer(question=question, answer=answer, role=role)
    return res["score"], res["feedback"]


coding_help = get_coding_help

__all__ = [
    "ask_llm",
    "generate_rag_answer",
    "generate_company_questions",
    "generate_interview_question",
    "evaluate_interview_answer",
    "coding_help",
    "resolve_model",
    "get_groq_client",
]
