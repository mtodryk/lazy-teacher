import pytest
from unittest.mock import patch, MagicMock

from documents.services.llm_client import AzureLlmClient
from documents.services.types import LlmResponse
from settings.utils import ApplicationError


class TestAzureLlmClient:

    @pytest.fixture
    def mock_settings(self, mocker):
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_ENDPOINT",
            "https://test.openai.azure.com",
        )
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_API_KEY", "test-key"
        )
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_DEPLOYMENT", "gpt-4o"
        )
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_API_VERSION",
            "2024-12-01",
        )

    @pytest.fixture
    def mock_openai(self, mocker):
        return mocker.patch("documents.services.llm_client.AzureOpenAI")

    def test_init_with_valid_credentials(self, mock_settings, mock_openai):
        client = AzureLlmClient()
        assert client.endpoint == "https://test.openai.azure.com"
        assert client.api_key == "test-key"
        assert client.deployment == "gpt-4o"

    def test_init_missing_credentials(self, mocker):
        mocker.patch("documents.services.llm_client.settings.AZURE_OPENAI_ENDPOINT", "")
        mocker.patch("documents.services.llm_client.settings.AZURE_OPENAI_API_KEY", "")
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_DEPLOYMENT", "gpt-4o"
        )
        mocker.patch(
            "documents.services.llm_client.settings.AZURE_OPENAI_API_VERSION",
            "2024-12-01",
        )

        with pytest.raises(ValueError):
            AzureLlmClient()

    def test_generate_success(self, mock_settings, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Generated response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        client = AzureLlmClient()
        result = client.generate(
            system_prompt="You are helpful",
            user_prompt="Hello",
        )

        assert isinstance(result, LlmResponse)
        assert result.content == "Generated response"

    def test_generate_api_error(self, mock_settings, mock_openai):
        mock_openai.return_value.chat.completions.create.side_effect = Exception(
            "API Error"
        )

        client = AzureLlmClient()
        with pytest.raises(ApplicationError) as exc_info:
            client.generate(system_prompt="sys", user_prompt="user")
        assert "LLM generation failed" in str(exc_info.value.message)

    def test_generate_passes_params(self, mock_settings, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        client = AzureLlmClient()
        client.generate(
            system_prompt="sys",
            user_prompt="user",
            temperature=0.5,
            max_tokens=1000,
        )

        call_kwargs = mock_openai.return_value.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 1000
        assert call_kwargs["model"] == "gpt-4o"

    def test_parse_json_response_valid(self, mock_settings, mock_openai):
        client = AzureLlmClient()
        response = LlmResponse(content='{"key": "value"}')
        result = client.parse_json_response(response)
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self, mock_settings, mock_openai):
        client = AzureLlmClient()
        response = LlmResponse(content="not json")
        with pytest.raises(ApplicationError) as exc_info:
            client.parse_json_response(response)
        assert "Invalid JSON" in str(exc_info.value.message)

    def test_parse_json_response_with_markdown(self, mock_settings, mock_openai):
        client = AzureLlmClient()
        response = LlmResponse(content='```json\n{"key": "value"}\n```')
        result = client.parse_json_response(response)
        assert result == {"key": "value"}
