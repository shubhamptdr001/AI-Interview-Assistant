"""
tests/conftest.py
-----------------
Pytest configuration and offline test fixtures.
Ensures zero external network dependencies for unit & API tests.
"""

import io
import os
import pytest
from unittest.mock import MagicMock

# Force test configuration
os.environ["GROQ_API_KEY"] = "mock_groq_api_key_test_12345"
os.environ["GROQ_MODEL"] = "qwen/qwen3.8-27b"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100/minute"


@pytest.fixture
def mock_llm_response(monkeypatch):
    """Fixture that mocks core.llm.ask_llm with deterministic offline responses."""
    def _mock_ask(prompt: str, max_tokens: int = 700, api_key=None) -> str:
        prompt_lower = prompt.lower()
        if "score:" in prompt_lower or "evaluate" in prompt_lower:
            return "SCORE: 8\nFEEDBACK: Excellent answer with strong architectural fundamentals."
        elif "interview questions" in prompt_lower or "commonly asked" in prompt_lower:
            return "1. Explain the difference between process and thread.\n2. How does garbage collection work in Python?"
        elif "coding mentor" in prompt_lower:
            return "### Solution\nA list is mutable while a tuple is immutable.\n```python\nmy_list = [1, 2]\n```"
        elif "analyze" in prompt_lower and "json" in prompt_lower:
            return (
                '{"target_role": "Backend Engineer", '
                '"profile_summary": "Strong backend candidate with Python and database experience.", '
                '"strengths": ["Clear API design experience", "Good database background"], '
                '"skill_gaps": ["Kubernetes orchestration"], '
                '"actionable_recommendations": ["Add CI/CD pipeline details"], '
                '"estimated_match_score": 85}'
            )
        elif "context:" in prompt_lower:
            return "Candidate has 2 years of experience building Python and FastAPI microservices."
        return "Mock response for interview assistant."

    import core.llm
    monkeypatch.setattr(core.llm, "ask_llm", _mock_ask)
    return _mock_ask


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Generate in-memory synthetic DOCX file bytes."""
    import docx
    doc = docx.Document()
    doc.add_heading("John Doe - Software Engineer", level=1)
    doc.add_paragraph("Experienced in Python, SQL, Docker, and Machine Learning.")
    doc.add_paragraph("Developed scalable REST APIs using FastAPI and LangChain.")
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume plain text with standard technical keywords."""
    return (
        "John Doe\n"
        "Email: john.doe@example.com | Phone: +1-555-0199\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Senior Software Developer with 4 years of experience building scalable backend microservices.\n"
        "SKILLS\n"
        "Languages: Python, Java, C++, SQL\n"
        "Frameworks: FastAPI, Flask, Streamlit, LangChain\n"
        "Tools & Cloud: Docker, Git, GitHub, PostgreSQL, FAISS, PyTorch\n\n"
        "EXPERIENCE\n"
        "Software Engineer at Acme Corp (2022 - Present)\n"
        "- Built RAG search engine with FAISS and Sentence Transformers improving query recall by 35%.\n"
        "- Designed high-throughput REST APIs handling 10k requests/minute."
    )
