import json
import logging
import random
from typing import Optional

from .llm_client import AzureLlmClient
from .prompts import (
    QUIZ_GENERATION_SYSTEM,
    QUIZ_GENERATION_USER,
    NO_CONTEXT_WARNING,
)
from .types import QuestionData, RetrievalContext
from settings.utils import ApplicationError

logger = logging.getLogger(__name__)


class QuizGenerationService:
    def __init__(
        self,
        llm_client: AzureLlmClient,
    ) -> None:
        self.llm_client = llm_client

    def generate_from_context(
        self,
        topic: str,
        context: RetrievalContext,
        max_distance: float = 0.5,
    ) -> Optional[QuestionData]:
        response = self.llm_client.generate(
            system_prompt=QUIZ_GENERATION_SYSTEM,
            user_prompt=QUIZ_GENERATION_USER.format(
                topic=topic,
                context="\n\n".join(context.documents)
                or "NO RELEVANT CONTEXT AVAILABLE",
                no_context_note=(
                    ""
                    if context.has_good_context(max_distance)
                    else NO_CONTEXT_WARNING.format(max_distance=max_distance)
                ),
            ),
            temperature=0.2,
            max_tokens=800,
        )

        data = self.llm_client.parse_json_response(response)

        try:
            question = QuestionData(
                question=data["question"],
                options=data["options"],
                correct_index=data["correct_index"],
                topic=topic,
                used_chunks_count=len(context.get_good_chunks(max_distance)),
                max_distance_used=max_distance,
            )
        except (KeyError, IndexError, ValueError) as e:
            logger.warning("Invalid quiz data for topic '%s': %s", topic, e)
            raise ApplicationError(
                f"Invalid question data structure for topic '{topic}'",
                extra={"missing_field": str(e)[:100]},
            )

        self._shuffle_options(question)
        return question

    @staticmethod
    def _shuffle_options(question: QuestionData) -> None:
        correct_answer = question.options[question.correct_index]
        random.shuffle(question.options)
        question.correct_index = question.options.index(correct_answer)
