"""
client/api_client.py
--------------------
HTTP client communicating with the FastAPI backend REST API.
Translates Streamlit UI interactions into backend API calls with graceful local fallbacks.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.getenv("API_TIMEOUT", "120.0"))


class APIClient:
    """Thin wrapper around httpx with local core fallback for robust performance."""

    def __init__(self, base_url: str = BACKEND_URL, timeout: float = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def check_health(self) -> Optional[Dict[str, Any]]:
        """Verify if backend API is reachable and healthy."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/health")
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return None

    def upload_resume(
        self,
        file_bytes: bytes,
        filename: str,
        index_for_rag: bool = False,
    ) -> Dict[str, Any]:
        """Upload resume via POST /resume/upload with optional immediate RAG indexing.

        Defaults to index_for_rag=False for instant (<100ms) parsing and analysis.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                files = {"file": (filename, file_bytes)}
                params = {"index_for_rag": "true" if index_for_rag else "false"}
                res = client.post(f"{self.base_url}/resume/upload", files=files, params=params)
                if res.status_code == 201:
                    return res.json()
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Upload failed ({res.status_code}): {detail}")
        except Exception as e:
            logger.warning(f"Backend upload error ({e}); falling back to local core parsing.")
            from core import parse_resume, extract_skills, get_word_count

            text = parse_resume(file_bytes, filename)
            skills = extract_skills(text)
            count = get_word_count(text)
            preview = text[:300].replace("\n", " ").strip() + ("..." if len(text) > 300 else "")
            return {
                "session_id": "local_fallback",
                "filename": filename,
                "word_count": count,
                "detected_skills": skills,
                "preview": preview,
                "text": text,
            }

    def ask_resume(
        self,
        question: str,
        session_id: Optional[str] = None,
        resume_text: Optional[str] = None,
        k: int = 3,
    ) -> Dict[str, Any]:
        """Query indexed resume via POST /resume/ask."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "question": question,
                "session_id": session_id,
                "resume_text": resume_text,
                "k": k,
            }
            res = client.post(f"{self.base_url}/resume/ask", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"RAG query failed ({res.status_code}): {detail}")
            return res.json()

    def analyze_resume(self, text: str, role: Optional[str] = None) -> Dict[str, Any]:
        """Analyze resume gaps and strengths via POST /resume/analyze with local fallback."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {"text": text, "role": role}
                res = client.post(f"{self.base_url}/resume/analyze", json=payload)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Backend analyze error ({e}); falling back to local core.")

        from core import analyze_resume as core_analyze

        return core_analyze(text, role=role)

    def generate_company_questions(
        self,
        company: str,
        role: str,
        count: int = 5,
        difficulty: str = "Medium",
    ) -> List[str]:
        """Generate targeted company questions via POST /questions with local fallback."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "company": company,
                    "role": role,
                    "count": count,
                    "difficulty": difficulty,
                }
                res = client.post(f"{self.base_url}/questions", json=payload)
                if res.status_code == 200:
                    return res.json().get("questions", [])
        except Exception as e:
            logger.warning(f"Backend questions error ({e}); falling back to local core.")

        from core import generate_questions as core_questions

        return core_questions(company, role, count, difficulty)

    def get_interview_question(
        self,
        role: str,
        difficulty: str = "Easy",
        previous_questions: Optional[List[str]] = None,
    ) -> str:
        """Fetch a single mock interview question via POST /interview/question with fallback."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "role": role,
                    "difficulty": difficulty,
                    "previous_questions": previous_questions or [],
                }
                res = client.post(f"{self.base_url}/interview/question", json=payload)
                if res.status_code == 200:
                    return res.json().get("question", "")
        except Exception as e:
            logger.warning(f"Backend single question error ({e}); falling back to local core.")

        from core import generate_interview_question as core_single_q

        return core_single_q(role, difficulty, previous_questions)

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        role: str = "Software Engineer",
    ) -> Dict[str, Any]:
        """Score candidate answer via POST /score with fallback."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {"question": question, "answer": answer, "role": role}
                res = client.post(f"{self.base_url}/score", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    if "correctness_percent" not in data:
                        data["correctness_percent"] = data.get("score", 5) * 10
                    return data
        except Exception as e:
            logger.warning(f"Backend evaluate error ({e}); falling back to local core.")

        from core import score_answer as core_score

        return core_score(question, answer, role)

    def get_coding_help(self, query: str) -> str:
        """Get coding help via POST /coding-help with fallback."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {"query": query}
                res = client.post(f"{self.base_url}/coding-help", json=payload)
                if res.status_code == 200:
                    return res.json().get("answer", "")
        except Exception as e:
            logger.warning(f"Backend coding help error ({e}); falling back to local core.")

        from core import get_coding_help as core_help

        return core_help(query)


# Global singleton
api_client = APIClient()
