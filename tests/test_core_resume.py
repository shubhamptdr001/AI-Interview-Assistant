"""
tests/test_core_resume.py
-------------------------
Unit tests for resume parsing, skill matching, word counts, and structured analysis.
"""

import pytest
from core.resume import parse_resume, extract_skills, get_word_count, analyze_resume


class TestResumeParsing:
    def test_parse_docx_success(self, sample_docx_bytes):
        text = parse_resume(sample_docx_bytes, "resume.docx")
        assert "John Doe" in text
        assert "Python" in text
        assert "FastAPI" in text

    def test_parse_empty_bytes_raises_error(self):
        with pytest.raises(ValueError, match="Resume file content is empty"):
            parse_resume(b"", "resume.pdf")

    def test_parse_unsupported_format_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_resume(b"sample bytes", "resume.exe")

    def test_extract_skills_precision(self):
        # Verify boundary matching: 'developer' should NOT trigger 'C' or 'R'
        text = "Experienced Python and SQL developer with Machine Learning in Docker."
        skills = extract_skills(text)
        assert "Python" in skills
        assert "SQL" in skills
        assert "Machine Learning" in skills
        assert "Docker" in skills
        assert "C" not in skills
        assert "R" not in skills

    def test_extract_skills_with_c_and_cpp(self):
        text = "Proficient in C++ and C programming."
        skills = extract_skills(text)
        assert "C++" in skills
        assert "C" in skills

    def test_get_word_count(self):
        assert get_word_count("") == 0
        assert get_word_count("Hello world from Python") == 4
        assert get_word_count("   One    two   three   ") == 3

    def test_analyze_resume_mocked(self, mock_llm_response, sample_resume_text):
        analysis = analyze_resume(sample_resume_text, role="Backend Engineer")
        assert analysis["target_role"] == "Backend Engineer"
        assert analysis["word_count"] > 10
        assert len(analysis["detected_skills"]) > 0
        assert "strengths" in analysis
        assert "skill_gaps" in analysis
        assert "actionable_recommendations" in analysis
        assert 0 <= analysis["estimated_match_score"] <= 100
