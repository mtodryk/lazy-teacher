import json
import logging

from django.conf import settings
from openai import AzureOpenAI

from .types import LlmResponse

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

    def parse_json_response(self, response: LlmResponse) -> dict:
        return json.loads(response.extract_json())
