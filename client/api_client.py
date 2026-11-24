"""
client/api_client.py
--------------------
HTTP client communicating with the FastAPI backend REST API.
Translates Streamlit UI interactions into backend API calls.
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
TIMEOUT = float(os.getenv("API_TIMEOUT", "60.0"))


class APIClient:
    """Thin wrapper around httpx for interacting with the AI Interview Assistant API."""

    def __init__(self, base_url: str = BACKEND_URL, timeout: float = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def check_health(self) -> Optional[Dict[str, Any]]:
        """Verify if backend API is reachable and healthy."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/health")
                if res.status_code == 200:
                    return res.json()
        except Exception:
            pass
        return None

    def upload_resume(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Upload and index resume via POST /resume/upload."""
        with httpx.Client(timeout=self.timeout) as client:
            files = {"file": (filename, file_bytes)}
            res = client.post(f"{self.base_url}/resume/upload", files=files)
            if res.status_code != 201:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Upload failed ({res.status_code}): {detail}")
            return res.json()

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
        """Analyze resume gaps and strengths via POST /resume/analyze."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {"text": text, "role": role}
            res = client.post(f"{self.base_url}/resume/analyze", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Resume analysis failed ({res.status_code}): {detail}")
            return res.json()

    def generate_company_questions(
        self,
        company: str,
        role: str,
        count: int = 5,
        difficulty: str = "Medium",
    ) -> List[str]:
        """Generate targeted company questions via POST /questions."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "company": company,
                "role": role,
                "count": count,
                "difficulty": difficulty,
            }
            res = client.post(f"{self.base_url}/questions", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Question generation failed ({res.status_code}): {detail}")
            return res.json().get("questions", [])

    def get_interview_question(
        self,
        role: str,
        difficulty: str = "Easy",
        previous_questions: Optional[List[str]] = None,
    ) -> str:
        """Fetch a single mock interview question via POST /interview/question."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "role": role,
                "difficulty": difficulty,
                "previous_questions": previous_questions or [],
            }
            res = client.post(f"{self.base_url}/interview/question", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Failed to fetch interview question ({res.status_code}): {detail}")
            return res.json().get("question", "")

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        role: str = "Software Engineer",
    ) -> Tuple[int, str]:
        """Score candidate answer via POST /score."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {"question": question, "answer": answer, "role": role}
            res = client.post(f"{self.base_url}/score", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Scoring failed ({res.status_code}): {detail}")
            data = res.json()
            return data.get("score", 5), data.get("feedback", "")

    def get_coding_help(self, query: str) -> str:
        """Get coding help via POST /coding-help."""
        with httpx.Client(timeout=self.timeout) as client:
            payload = {"query": query}
            res = client.post(f"{self.base_url}/coding-help", json=payload)
            if res.status_code != 200:
                detail = res.json().get("detail", res.text)
                raise RuntimeError(f"Coding assistance failed ({res.status_code}): {detail}")
            return res.json().get("answer", "")


# Global singleton
api_client = APIClient()
