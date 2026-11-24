"""
tests/test_core_llm.py
----------------------
Unit tests for LLM question generation, scoring, and coding assistant.
All tests run offline using mocked ask_llm.
"""

import pytest
from core.llm import (
    generate_questions,
    generate_interview_question,
    score_answer,
    get_coding_help,
)


class TestLLMCore:
    def test_generate_questions_parsing(self, mock_llm_response):
        questions = generate_questions(company="Google", role="Software Engineer", count=2)
        assert len(questions) == 2
        assert "process and thread" in questions[0]
        assert "garbage collection" in questions[1]

    def test_generate_questions_empty_company_raises(self):
        with pytest.raises(ValueError, match="Company and role must both be provided"):
            generate_questions(company="", role="AI Engineer")

    def test_generate_interview_question(self, mock_llm_response):
        q = generate_interview_question(role="Backend Developer", difficulty="Easy")
        assert len(q) > 0

    def test_score_answer_parsing(self, mock_llm_response):
        res = score_answer(
            question="What is an index in SQL?",
            answer="An index optimizes retrieval performance on database tables.",
            role="Database Admin",
        )
        assert res["score"] == 8
        assert "architectural" in res["feedback"]

    def test_score_answer_empty_returns_score_one(self):
        res = score_answer(question="What is OOP?", answer="", role="Java Developer")
        assert res["score"] == 1
        assert "submitting" in res["feedback"]

    def test_get_coding_help(self, mock_llm_response):
        res = get_coding_help("What is the difference between list and tuple?")
        assert "Solution" in res
        assert "mutable" in res
