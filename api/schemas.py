"""
api/schemas.py
--------------
Pydantic v2 data models for API requests, responses, and validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# --- Health ---
class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="API health status")
    version: str = Field(default="1.0.0", description="API version")
    model: str = Field(..., description="Active Groq model name")
    prompt_version: str = Field(..., description="Active prompt templates version")


# --- Resume ---
class ResumeUploadResponse(BaseModel):
    session_id: str = Field(..., description="Unique identifier for uploaded resume session")
    filename: str = Field(..., description="Original filename uploaded")
    word_count: int = Field(..., description="Total word count in resume")
    detected_skills: List[str] = Field(default_factory=list, description="Skills detected from SKILLS_BANK")
    preview: str = Field(..., description="First 300 characters excerpt of extracted resume text")
    text: Optional[str] = Field(default="", description="Full extracted plain text from resume")


class ResumeAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Question about the resume")
    session_id: Optional[str] = Field(default=None, description="Active session ID from /resume/upload")
    resume_text: Optional[str] = Field(default=None, description="Optional raw resume text if no session_id")
    k: Optional[int] = Field(default=3, ge=1, le=10, description="Top-k context chunks to retrieve")


class ResumeAskResponse(BaseModel):
    answer: str = Field(..., description="AI response generated using RAG context")
    sources: List[str] = Field(default_factory=list, description="Text excerpts retrieved from resume")


class ResumeAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Plain text extracted from resume")
    role: Optional[str] = Field(default=None, max_length=150, description="Target job role")


class ResumeAnalyzeResponse(BaseModel):
    target_role: str
    word_count: int
    detected_skills: List[str]
    profile_summary: str
    strengths: List[str]
    skill_gaps: List[str]
    actionable_recommendations: List[str]
    estimated_match_score: int = Field(ge=0, le=100)


# --- Interview ---
class GenerateQuestionsRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=100, description="Target company")
    role: str = Field(..., min_length=1, max_length=100, description="Target job role")
    count: int = Field(default=5, ge=1, le=15, description="Number of questions to generate")
    difficulty: str = Field(default="Medium", description="Difficulty: Easy, Medium, or Hard")


class QuestionsResponse(BaseModel):
    company: str
    role: str
    questions: List[str]


class SingleQuestionRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=100, description="Target role")
    difficulty: str = Field(default="Easy", description="Difficulty: Easy, Medium, or Hard")
    previous_questions: List[str] = Field(default_factory=list, description="Already asked questions")


class SingleQuestionResponse(BaseModel):
    role: str
    difficulty: str
    question: str


class ScoreRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The interview question asked")
    answer: str = Field(..., min_length=1, description="Candidate's answer")
    role: str = Field(default="Software Engineer", max_length=100, description="Target role")


class ScoreResponse(BaseModel):
    score: int = Field(ge=1, le=10, description="Evaluation score between 1 and 10")
    feedback: str = Field(..., description="Actionable constructive evaluation feedback")


class CodingHelpRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=3000, description="Technical question or doubt")


class CodingHelpResponse(BaseModel):
    answer: str = Field(..., description="Explanation and code solution")
