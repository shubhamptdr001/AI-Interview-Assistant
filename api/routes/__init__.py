"""
api routes package
"""
from api.routes.health import router as health_router
from api.routes.resume import router as resume_router
from api.routes.interview import router as interview_router

__all__ = ["health_router", "resume_router", "interview_router"]
