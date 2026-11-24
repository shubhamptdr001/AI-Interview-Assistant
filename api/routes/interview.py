"""
api/routes/interview.py
------------------------
Interview question generation, candidate answer evaluation, and coding help endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from core import (
    generate_questions,
    generate_interview_question,
    score_answer,
    get_coding_help,
)
from api.schemas import (
    GenerateQuestionsRequest,
    QuestionsResponse,
    SingleQuestionRequest,
    SingleQuestionResponse,
    ScoreRequest,
    ScoreResponse,
    CodingHelpRequest,
    CodingHelpResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Interview"])


@router.post(
    "/questions",
    response_model=QuestionsResponse,
    summary="Generate company-specific interview questions",
)
async def get_company_questions(payload: GenerateQuestionsRequest):
    """Generate realistic technical and behavioral interview questions for a specified company and role."""
    try:
        questions = generate_questions(
            company=payload.company,
            role=payload.role,
            count=payload.count,
            difficulty=payload.difficulty,
        )
        return QuestionsResponse(
            company=payload.company,
            role=payload.role,
            questions=questions,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Question generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question generation error: {str(e)}",
        )


@router.post(
    "/interview/question",
    response_model=SingleQuestionResponse,
    summary="Generate a single mock interview question",
)
async def get_single_question(payload: SingleQuestionRequest):
    """Generate a single fresh interview question for a mock interview round."""
    try:
        q = generate_interview_question(
            role=payload.role,
            difficulty=payload.difficulty,
            previous_questions=payload.previous_questions,
        )
        return SingleQuestionResponse(
            role=payload.role,
            difficulty=payload.difficulty,
            question=q,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Single question generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating question: {str(e)}",
        )


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score and provide constructive feedback on candidate answer",
)
async def evaluate_answer(payload: ScoreRequest):
    """Score a candidate's answer (1-10) and generate constructive, actionable feedback."""
    try:
        result = score_answer(
            question=payload.question,
            answer=payload.answer,
            role=payload.role,
        )
        return ScoreResponse(
            score=result["score"],
            correctness_percent=result.get("correctness_percent", result["score"] * 10),
            what_was_good=result.get("what_was_good", ""),
            what_is_missing=result.get("what_is_missing", ""),
            feedback=result["feedback"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Answer scoring failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring error: {str(e)}",
        )


@router.post(
    "/coding-help",
    response_model=CodingHelpResponse,
    summary="Get coding assistance, concept explanations, and commented code",
)
async def coding_assistance(payload: CodingHelpRequest):
    """Answer coding doubts and DSA concepts with simple explanations and commented code."""
    try:
        answer = get_coding_help(payload.query)
        return CodingHelpResponse(answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Coding assistance failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coding help error: {str(e)}",
        )
