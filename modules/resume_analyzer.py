"""
modules/resume_analyzer.py
---------------------------
Backward-compatibility adapter forwarding to core.resume.
"""

from core.resume import (
    parse_resume,
    extract_skills,
    get_word_count,
    analyze_resume,
)


def extract_text(uploaded_file):
    """Backward-compatible wrapper for Streamlit uploaded file objects."""
    if uploaded_file is None:
        return None
    try:
        # Check if already bytes
        if isinstance(uploaded_file, bytes):
            return parse_resume(uploaded_file, "resume.pdf")

        # Streamlit UploadedFile has getbuffer(), getvalue(), or read()
        if hasattr(uploaded_file, "getvalue"):
            file_bytes = uploaded_file.getvalue()
        elif hasattr(uploaded_file, "read"):
            file_bytes = uploaded_file.read()
        else:
            return None

        filename = getattr(uploaded_file, "name", "resume.pdf")
        return parse_resume(file_bytes, filename)
    except Exception:
        return None


__all__ = [
    "extract_text",
    "extract_skills",
    "get_word_count",
    "analyze_resume",
    "parse_resume",
]
