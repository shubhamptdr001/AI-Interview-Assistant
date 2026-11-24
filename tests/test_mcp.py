"""
tests/test_mcp.py
-----------------
Smoke tests for FastMCP tools exposed in mcp_server/server.py.
Verifies tool signatures, docstrings, and execution with mocked core dependencies.
"""

from mcp_server.server import generate_questions, score_answer, analyze_resume


class TestMCPServerTools:
    def test_generate_questions_tool(self, mock_llm_response):
        questions = generate_questions(company="Google", role="AI Engineer", count=2, difficulty="Hard")
        assert isinstance(questions, list)
        assert len(questions) == 2
        assert generate_questions.__doc__ is not None
        assert "company" in generate_questions.__doc__

    def test_score_answer_tool(self, mock_llm_response):
        result = score_answer(
            question="Explain CAP theorem.",
            answer="CAP theorem states a distributed system can only guarantee two of Consistency, Availability, Partition tolerance.",
            role="Distributed Systems Engineer",
        )
        assert isinstance(result, dict)
        assert "score" in result
        assert "feedback" in result
        assert result["score"] == 8
        assert score_answer.__doc__ is not None

    def test_analyze_resume_tool(self, mock_llm_response, sample_resume_text):
        analysis = analyze_resume(resume_text=sample_resume_text, role="Backend Engineer")
        assert isinstance(analysis, dict)
        assert "target_role" in analysis
        assert "strengths" in analysis
        assert "skill_gaps" in analysis
        assert analyze_resume.__doc__ is not None
