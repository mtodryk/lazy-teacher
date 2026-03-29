import pytest
from unittest.mock import MagicMock, patch

from documents.services.quiz_generator import QuizGenerationService
from documents.services.types import QuestionData, RetrievalContext, LlmResponse
from settings.utils import ApplicationError


class TestQuizGenerationService:

    @pytest.fixture
    def mock_llm_client(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_llm_client):
        return QuizGenerationService(llm_client=mock_llm_client)

    @pytest.fixture
    def good_context(self):
        return RetrievalContext(
            documents=["Some relevant text about ML"],
            distances=[0.1],
        )

    def test_generate_from_context_success(
        self, service, mock_llm_client, good_context
    ):
        mock_llm_client.generate.return_value = LlmResponse(
            content='{"question": "What is ML?", "options": ["A", "B", "C", "D"], "correct_index": 0}'
        )
        mock_llm_client.parse_json_response.return_value = {
            "question": "What is ML?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 0,
        }

        result = service.generate_from_context(
            topic="Machine Learning",
            context=good_context,
            max_distance=0.5,
        )

        assert result is not None
        assert result.question == "What is ML?"
        assert len(result.options) == 4
        assert result.topic == "Machine Learning"
        assert result.used_chunks_count == 1

    def test_generate_from_context_invalid_data(
        self, service, mock_llm_client, good_context
    ):
        mock_llm_client.generate.return_value = LlmResponse(content="{}")
        mock_llm_client.parse_json_response.return_value = {}

        with pytest.raises(ApplicationError):
            service.generate_from_context(
                topic="ML", context=good_context, max_distance=0.5
            )

    def test_generate_from_context_missing_key(
        self, service, mock_llm_client, good_context
    ):
        mock_llm_client.generate.return_value = LlmResponse(content="{}")
        mock_llm_client.parse_json_response.return_value = {
            "question": "Q?",
            # missing options and correct_index
        }

        with pytest.raises(ApplicationError):
            service.generate_from_context(
                topic="ML", context=good_context, max_distance=0.5
            )

    def test_generate_uses_no_context_warning(self, service, mock_llm_client):
        context = RetrievalContext(
            documents=["text"],
            distances=[0.8],  # above max_distance
        )
        mock_llm_client.generate.return_value = LlmResponse(content="{}")
        mock_llm_client.parse_json_response.return_value = {
            "question": "Q?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 0,
        }

        service.generate_from_context(topic="ML", context=context, max_distance=0.5)

        call_args = mock_llm_client.generate.call_args
        user_prompt = call_args[1]["user_prompt"]
        assert "distance" in user_prompt.lower() or "0.5" in user_prompt

    def test_shuffle_options(self):
        question = QuestionData(
            question="Q?",
            options=["Correct", "Wrong1", "Wrong2", "Wrong3"],
            correct_index=0,
        )
        QuizGenerationService._shuffle_options(question)
        # After shuffle, correct_index should point to "Correct"
        assert question.options[question.correct_index] == "Correct"
        assert len(question.options) == 4

    def test_shuffle_options_preserves_all_options(self):
        original_options = ["A", "B", "C", "D"]
        question = QuestionData(
            question="Q?",
            options=original_options.copy(),
            correct_index=2,
        )
        QuizGenerationService._shuffle_options(question)
        assert sorted(question.options) == sorted(original_options)
        assert question.options[question.correct_index] == "C"
