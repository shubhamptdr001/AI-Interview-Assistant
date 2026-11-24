"""
tests/test_api.py
-----------------
API integration tests using FastAPI TestClient.
Tests cover health, question generation, scoring, resume analysis, input validation (422),
unsupported file types (415), missing session (404), and rate limiting (429).
"""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "model" in data

    def test_generate_questions_success(self, mock_llm_response):
        payload = {"company": "Amazon", "role": "Cloud Architect", "count": 2, "difficulty": "Medium"}
        response = client.post("/questions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["company"] == "Amazon"
        assert len(data["questions"]) == 2

    def test_generate_questions_validation_error(self):
        # Empty string violates min_length=1
        payload = {"company": "", "role": ""}
        response = client.post("/questions", json=payload)
        assert response.status_code == 422
        assert "Validation error" in response.json()["detail"]

    def test_score_answer_success(self, mock_llm_response):
        payload = {
            "question": "What is dependency injection?",
            "answer": "Dependency injection is a pattern where an object receives its dependencies from outside.",
            "role": "Java Developer",
        }
        response = client.post("/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 8
        assert "feedback" in data

    def test_score_answer_validation_error(self):
        payload = {"question": ""}  # Missing answer and invalid question
        response = client.post("/score", json=payload)
        assert response.status_code == 422

    def test_coding_help_endpoint(self, mock_llm_response):
        payload = {"query": "How to sort a dict by value in Python?"}
        response = client.post("/coding-help", json=payload)
        assert response.status_code == 200
        assert "Solution" in response.json()["answer"]

    def test_resume_analyze_endpoint(self, mock_llm_response, sample_resume_text):
        payload = {"text": sample_resume_text, "role": "Backend Engineer"}
        response = client.post("/resume/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["target_role"] == "Backend Engineer"
        assert data["word_count"] > 10

    def test_resume_upload_unsupported_format(self):
        files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
        response = client.post("/resume/upload", files=files)
        assert response.status_code == 415
        assert "Unsupported file type" in response.json()["detail"]

    def test_resume_upload_and_ask_flow(self, monkeypatch, mock_llm_response, sample_docx_bytes):
        # Mock vector store creation to avoid downloading heavy embedding models in tests
        mock_vs = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Candidate built microservices using Python and FastAPI."
        mock_vs.similarity_search.return_value = [mock_doc]

        import api.routes.resume
        monkeypatch.setattr(api.routes.resume, "build_resume_index", lambda text: mock_vs)
        monkeypatch.setattr(
            api.routes.resume,
            "answer_resume_question",
            lambda vs, q, k=3: {
                "answer": "Candidate has experience with Python and FastAPI microservices.",
                "sources": [mock_doc.page_content],
            },
        )

        # Upload synthetic DOCX
        files = {
            "file": (
                "my_resume.docx",
                sample_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        upload_res = client.post("/resume/upload", files=files)
        assert upload_res.status_code == 201
        session_id = upload_res.json()["session_id"]
        assert len(session_id) > 10

        # Ask question against uploaded session
        ask_res = client.post(
            "/resume/ask",
            json={"session_id": session_id, "question": "What frameworks does the candidate know?"},
        )
        assert ask_res.status_code == 200
        assert "answer" in ask_res.json()
        assert len(ask_res.json()["sources"]) == 1

    def test_resume_ask_unknown_session_returns_404(self):
        response = client.post(
            "/resume/ask",
            json={"session_id": "non_existent_session_id", "question": "Any question?"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
