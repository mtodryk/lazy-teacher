import pytest
import json
from unittest.mock import patch, MagicMock

from documents.services.topic_extraction import (
    extract_topics,
    _parse_topics,
    generate_rag_quiz,
)
from documents.services.types import LlmResponse, QuizData
from settings.utils import ApplicationError


class TestParseTopics:

    def test_valid_json(self):
        raw = '{"topics": ["Topic 1", "Topic 2", "Topic 3"]}'
        result = _parse_topics(raw)
        assert result == ["Topic 1", "Topic 2", "Topic 3"]

    def test_invalid_json(self):
        with pytest.raises(ApplicationError) as exc_info:
            _parse_topics("not json")
        assert "Invalid JSON" in exc_info.value.message

    def test_missing_topics_key(self):
        with pytest.raises(ApplicationError) as exc_info:
            _parse_topics('{"data": ["a"]}')
        assert "Missing 'topics' key" in exc_info.value.message

    def test_topics_not_list(self):
        with pytest.raises(ApplicationError) as exc_info:
            _parse_topics('{"topics": "not a list"}')
        assert "list of strings" in exc_info.value.message

    def test_topics_not_strings(self):
        with pytest.raises(ApplicationError) as exc_info:
            _parse_topics('{"topics": [1, 2, 3]}')
        assert "list of strings" in exc_info.value.message

    def test_empty_topics_list(self):
        result = _parse_topics('{"topics": []}')
        assert result == []

    def test_topics_not_dict(self):
        with pytest.raises(ApplicationError):
            _parse_topics('["topic1", "topic2"]')


class TestExtractTopics:

    def test_extract_topics_success(self, mocker):
        mock_client = MagicMock()
        mock_client.generate.return_value = LlmResponse(
            content='{"topics": ["ML", "AI"]}'
        )
        mocker.patch(
            "documents.services.topic_extraction.AzureLlmClient",
            return_value=mock_client,
        )

        result = extract_topics(["chunk1", "chunk2"])
        assert result == ["ML", "AI"]

    def test_extract_topics_passes_chunks(self, mocker):
        mock_client = MagicMock()
        mock_client.generate.return_value = LlmResponse(content='{"topics": ["T1"]}')
        mocker.patch(
            "documents.services.topic_extraction.AzureLlmClient",
            return_value=mock_client,
        )

        chunks = ["chunk 1 text", "chunk 2 text"]
        extract_topics(chunks)

        call_kwargs = mock_client.generate.call_args[1]
        assert "chunk 1 text" in call_kwargs["user_prompt"]
        assert "chunk 2 text" in call_kwargs["user_prompt"]


class TestGenerateRagQuiz:

    @pytest.fixture
    def mock_deps(self, mocker):
        mock_service = MagicMock()
        mocker.patch(
            "documents.services.topic_extraction.QuizGenerationService",
            return_value=mock_service,
        )
        mocker.patch(
            "documents.services.topic_extraction.AzureLlmClient",
        )
        mock_retriever = MagicMock()
        mocker.patch(
            "documents.services.topic_extraction.ChromaRetriever",
            return_value=mock_retriever,
        )
        return mock_service, mock_retriever

    def test_generate_quiz_success(self, mock_deps):
        service, retriever = mock_deps
        from documents.services.types import QuestionData, RetrievalContext

        context = RetrievalContext(documents=["text"], distances=[0.1])
        retriever.retrieve_for_topics.return_value = {"Topic 1": context}

        question = QuestionData(
            question="Q?",
            options=["A", "B", "C", "D"],
            correct_index=0,
            topic="Topic 1",
        )
        service.generate_from_context.return_value = question

        result = generate_rag_quiz(
            topics=["Topic 1"],
            count=1,
            collection=MagicMock(),
        )

        assert len(result) == 1
        assert result[0]["question"] == "Q?"

    def test_generate_quiz_multiple_topics_cycled(self, mock_deps):
        service, retriever = mock_deps
        from documents.services.types import QuestionData, RetrievalContext

        context = RetrievalContext(documents=["text"], distances=[0.1])
        retriever.retrieve_for_topics.return_value = {
            "T1": context,
            "T2": context,
        }

        question = QuestionData(
            question="Q?",
            options=["A", "B", "C", "D"],
            correct_index=0,
        )
        service.generate_from_context.return_value = question

        result = generate_rag_quiz(
            topics=["T1", "T2"],
            count=4,
            collection=MagicMock(),
        )

        assert len(result) == 4

    def test_generate_quiz_skips_failed_questions(self, mock_deps):
        service, retriever = mock_deps
        from documents.services.types import RetrievalContext

        context = RetrievalContext(documents=["text"], distances=[0.1])
        retriever.retrieve_for_topics.return_value = {"T1": context}

        service.generate_from_context.side_effect = ApplicationError("Failed")

        result = generate_rag_quiz(
            topics=["T1"],
            count=3,
            collection=MagicMock(),
        )

        assert result == []

    def test_generate_quiz_skips_missing_topics(self, mock_deps):
        service, retriever = mock_deps

        retriever.retrieve_for_topics.return_value = {}

        result = generate_rag_quiz(
            topics=["T1"],
            count=1,
            collection=MagicMock(),
        )

        assert result == []
        service.generate_from_context.assert_not_called()
