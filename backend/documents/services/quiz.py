from typing import List, Dict, Any

from django.db import transaction

from quizes.models import Answer, Question, Quiz
from quizes.utils import generate_share_code

from ..models import Document


def create_quiz_from_topics(
    user,
    document: Document,
    quiz_data: List[Dict[str, Any]],
) -> Quiz:
    """
    Create a quiz with questions and answers from quiz data.

    Args:
        user: The user who owns the quiz
        document: The document associated with the quiz
        quiz_data: List of question dictionaries with keys:
                  - 'question': question text
                  - 'topic': (optional) topic name
                  - 'options': list of answer options
                  - 'correct_index': index of the correct answer

    Returns:
        Quiz: The created quiz object
    """
    with transaction.atomic():
        quiz = Quiz.objects.create(
            user=user,
            document=document,
            code=generate_share_code(document.id),
        )

        for item in quiz_data:
            question = Question.objects.create(
                quiz=quiz,
                text=item["question"],
                topic=item.get("topic", ""),
                source_chunks=item.get("source_chunks", []),
            )

            options = item.get("options", [])
            correct_idx = item.get("correct_index", -1)

            Answer.objects.bulk_create(
                [
                    Answer(question=question, text=text, is_correct=i == correct_idx)
                    for i, text in enumerate(options)
                ]
            )

        return quiz
