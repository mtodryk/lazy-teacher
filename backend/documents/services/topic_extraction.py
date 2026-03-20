import json
import logging
from itertools import cycle
from typing import Optional

from .llm_client import AzureLlmClient
from .prompts import (
    TOPIC_EXTRACTION_SYSTEM,
    TOPIC_EXTRACTION_USER,
)
from .chroma_retriever import ChromaRetriever
from .quiz_generator import QuizGenerationService
from .types import QuizData

logger = logging.getLogger(__name__)


def extract_topics(chunks: list[str]) -> list[str]:
    response = AzureLlmClient().generate(
        system_prompt=TOPIC_EXTRACTION_SYSTEM,
        user_prompt=TOPIC_EXTRACTION_USER.format(combined_chunks="\n\n".join(chunks)),
        temperature=0.0,
        max_tokens=800,
    )

    return _parse_topics(response.extract_json())


def _parse_topics(raw: str) -> list[str]:
    data = json.loads(raw)

    if not isinstance(data, dict) or "topics" not in data:
        raise ValueError("Response JSON missing 'topics' key")

    topics = data["topics"]
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise ValueError("'topics' must be a list of strings")

    return topics


def generate_rag_quiz(
    topics: list[str],
    count: int,
    collection,
    max_distance: float = 0.5,
    chunks_per_question: int = 3,
) -> list[dict]:
    """
    Generate quiz questions using RAG + LLM.

    Args:
        topics: List of topics to generate questions about
        count: Number of questions to generate
        collection: ChromaDB collection for retrieval
        max_distance: Maximum distance for context relevance
        chunks_per_question: Number of context chunks to use per question

    Returns:
        List of QuestionData dictionaries ready for database insertion
    """

    quiz = QuizData()
    topic_cycle = cycle(topics)

    for _ in range(count):
        question = QuizGenerationService(
            AzureLlmClient(), ChromaRetriever(collection)
        ).generate_question(
            topic=next(topic_cycle),
            max_distance=max_distance,
            chunks_per_question=chunks_per_question,
        )

        if question:
            quiz.add_question(question)

    return quiz.to_dict()
