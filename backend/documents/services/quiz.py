from typing import List, Dict, Any

from django.db import transaction

from tests.models import Answer, Question, Test
from tests.utils import generate_share_code

from ..models import Document


def create_quiz_from_topics(
    user,
    document: Document,
    quiz_data: List[Dict[str, Any]],
) -> Test:
    """
    Create a test with questions and answers from quiz data.

    Args:
        user: The user who owns the test
        document: The document associated with the test
        quiz_data: List of question dictionaries with keys:
                  - 'question': question text
                  - 'topic': (optional) topic name
                  - 'options': list of answer options
                  - 'correct_index': index of the correct answer

    Returns:
        Test: The created test object
    """
    with transaction.atomic():
        test = Test.objects.create(
            user=user,
            document=document,
            code=generate_share_code(document.id),
        )

        for item in quiz_data:
            question = Question.objects.create(
                test=test,
                text=item["question"],
                topic=item.get("topic", ""),
            )

            options = item.get("options", [])
            correct_idx = item.get("correct_index", -1)

            Answer.objects.bulk_create(
                [
                    Answer(question=question, text=text, is_correct=i == correct_idx)
                    for i, text in enumerate(options)
                ]
            )

        return test
