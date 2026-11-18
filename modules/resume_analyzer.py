"""
modules/resume_analyzer.py
---------------------------
PDF/DOCX se text nikaalta hai aur skills match karta hai.
"""

import PyPDF2
import docx
from data.skills_bank import SKILLS_BANK


def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(uploaded_file):
    document = docx.Document(uploaded_file)
    text = "\n".join([para.text for para in document.paragraphs])
    return text


def extract_text(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return None


def extract_skills(resume_text):
    resume_text_lower = resume_text.lower()
    found_skills = []
    for skill in SKILLS_BANK:
        if skill.lower() in resume_text_lower:
            found_skills.append(skill)
    return found_skills


def get_word_count(resume_text):
    return len(resume_text.split())