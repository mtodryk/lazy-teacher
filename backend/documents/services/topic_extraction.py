import json
import logging
from itertools import cycle

from .llm_client import AzureLlmClient
from .prompts import (
    TOPIC_EXTRACTION_SYSTEM,
    TOPIC_EXTRACTION_USER,
)
from .chroma_retriever import ChromaRetriever
from .quiz_generator import QuizGenerationService
from .types import QuizData
from settings.utils import ApplicationError

logger = logging.getLogger(__name__)


def extract_topics(chunks: list[str]) -> list[str]:
    response = AzureLlmClient().generate(
        system_prompt=TOPIC_EXTRACTION_SYSTEM,
        user_prompt=TOPIC_EXTRACTION_USER.format(combined_chunks="\n\n".join(chunks)),
        temperature=0.0,
        max_tokens=800,
    )

    raw = response.extract_json()
    return _parse_topics(raw)


def _parse_topics(raw: str) -> list[str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ApplicationError(
            "Invalid JSON in LLM response",
            extra={"error": str(e)[:100]},
        )

    if not isinstance(data, dict) or "topics" not in data:
        raise ApplicationError(
            "Missing 'topics' key in LLM response",
            extra={"received_type": type(data).__name__},
        )

    topics = data["topics"]
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise ApplicationError(
            "'topics' must be a list of strings",
            extra={"received_type": type(topics).__name__},
        )

    return topics


def generate_rag_quiz(
    topics: list[str],
    count: int,
    collection,
    max_distance: float = 0.5,
    chunks_per_question: int = 3,
    doc_id: int | None = None,
) -> list[dict]:

    service = QuizGenerationService(AzureLlmClient())

    topic_cycle = cycle(topics)
    topic_sequence = [next(topic_cycle) for _ in range(count)]

    unique_topics = list(set(topic_sequence))
    topic_contexts = ChromaRetriever(collection).retrieve_for_topics(
        topics=unique_topics,
        max_results=chunks_per_question,
        max_distance=max_distance,
        doc_id=doc_id,
    )

    quiz = QuizData()
    for topic in topic_sequence:
        if topic not in topic_contexts:
            logger.warning(f"Topic '{topic}' not in retrieval results, skipping")
            continue

        try:
            question = service.generate_from_context(
                topic=topic,
                context=topic_contexts[topic],
                max_distance=max_distance,
            )
            if question:
                quiz.add_question(question)
        except ApplicationError as e:
            logger.warning(f"Skipping topic '{topic}': {e.message}")
            continue

    return quiz.to_dict()
