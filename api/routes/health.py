"""
api/routes/health.py
---------------------
Health check and diagnostic endpoint.
"""

from fastapi import APIRouter
from core.config import settings
from core.prompts import PROMPT_VERSION
from api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns the operational status, active LLM model, and prompt version."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model=settings.GROQ_MODEL,
        prompt_version=PROMPT_VERSION,
    )
