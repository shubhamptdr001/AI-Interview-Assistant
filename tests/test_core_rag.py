"""
tests/test_core_rag.py
----------------------
Unit tests for text chunking, vector indexing, and RAG retrieval.
"""

from unittest.mock import MagicMock
from core.rag import chunk_text, answer_resume_question, search_similar_chunks


class TestRAGCore:
    def test_chunk_text_basic(self):
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=5)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_text_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_search_similar_chunks_with_mock_vectorstore(self):
        mock_doc = MagicMock()
        mock_doc.page_content = "Python developer with LangChain experience."

        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [mock_doc]

        results = search_similar_chunks(mock_vs, query="Python skills", k=1)
        assert len(results) == 1
        assert "LangChain" in results[0]

    def test_answer_resume_question_mocked(self, mock_llm_response):
        mock_doc = MagicMock()
        mock_doc.page_content = "Candidate built microservices using Python and FastAPI."

        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = [mock_doc]

        res = answer_resume_question(mock_vs, "What backend frameworks does candidate know?", k=1)
        assert "answer" in res
        assert "sources" in res
        assert len(res["sources"]) == 1
        assert "FastAPI" in res["sources"][0]
