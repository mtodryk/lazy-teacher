import json
import logging
import random
from typing import Optional

from .chroma_retriever import ChromaRetriever
from .llm_client import AzureLlmClient
from .prompts import (
    QUIZ_GENERATION_SYSTEM,
    QUIZ_GENERATION_USER,
    NO_CONTEXT_WARNING,
)
from .types import QuestionData

logger = logging.getLogger(__name__)


class QuizGenerationService:
    def __init__(
        self,
        llm_client: AzureLlmClient,
        retriever: ChromaRetriever,
    ) -> None:
        self.llm_client = llm_client
        self.retriever = retriever

    def generate_question(
        self,
        topic: str,
        max_distance: float = 0.5,
        chunks_per_question: int = 3,
    ) -> Optional[QuestionData]:

        context = self.retriever.retrieve_for_topic(
            topic=topic,
            max_results=chunks_per_question,
            max_distance=max_distance,
        )

        try:
            response = self.llm_client.generate(
                system_prompt=QUIZ_GENERATION_SYSTEM,
                user_prompt=QUIZ_GENERATION_USER.format(
                    topic=topic,
                    context="\n\n".join(context.documents)
                    or "BRAK ODPOWIEDNIEGO FRAGMENTU",
                    no_context_note=(
                        ""
                        if context.has_good_context(max_distance)
                        else NO_CONTEXT_WARNING.format(max_distance=max_distance)
                    ),
                ),
                temperature=0.2,
                max_tokens=800,
            )
        except Exception as e:
            logger.error("LLM call failed for topic '%s': %s", topic, e)
            return None

        try:
            data = self.llm_client.parse_json_response(response)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse quiz response for topic '%s': %s", topic, e)
            return None

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
            return None

        # Step 5: Shuffle options
        self._shuffle_options(question)

        return question

    @staticmethod
    def _shuffle_options(question: QuestionData) -> None:
        correct_answer = question.options[question.correct_index]
        random.shuffle(question.options)
        question.correct_index = question.options.index(correct_answer)
