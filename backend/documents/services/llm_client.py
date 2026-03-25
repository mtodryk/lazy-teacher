import json
import logging

from django.conf import settings
from openai import AzureOpenAI

from .types import LlmResponse
from settings.utils import ApplicationError

logger = logging.getLogger(__name__)


class AzureLlmClient:
    def __init__(self) -> None:
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.api_version = settings.AZURE_OPENAI_API_VERSION

        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI credentials not configured. ")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 800,
    ) -> LlmResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return LlmResponse(content=response.choices[0].message.content.strip())
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise ApplicationError(
                "LLM generation failed", extra={"error_type": type(e).__name__}
            )

    def parse_json_response(self, response: LlmResponse) -> dict:
        try:
            return json.loads(response.extract_json())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            raise ApplicationError(
                "Invalid JSON response from LLM",
                extra={"error_type": "JSONDecodeError"},
            )
