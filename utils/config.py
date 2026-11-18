"""
utils/config.py
----------------
Ye file .env se saari settings/keys load karti hai.
Aage jitni bhi files ko API key chahiye hogi, wo yahan se import karengi
taaki har jagah alag se load_dotenv() na likhna pade.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Phase 4 mein ye keys use hongi
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# App-level constants
APP_NAME = "AI Interview Assistant"
UPLOAD_DIR = "uploads"
VECTOR_DB_DIR = "vector_db"
DATA_DIR = "data"
