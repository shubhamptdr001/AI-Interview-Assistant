"""
api/routes/resume.py
---------------------
Resume upload, RAG question answering, and role gap analysis endpoints.
"""

import logging
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from core.config import settings
from core import (
    parse_resume,
    extract_skills,
    get_word_count,
    analyze_resume,
    build_resume_index,
    answer_resume_question,
)
from api.schemas import (
    ResumeUploadResponse,
    ResumeAskRequest,
    ResumeAskResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
)
from api.state import session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index resume (PDF or DOCX)",
)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file, parse text, extract skills, and construct an in-memory RAG index."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must be provided.",
        )

    # Validate file extension
    lower_name = file.filename.lower()
    if not any(lower_name.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Read bytes and validate size
    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Parse resume text
    try:
        text = parse_resume(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    word_count = get_word_count(text)
    detected_skills = extract_skills(text)

    # Build RAG vector index
    try:
        vector_store = build_resume_index(text)
    except Exception as e:
        logger.error(f"Failed to build vector index: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index resume for search: {str(e)}",
        )

    # Register in in-memory session store
    session_id = session_store.create_session(
        vector_store=vector_store,
        text=text,
        filename=file.filename,
        word_count=word_count,
        skills=detected_skills,
    )

    preview_text = text[:300].replace("\n", " ").strip() + ("..." if len(text) > 300 else "")

    return ResumeUploadResponse(
        session_id=session_id,
        filename=file.filename,
        word_count=word_count,
        detected_skills=detected_skills,
        preview=preview_text,
    )


@router.post(
    "/ask",
    response_model=ResumeAskResponse,
    summary="Ask a question about a resume using RAG",
)
async def ask_resume(payload: ResumeAskRequest):
    """Retrieve relevant excerpts from the indexed resume and generate an AI answer."""
    vector_store = None

    # Retrieve from session store if session_id provided
    if payload.session_id:
        session = session_store.get_session(payload.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{payload.session_id}' not found or has expired. Please re-upload.",
            )
        vector_store = session["vector_store"]
    elif payload.resume_text:
        try:
            vector_store = build_resume_index(payload.resume_text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not index raw text: {str(e)}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'session_id' or 'resume_text' must be provided.",
        )

    try:
        rag_result = answer_resume_question(vector_store, payload.question, k=payload.k)
        return ResumeAskResponse(
            answer=rag_result["answer"],
            sources=rag_result["sources"],
        )
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )


@router.post(
    "/analyze",
    response_model=ResumeAnalyzeResponse,
    summary="Comprehensive resume evaluation and skill gap analysis",
)
async def analyze_resume_endpoint(payload: ResumeAnalyzeRequest):
    """Analyze resume text against a target job role, generating strengths, gaps, and recommendations."""
    try:
        result = analyze_resume(payload.text, role=payload.role)
        return ResumeAnalyzeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume analysis error: {str(e)}",
        )
