"""
mcp_server/server.py
--------------------
Model Context Protocol (MCP) Server for AI Interview Assistant.
Exposes interview preparation and resume evaluation tools to external LLM clients
(e.g., Claude Desktop, Cursor) over standard input/output (stdio).

Zero duplicated logic: tools delegate strictly to core functions.
"""

import sys
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

from core import (
    generate_questions as core_generate_questions,
    score_answer as core_score_answer,
    analyze_resume as core_analyze_resume,
)

# Initialize FastMCP Server
mcp = FastMCP("AI-Interview-Assistant")


@mcp.tool()
def generate_questions(
    company: str,
    role: str,
    count: int = 5,
    difficulty: str = "Medium",
) -> List[str]:
    """Generate company-specific and role-specific technical and behavioral interview questions.

    Use this tool when the user wants to practice realistic interview questions tailored
    to a specific target company (e.g. 'Google', 'Amazon', 'TCS') and job role
    (e.g. 'Full-Stack Developer', 'AI Engineer').

    Args:
        company: The target employer company name (e.g., 'Google', 'Meta', 'TCS').
        role: The target professional role (e.g., 'Backend Engineer', 'Data Scientist').
        count: The number of questions to generate (default 5, maximum 15).
        difficulty: The target difficulty level. Choose from 'Easy', 'Medium', or 'Hard'.

    Returns:
        A list of generated interview question strings categorized by question type.
    """
    return core_generate_questions(
        company=company,
        role=role,
        count=count,
        difficulty=difficulty,
    )


@mcp.tool()
def score_answer(
    question: str,
    answer: str,
    role: str = "Software Engineer",
) -> Dict[str, Any]:
    """Evaluate and score a candidate's answer to a technical or behavioral interview question.

    Use this tool to evaluate mock interview responses. It provides a numerical rating
    from 1 to 10 along with constructive, actionable feedback highlighting what was done well
    and specific areas for improvement.

    Args:
        question: The exact interview question that was asked.
        answer: The candidate's submitted response.
        role: The professional job role being interviewed for (default 'Software Engineer').

    Returns:
        A dictionary with:
        - 'score': Integer from 1 to 10 evaluating answer completeness and technical accuracy.
        - 'feedback': Detailed constructive feedback with critique and improvement suggestions.
    """
    return core_score_answer(
        question=question,
        answer=answer,
        role=role,
    )


@mcp.tool()
def analyze_resume(
    resume_text: str,
    role: str = "Software Engineer",
) -> Dict[str, Any]:
    """Perform a deep structural and skill-gap evaluation of a candidate's resume text.

    Use this tool when the user provides resume text and wants to understand how well
    it matches a target role, what skills were detected, strengths, and missing skill gaps.

    Args:
        resume_text: Plain text content extracted from the candidate's resume.
        role: The target position to evaluate the resume against (e.g., 'Cloud Architect').

    Returns:
        A dictionary containing:
        - 'target_role': Evaluated role title.
        - 'word_count': Total word count in resume text.
        - 'detected_skills': List of recognized technical and soft skills.
        - 'profile_summary': Professional summary of the candidate's background.
        - 'strengths': List of highlighted strong points in the profile.
        - 'skill_gaps': List of missing skills or domain gaps for the target role.
        - 'actionable_recommendations': Concrete steps to improve the resume.
        - 'estimated_match_score': An alignment score from 1 to 100.
    """
    return core_analyze_resume(
        text=resume_text,
        role=role,
    )


if __name__ == "__main__":
    # Run the MCP server over standard input/output (stdio)
    mcp.run(transport="stdio")
