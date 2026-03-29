import pytest
from unittest.mock import patch, MagicMock

from documents.services.vector_store import ChromaVectorStore, SearchResult


class TestSearchResult:

    def test_create_search_result(self):
        result = SearchResult(
            text="Sample text",
            chunk_idx=0,
            distance=0.15,
            source="doc.pdf",
        )
        assert result.text == "Sample text"
        assert result.chunk_idx == 0
        assert result.distance == 0.15
        assert result.source == "doc.pdf"
        assert result.metadata == {}

    def test_create_with_metadata(self):
        result = SearchResult(
            text="Text",
            chunk_idx=1,
            distance=0.2,
            source="doc.pdf",
            metadata={"user_id": "1", "doc_id": "2"},
        )
        assert result.metadata == {"user_id": "1", "doc_id": "2"}


class TestChromaVectorStoreBuildWhere:

    def test_build_where_none(self):
        result = ChromaVectorStore._build_where(None)
        assert result is None

    def test_build_where_empty(self):
        result = ChromaVectorStore._build_where({})
        assert result is None

    def test_build_where_single_filter(self):
        result = ChromaVectorStore._build_where({"doc_id": "1"})
        assert result == {"doc_id": "1"}

    def test_build_where_multiple_filters(self):
        result = ChromaVectorStore._build_where({"doc_id": "1", "user_id": "2"})
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"doc_id": "1"} in conditions
        assert {"user_id": "2"} in conditions


class TestChromaVectorStoreOperations:

    @pytest.fixture
    def mock_store(self, mocker):
        mocker.patch("documents.services.vector_store.get_chroma_collection")
        mocker.patch("documents.services.vector_store.get_embedding_function")
        store = ChromaVectorStore()
        return store

    def test_add_documents(self, mock_store):
        mock_store._collection = MagicMock()
        documents = ["doc1", "doc2"]
        ids = ["id1", "id2"]
        metadatas = [{"k": "v1"}, {"k": "v2"}]

        mock_store.add_documents(documents, ids, metadatas)
        mock_store._collection.add.assert_called_once()

    def test_add_documents_batched(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store.BATCH_SIZE = 2

        documents = ["d1", "d2", "d3", "d4", "d5"]
        ids = ["i1", "i2", "i3", "i4", "i5"]
        metadatas = [{"k": str(i)} for i in range(5)]

        mock_store.add_documents(documents, ids, metadatas)
        assert mock_store._collection.add.call_count == 3

    def test_delete_with_filter(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store.delete(where={"doc_id": "1"})
        mock_store._collection.delete.assert_called_once_with(where={"doc_id": "1"})

    def test_delete_empty_filter(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store.delete(where={})
        mock_store._collection.delete.assert_not_called()

    def test_search_returns_results(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._embed = MagicMock(return_value=[[0.1, 0.2]])
        mock_store._collection.query.return_value = {
            "documents": [["text1", "text2"]],
            "metadatas": [
                [
                    {"chunk_idx": 0, "source": "doc.pdf"},
                    {"chunk_idx": 1, "source": "doc.pdf"},
                ]
            ],
            "distances": [[0.1, 0.3]],
        }

        results = mock_store.search("test query", n_results=2)
        assert len(results) == 2
        assert results[0].text == "text1"
        assert results[0].distance == 0.1
        assert results[1].text == "text2"

    def test_search_empty_results(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._embed = MagicMock(return_value=[[0.1]])
        mock_store._collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        results = mock_store.search("test")
        assert results == []

    def test_search_no_documents(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._embed = MagicMock(return_value=[[0.1]])
        mock_store._collection.query.return_value = {
            "documents": None,
            "metadatas": None,
            "distances": None,
        }

        results = mock_store.search("test")
        assert results == []

    def test_search_with_where_filter(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._embed = MagicMock(return_value=[[0.1]])
        mock_store._collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        mock_store.search("test", where={"doc_id": "1"})
        call_kwargs = mock_store._collection.query.call_args[1]
        assert call_kwargs["where"] == {"doc_id": "1"}

    def test_get_all_documents(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._collection.get.return_value = {
            "documents": ["chunk2", "chunk1", "chunk3"],
            "metadatas": [
                {"chunk_idx": 1},
                {"chunk_idx": 0},
                {"chunk_idx": 2},
            ],
        }

        results = mock_store.get_all_documents()
        assert results == ["chunk1", "chunk2", "chunk3"]

    def test_get_all_documents_empty(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._collection.get.return_value = {
            "documents": [],
            "metadatas": [],
        }

        results = mock_store.get_all_documents()
        assert results == []

    def test_get_all_documents_with_filter(self, mock_store):
        mock_store._collection = MagicMock()
        mock_store._collection.get.return_value = {
            "documents": ["text"],
            "metadatas": [{"chunk_idx": 0}],
        }

        mock_store.get_all_documents(where={"doc_id": "1"})
        call_kwargs = mock_store._collection.get.call_args[1]
        assert call_kwargs["where"] == {"doc_id": "1"}
