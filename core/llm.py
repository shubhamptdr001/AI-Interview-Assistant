"""
core/llm.py
-----------
Pure Python Groq LLM wrapper with dynamic model resolution, question generation,
answer scoring, and coding assistant logic.
No UI dependencies.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from core.config import settings
from core.prompts import (
    CODING_HELP_PROMPT_TEMPLATE,
    COMPANY_QUESTIONS_PROMPT_TEMPLATE,
    EVALUATE_ANSWER_PROMPT_TEMPLATE,
    INTERVIEW_QUESTION_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)

_groq_client = None
_resolved_model = None


def get_groq_client(api_key: Optional[str] = None):
    """Lazily initialize and return the Groq client.

    Args:
        api_key: Optional API key override. If omitted, settings.GROQ_API_KEY is used.
    """
    global _groq_client
    key = api_key or settings.GROQ_API_KEY
    if not key:
        return None

    if _groq_client is None or api_key is not None:
        from groq import Groq

        _groq_client = Groq(api_key=key)
    return _groq_client


def resolve_model(client) -> str:
    """Identify the optimal available chat model on the Groq account."""
    global _resolved_model
    if _resolved_model:
        return _resolved_model

    # Use explicit setting if provided
    if settings.GROQ_MODEL:
        _resolved_model = settings.GROQ_MODEL
        return _resolved_model

    preferred = [
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b",
    ]

    try:
        remote_models = [m.id for m in client.models.list().data]
        for candidate in preferred:
            if candidate in remote_models:
                _resolved_model = candidate
                return _resolved_model
        for m in remote_models:
            if "whisper" not in m and "guard" not in m:
                _resolved_model = m
                return _resolved_model
    except Exception as e:
        logger.warning(f"Could not query remote Groq models: {e}")

    _resolved_model = "qwen/qwen3.8-27b"
    return _resolved_model


def ask_llm(prompt: str, max_tokens: int = 700, api_key: Optional[str] = None) -> str:
    """Send a prompt to Groq and return the response text.

    Args:
        prompt: User prompt content.
        max_tokens: Maximum tokens in completion.
        api_key: Optional key override.

    Returns:
        Generated text string.
    """
    client = get_groq_client(api_key=api_key)
    if not client:
        return (
            "⚠️ Groq API Key not found! Please set GROQ_API_KEY in your .env file or environment."
        )

    model_name = resolve_model(client)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        err = str(e)
        # Attempt fallback to primary stable model if model not found
        if "model_not_found" in err or "404" in err:
            try:
                fallback_model = "qwen/qwen3.8-27b"
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e2:
                return f"⚠️ Groq API Error: {str(e2)}"
        return f"⚠️ Groq API Error: {err}"


def _parse_questions_from_text(raw: str, count: int = 5) -> List[str]:
    """Parse raw LLM generation into a clean list of complete interview questions.

    Robustly handles single-line numbered lists, multi-line numbered lists with separate
    'Type: ...' metadata lines, bolded markdown numbering, and bullet points.
    """
    if not raw or not raw.strip():
        return []

    # If it is an API error message, return it directly
    if raw.strip().startswith("⚠️"):
        return [raw.strip()]

    # Pattern to find numbered items (e.g. '1. ', '1) ', '**1.**', '1 - ') or bullets
    pattern = re.compile(
        r'(?:^|\n)\s*(?:\*\*)?(?:(?:\d{1,2}[\.\)]|\-|\*))\s*(?:\*\*)?\s*(.*?)(?=(?:\n\s*(?:\*\*)?(?:(?:\d{1,2}[\.\)]|\-|\*))\s*(?:\*\*)?)|$)',
        re.DOTALL,
    )

    matches = [m.group(1).strip() for m in pattern.finditer(raw) if m.group(1).strip()]
    cleaned_questions: List[str] = []

    for item in matches:
        # Strip outer bold/italic markdown
        cleaned = re.sub(r"^\*+|\*+$", "", item).strip()
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        if not lines:
            continue

        # Check if first line is only metadata (e.g., 'Type: Technical' or 'Category: ...')
        if len(lines) > 1 and re.match(
            r"^(?:type|category|round)\s*:\s*(?:technical|behavioral|hr|system design|coding)?\s*$",
            lines[0],
            re.IGNORECASE,
        ):
            meta_line = lines[0]
            body_lines = lines[1:]
            q_text = " ".join(body_lines)
            type_match = re.search(r"(technical|behavioral|hr|system design|coding)", meta_line, re.IGNORECASE)
            if type_match and not re.search(
                r"\((technical|behavioral|hr|system design|coding)\)", q_text, re.IGNORECASE
            ):
                q_text = f"{q_text} ({type_match.group(1).capitalize()})"
        # Check if last line is metadata
        elif len(lines) > 1 and re.match(
            r"^(?:type|category|round)\s*:\s*(?:technical|behavioral|hr|system design|coding)?\s*$",
            lines[-1],
            re.IGNORECASE,
        ):
            meta_line = lines[-1]
            body_lines = lines[:-1]
            q_text = " ".join(body_lines)
            type_match = re.search(r"(technical|behavioral|hr|system design|coding)", meta_line, re.IGNORECASE)
            if type_match and not re.search(
                r"\((technical|behavioral|hr|system design|coding)\)", q_text, re.IGNORECASE
            ):
                q_text = f"{q_text} ({type_match.group(1).capitalize()})"
        else:
            q_text = " ".join(lines)

        # Strip prefixes like 'Question: ', 'Q1: ', 'Type: Technical - '
        q_text = re.sub(r"^(?:question\s*\d*\s*:\s*|q\s*\d*\s*:\s*)", "", q_text, flags=re.IGNORECASE).strip()
        q_text = re.sub(
            r"^(?:type|category)\s*:\s*(?:technical|behavioral|hr|system design|coding)\s*[-:]\s*",
            "",
            q_text,
            flags=re.IGNORECASE,
        ).strip()

        # Sanity check: must be a substantive question, not just a standalone label
        if len(q_text) >= 15 and not re.match(
            r"^(?:type\s*:\s*)?(?:technical|behavioral|hr|coding)\s*$", q_text, re.IGNORECASE
        ):
            cleaned_questions.append(q_text)

    # Fallback to double newline split if list parsing yielded nothing
    if not cleaned_questions:
        paragraphs = [p.strip() for p in raw.split("\n\n") if len(p.strip()) >= 15]
        cleaned_questions = paragraphs

    return cleaned_questions[:count] if cleaned_questions else [raw.strip()]


def generate_questions(
    company: str,
    role: str,
    count: int = 5,
    difficulty: str = "Medium",
    api_key: Optional[str] = None,
) -> List[str]:
    """Generate company and role-specific interview questions.

    Args:
        company: Target company (e.g. 'Google', 'TCS').
        role: Target role (e.g. 'Software Engineer', 'Data Scientist').
        count: Number of questions to generate.
        difficulty: Difficulty level ('Easy', 'Medium', 'Hard').
        api_key: Optional Groq API key override.

    Returns:
        List of generated question strings.
    """
    if not company or not role:
        raise ValueError("Company and role must both be provided.")

    prompt = COMPANY_QUESTIONS_PROMPT_TEMPLATE.format(
        company=company.strip(),
        role=role.strip(),
        count=count,
        difficulty=difficulty,
    )
    raw = ask_llm(prompt, max_tokens=900, api_key=api_key)
    return _parse_questions_from_text(raw, count=count)


def generate_interview_question(
    role: str,
    difficulty: str = "Easy",
    previous_questions: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> str:
    """Generate a single fresh interview question for a mock interview round.

    Args:
        role: Target role (e.g. 'Software Engineer').
        difficulty: 'Easy', 'Medium', or 'Hard'.
        previous_questions: List of previously asked questions to avoid duplication.
        api_key: Optional key override.

    Returns:
        A single interview question.
    """
    if not role or not role.strip():
        raise ValueError("Role must be provided.")

    prev_list = "\n".join(previous_questions) if previous_questions else "None"
    prompt = INTERVIEW_QUESTION_PROMPT_TEMPLATE.format(
        role=role.strip(),
        difficulty=difficulty,
        previous_questions=prev_list,
    )
    question = ask_llm(prompt, max_tokens=250, api_key=api_key)
    return question.strip().strip('"')


def score_answer(
    question: str,
    answer: str,
    role: str = "Software Engineer",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate a candidate's answer to an interview question.

    Returns score (1-10), correctness percentage, what was correct,
    and what was missing in clear English.

    Args:
        question: The interview question asked.
        answer: Candidate's response.
        role: Targeted role.
        api_key: Optional key override.

    Returns:
        Dictionary with 'score', 'correctness_percent', 'what_was_good',
        'what_is_missing', and 'feedback'.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")
    if not answer or not answer.strip():
        return {
            "score": 1,
            "correctness_percent": 10,
            "what_was_good": "No answer was provided.",
            "what_is_missing": "The complete answer was missing. Please attempt the question to receive technical evaluation.",
            "feedback": "Please type your technical response before submitting.",
        }

    prompt = EVALUATE_ANSWER_PROMPT_TEMPLATE.format(
        role=role,
        question=question.strip(),
        answer=answer.strip(),
    )
    raw = ask_llm(prompt, max_tokens=600, api_key=api_key)

    score = 5
    correct = ""
    missing = ""
    feedback = raw

    try:
        current_section = None
        for line in raw.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.upper().startswith("SCORE:"):
                digits = "".join(filter(str.isdigit, line_str))
                if digits:
                    parsed_score = int(digits)
                    score = max(1, min(10, parsed_score))
                current_section = "SCORE"
            elif line_str.upper().startswith("CORRECT:"):
                correct = line_str[len("CORRECT:") :].strip()
                current_section = "CORRECT"
            elif line_str.upper().startswith("MISSING:"):
                missing = line_str[len("MISSING:") :].strip()
                current_section = "MISSING"
            elif line_str.upper().startswith("FEEDBACK:"):
                feedback = line_str[len("FEEDBACK:") :].strip()
                current_section = "FEEDBACK"
            else:
                if current_section == "CORRECT":
                    correct += " " + line_str
                elif current_section == "MISSING":
                    missing += " " + line_str
                elif current_section == "FEEDBACK":
                    feedback += " " + line_str
    except Exception as e:
        logger.warning(f"Error parsing evaluation response: {e}")

    # Fallbacks if sections were not cleanly formatted
    if not correct:
        correct = "You covered the fundamental concept." if score >= 5 else "An initial attempt was made."
    if not missing:
        missing = "Consider including specific implementation examples, complexity analysis, and edge cases."

    return {
        "score": score,
        "correctness_percent": score * 10,
        "what_was_good": correct.strip(),
        "what_is_missing": missing.strip(),
        "feedback": feedback.strip(),
    }


def get_coding_help(query: str, api_key: Optional[str] = None) -> str:
    """Generate coding assistance, concept explanations, and commented code.

    Args:
        query: User coding doubt or question.
        api_key: Optional key override.

    Returns:
        Formatted markdown answer with explanation and code snippets.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    prompt = CODING_HELP_PROMPT_TEMPLATE.format(query=query.strip())
    return ask_llm(prompt, max_tokens=1000, api_key=api_key)
