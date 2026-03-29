import pytest
from unittest.mock import patch, MagicMock

from documents.services.rag import retrieve_chunks
from documents.services.vector_store import SearchResult


class TestRetrieveChunks:

    def test_retrieve_chunks_calls_store(self, mocker):
        mock_store = MagicMock()
        mock_store.search.return_value = [
            SearchResult(text="chunk1", chunk_idx=0, distance=0.1, source="doc.pdf"),
        ]
        mocker.patch(
            "documents.services.rag.ChromaVectorStore",
            return_value=mock_store,
        )

        results = retrieve_chunks(query="test query", doc_id=1, user_id=2, n_results=5)

        assert len(results) == 1
        assert results[0].text == "chunk1"
        mock_store.search.assert_called_once_with(
            query="test query",
            n_results=5,
            where={"doc_id": "1", "user_id": "2"},
        )

    def test_retrieve_chunks_converts_ids_to_str(self, mocker):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        mocker.patch(
            "documents.services.rag.ChromaVectorStore",
            return_value=mock_store,
        )

        retrieve_chunks(query="q", doc_id=42, user_id=7)

        call_kwargs = mock_store.search.call_args[1]
        assert call_kwargs["where"] == {"doc_id": "42", "user_id": "7"}

    def test_retrieve_chunks_default_n_results(self, mocker):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        mocker.patch(
            "documents.services.rag.ChromaVectorStore",
            return_value=mock_store,
        )

        retrieve_chunks(query="q", doc_id=1, user_id=1)

        call_kwargs = mock_store.search.call_args[1]
        assert call_kwargs["n_results"] == 5

    def test_retrieve_chunks_empty_results(self, mocker):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        mocker.patch(
            "documents.services.rag.ChromaVectorStore",
            return_value=mock_store,
        )

        results = retrieve_chunks(query="nothing", doc_id=1, user_id=1)
        assert results == []
