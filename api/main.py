"""
api/main.py
------------
FastAPI application entrypoint for AI Interview Assistant.
Configures CORS, rate limiting, request logging, and error handlers.
"""

import logging
import time
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import settings
from api.routes import health_router, resume_router, interview_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")

# Initialize Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_PER_MINUTE],
)

app = FastAPI(
    title="AI Interview Assistant API",
    description=(
        "Production-ready REST API for AI Interview Preparation Assistant. "
        "Provides endpoints for resume parsing, RAG resume querying, question generation, "
        "mock interview scoring, and coding assistance powered by Groq LLMs."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- CORS Middleware ---
cors_origins: List[str] = (
    ["*"]
    if settings.CORS_ORIGINS == "*"
    else [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Timing & Access Logging Middleware ---
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{client_host} - '{request.method} {request.url.path}' {response.status_code} ({process_time:.2f}ms)"
        )
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        return response
    except Exception as exc:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"{client_host} - '{request.method} {request.url.path}' 500 ({process_time:.2f}ms) - Exception: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please try again later."},
        )


# --- Custom Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        errors.append({"field": loc, "message": err.get("msg", "Invalid input")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error in request parameters", "errors": errors},
    )


# --- Register Routers ---
app.include_router(health_router)
app.include_router(resume_router)
app.include_router(interview_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "AI Interview Assistant API is running.",
        "documentation": "/docs",
        "health": "/health",
    }
