import pytest
from unittest.mock import patch, MagicMock

from documents.services.chroma_retriever import ChromaRetriever
from documents.services.types import RetrievalContext
from settings.utils import ApplicationError


class TestChromaRetriever:

    @pytest.fixture
    def mock_collection(self):
        return MagicMock()

    @pytest.fixture
    def retriever(self, mock_collection):
        return ChromaRetriever(mock_collection)

    def test_retrieve_for_topics_success(self, retriever, mock_collection):
        mock_collection.query.return_value = {
            "documents": [["doc1", "doc2"], ["doc3"]],
            "distances": [[0.1, 0.3], [0.2]],
        }

        results = retriever.retrieve_for_topics(
            topics=["Topic 1", "Topic 2"],
            max_results=3,
            max_distance=0.5,
        )

        assert "Topic 1" in results
        assert "Topic 2" in results
        assert isinstance(results["Topic 1"], RetrievalContext)
        assert results["Topic 1"].documents == ["doc1", "doc2"]
        assert results["Topic 2"].documents == ["doc3"]

    def test_retrieve_empty_topics(self, retriever):
        result = retriever.retrieve_for_topics(topics=[])
        assert result == {}

    def test_retrieve_with_doc_id_filter(self, retriever, mock_collection):
        mock_collection.query.return_value = {
            "documents": [["doc1"]],
            "distances": [[0.1]],
        }

        retriever.retrieve_for_topics(
            topics=["Topic 1"],
            max_results=3,
            max_distance=0.5,
            doc_id=42,
        )

        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["where"] == {"doc_id": "42"}

    def test_retrieve_filters_by_distance(self, retriever, mock_collection):
        mock_collection.query.return_value = {
            "documents": [["close_doc", "far_doc"]],
            "distances": [[0.1, 0.8]],
        }

        results = retriever.retrieve_for_topics(
            topics=["Topic 1"],
            max_results=5,
            max_distance=0.5,
        )

        assert results["Topic 1"].documents == ["close_doc"]
        assert results["Topic 1"].distances == [0.1]

    def test_retrieve_chroma_error(self, retriever, mock_collection):
        mock_collection.query.side_effect = Exception("Chroma error")

        with pytest.raises(ApplicationError):
            retriever.retrieve_for_topics(
                topics=["Topic 1"], max_results=3, max_distance=0.5
            )

    def test_build_query_kwargs_without_doc_id(self, retriever):
        kwargs = retriever._build_query_kwargs(
            topics=["T1", "T2"], max_results=3, doc_id=None
        )
        assert kwargs["query_texts"] == ["T1", "T2"]
        assert kwargs["n_results"] == 5  # max_results + 2
        assert "where" not in kwargs

    def test_build_query_kwargs_with_doc_id(self, retriever):
        kwargs = retriever._build_query_kwargs(topics=["T1"], max_results=3, doc_id=10)
        assert kwargs["where"] == {"doc_id": "10"}

    def test_validate_batch_response_valid(self, retriever):
        retriever._validate_batch_response(
            {
                "documents": [["d1"]],
                "distances": [[0.1]],
            }
        )

    def test_validate_batch_response_invalid(self, retriever):
        with pytest.raises(ValueError):
            retriever._validate_batch_response({})

        with pytest.raises(ValueError):
            retriever._validate_batch_response(None)

    def test_extract_topic_results_success(self, retriever):
        results = {
            "documents": [["d1", "d2"]],
            "distances": [[0.1, 0.2]],
        }
        docs, dists = retriever._extract_topic_results(results, 0)
        assert docs == ["d1", "d2"]
        assert dists == [0.1, 0.2]

    def test_extract_topic_results_invalid_index(self, retriever):
        results = {"documents": [["d1"]], "distances": [[0.1]]}
        docs, dists = retriever._extract_topic_results(results, 5)
        assert docs == []
        assert dists == []

    def test_filter_by_distance(self, retriever):
        docs, dists = retriever._filter_by_distance(
            docs=["d1", "d2", "d3"],
            dists=[0.1, 0.6, 0.2],
            max_results=5,
            max_distance=0.5,
        )
        assert docs == ["d1", "d3"]
        assert dists == [0.1, 0.2]

    def test_filter_by_distance_limits_results(self, retriever):
        docs, dists = retriever._filter_by_distance(
            docs=["d1", "d2", "d3"],
            dists=[0.1, 0.2, 0.3],
            max_results=2,
            max_distance=0.5,
        )
        assert len(docs) == 2
