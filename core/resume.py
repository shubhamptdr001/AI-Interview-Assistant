"""
core/resume.py
--------------
Pure Python resume parsing, skill extraction, and resume analysis functions.
No UI dependencies.
"""

import io
import json
import logging
import re
from typing import Any, Dict, List, Optional

from data.skills_bank import SKILLS_BANK
from core.prompts import RESUME_ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


def parse_resume(file_bytes: bytes, filename: str) -> str:
    """Extract clean text content from PDF or DOCX file bytes.

    Args:
        file_bytes: Binary content of the resume file.
        filename: Name of the file, used to determine extension.

    Returns:
        Extracted plain text from the resume.

    Raises:
        ValueError: If file format is unsupported or file content is empty/corrupt.
        ImportError: If required parsing library is not installed.
    """
    if not file_bytes:
        raise ValueError("Resume file content is empty.")

    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        try:
            import PyPDF2
        except ImportError as e:
            raise ImportError(
                "PyPDF2 package is required to parse PDF resumes. Install via 'pip install PyPDF2'."
            ) from e

        try:
            stream = io.BytesIO(file_bytes)
            reader = PyPDF2.PdfReader(stream)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text.strip())
            full_text = "\n\n".join(filter(None, extracted_pages))
            if not full_text.strip():
                raise ValueError("Could not extract any text from PDF. The file may be scanned or empty.")
            return full_text
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to parse PDF document: {str(e)}") from e

    elif lower_name.endswith(".docx"):
        try:
            import docx
        except ImportError as e:
            raise ImportError(
                "python-docx package is required to parse DOCX resumes. Install via 'pip install python-docx'."
            ) from e

        try:
            stream = io.BytesIO(file_bytes)
            doc = docx.Document(stream)
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            full_text = "\n".join(paragraphs)
            if not full_text.strip():
                raise ValueError("Could not extract text from DOCX file. File appears empty.")
            return full_text
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to parse DOCX document: {str(e)}") from e

    else:
        raise ValueError(
            f"Unsupported file format '{filename}'. Allowed formats: .pdf, .docx"
        )


def extract_skills(text: str, custom_skills: Optional[List[str]] = None) -> List[str]:
    """Identify matching technical and soft skills in resume text against SKILLS_BANK.

    Uses boundary-aware regex matching to avoid false positives (e.g., 'C' in 'developer').

    Args:
        text: Raw resume text.
        custom_skills: Optional list of additional skills to check.

    Returns:
        List of unique matched skill names in their original casing.
    """
    if not text:
        return []

    target_bank = list(SKILLS_BANK)
    if custom_skills:
        target_bank.extend(custom_skills)

    matched = []
    for skill in target_bank:
        if skill.upper() == "C":
            pattern = r"(?<![A-Za-z0-9])C(?![A-Za-z0-9+#])"
        else:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"

        if re.search(pattern, text, re.IGNORECASE):
            matched.append(skill)

    # Return deduplicated preserving order
    seen = set()
    return [s for s in matched if not (s in seen or seen.add(s))]


def get_word_count(text: str) -> int:
    """Return the total word count in a text string.

    Args:
        text: Input string.

    Returns:
        Number of whitespace-delimited words.
    """
    if not text:
        return 0
    return len(text.split())


def analyze_resume(text: str, role: Optional[str] = None) -> Dict[str, Any]:
    """Perform a structured evaluation of resume content against an optional target role.

    Combines deterministic heuristics (word count, detected skills) with LLM insights.

    Args:
        text: Parsed resume text.
        role: Targeted job role (e.g., 'Full-Stack Developer', 'AI Engineer').

    Returns:
        Dictionary containing structured metrics, strengths, gaps, and recommendations.
    """
    if not text or not text.strip():
        raise ValueError("Resume text cannot be empty.")

    target_role = role.strip() if role and role.strip() else "General Software / Tech Role"
    skills = extract_skills(text)
    word_count = get_word_count(text)

    # Fallback heuristic analysis
    fallback_analysis: Dict[str, Any] = {
        "target_role": target_role,
        "word_count": word_count,
        "detected_skills": skills,
        "profile_summary": f"Resume with {word_count} words and {len(skills)} detected skills in {target_role}.",
        "strengths": [
            f"Detected {len(skills)} relevant technical competencies ({', '.join(skills[:5]) if skills else 'Basic profile'}).",
            "Structured document with parseable sections.",
        ],
        "skill_gaps": [
            "Consider adding measurable business impact metrics (e.g., % improvement, scale)."
        ],
        "actionable_recommendations": [
            "Highlight core projects aligning specifically to " + target_role,
            "Include technical stack tags and system architecture highlights.",
        ],
        "estimated_match_score": min(90, max(40, len(skills) * 8)),
    }

    # Attempt LLM enhanced analysis if client/key is available
    try:
        from core.llm import ask_llm

        prompt = RESUME_ANALYSIS_PROMPT_TEMPLATE.format(
            role=target_role,
            resume_text=text[:3500],  # Guard token length
            detected_skills=", ".join(skills) if skills else "None detected",
        )
        llm_raw = ask_llm(prompt, max_tokens=800)

        # Parse JSON from LLM response
        cleaned_json = llm_raw.strip()
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
        elif "```" in cleaned_json:
            cleaned_json = cleaned_json.split("```")[-1].split("```")[0].strip()

        parsed = json.loads(cleaned_json)
        # Augment with deterministic metrics
        parsed["word_count"] = word_count
        parsed["detected_skills"] = skills
        if "target_role" not in parsed:
            parsed["target_role"] = target_role
        return parsed
    except Exception as e:
        logger.warning(f"LLM analysis fallback used due to: {e}")
        return fallback_analysis
