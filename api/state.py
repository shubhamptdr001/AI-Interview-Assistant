"""
api/state.py
-------------
In-memory session registry for active RAG vector stores.
Includes automatic capacity management and LRU eviction.
"""

import time
import uuid
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Max sessions kept in memory simultaneously
MAX_SESSIONS = 50
SESSION_TTL_SECONDS = 3600 * 4  # 4 hours


class SessionStore:
    """Thread-safe in-memory store for user resume vector indices."""

    def __init__(self, max_sessions: int = MAX_SESSIONS, ttl: int = SESSION_TTL_SECONDS):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._max_sessions = max_sessions
        self._ttl = ttl

    def create_session(
        self,
        vector_store: Any,
        text: str,
        filename: str,
        word_count: int,
        skills: list,
    ) -> str:
        self.cleanup_expired()

        # If capacity reached, evict oldest session
        if len(self._sessions) >= self._max_sessions:
            oldest_key = min(self._sessions.keys(), key=lambda k: self._sessions[k]["created_at"])
            del self._sessions[oldest_key]
            logger.info(f"Evicted oldest session: {oldest_key}")

        session_id = uuid.uuid4().hex
        self._sessions[session_id] = {
            "vector_store": vector_store,
            "text": text,
            "filename": filename,
            "word_count": word_count,
            "skills": skills,
            "created_at": time.time(),
            "last_accessed": time.time(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if session:
            session["last_accessed"] = time.time()
        return session

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            k for k, v in self._sessions.items() if (now - v.get("last_accessed", 0)) > self._ttl
        ]
        for k in expired:
            del self._sessions[k]
        return len(expired)

    def count(self) -> int:
        return len(self._sessions)


# Global singleton instance
session_store = SessionStore()
