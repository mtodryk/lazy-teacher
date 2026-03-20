from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from settings.utils import ApplicationError
from ..models import Answer, Question, Test
from ..serializers import (
    AddQuestionsSerializer,
    BulkUpdateQuestionsSerializer,
    QuestionResponseSerializer,
    TestResponseSerializer,
)


class TestQuestions(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = AddQuestionsSerializer

    def _get_test(self, test_id: int, user):
        try:
            return Test.objects.get(id=test_id, user=user)
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

    def post(self, request: Request, test_id: int) -> Response:
        """
        Add new questions (with answers) to a test.

        Expected request body:
        {
            "questions": [
                {
                    "text": "Question text",
                    "topic": "optional topic",
                    "answers": [
                        {"text": "Answer 1", "is_correct": true},
                        {"text": "Answer 2", "is_correct": false}
                    ]
                }
            ]
        }

        All questions provided in the request will be created as new questions.
        """
        test = self._get_test(test_id, request.user)

        serializer = AddQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_questions = []
        with transaction.atomic():
            for q_data in serializer.validated_data["questions"]:
                question = Question.objects.create(
                    test=test,
                    text=q_data["text"],
                    topic=q_data.get("topic", ""),
                )
                answers_to_create = [
                    Answer(
                        question=question,
                        text=a["text"],
                        is_correct=a["is_correct"],
                    )
                    for a in q_data["answers"]
                ]
                Answer.objects.bulk_create(answers_to_create)
                created_questions.append(question)

        # Refetch with answers for response
        question_ids = [q.id for q in created_questions]
        questions = Question.objects.filter(id__in=question_ids).prefetch_related(
            "answers"
        )

        return Response(
            QuestionResponseSerializer(questions, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request: Request, test_id: int) -> Response:
        """
        Bulk-update existing questions/answers in a test.

        Only updates the questions included in the request. Questions not in the
        array remain completely unchanged.

        Expected request body:
        {
            "questions": [
                {
                    "id": 1,
                    "text": "Updated question text",
                    "topic": "new topic",
                    "answers": [
                        {"id": 1, "text": "Answer 1", "is_correct": true},
                        {"id": 2, "text": "Answer 2", "is_correct": false}
                    ]
                }
            ]
        }

        Behavior:
        - Only questions with IDs in the request are updated
        - Questions with IDs NOT in the request are left completely unchanged
        - For each question being updated, ALL answer IDs and data must be provided
        - At least one answer must be marked as correct
        - All answer IDs and question IDs must exist in the test
        """

        test = self._get_test(test_id, request.user)

        serializer = BulkUpdateQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_ids = [q["id"] for q in serializer.validated_data["questions"]]
        existing_questions = {
            q.id: q for q in Question.objects.filter(id__in=question_ids, test=test)
        }

        missing = set(question_ids) - set(existing_questions.keys())
        if missing:
            raise ApplicationError(
                message="Some questions were not found in this test.",
                extra={"missing_ids": sorted(missing)},
            )

        with transaction.atomic():
            for q_data in serializer.validated_data["questions"]:
                question = existing_questions[q_data["id"]]

                if "text" in q_data:
                    question.text = q_data["text"]
                if "topic" in q_data:
                    question.topic = q_data["topic"]
                question.save(update_fields=["text", "topic"])

                if "answers" in q_data:
                    answer_updates = q_data["answers"]

                    # Validate at least 1 correct
                    correct_count = sum(1 for a in answer_updates if a["is_correct"])
                    if correct_count < 1:
                        raise ApplicationError(
                            message="At least one answer must be correct.",
                            extra={"question_id": question.id},
                        )

                    answer_ids = [a["id"] for a in answer_updates]
                    existing_answers = {
                        a.id: a
                        for a in Answer.objects.filter(
                            id__in=answer_ids, question=question
                        )
                    }

                    missing_answers = set(answer_ids) - set(existing_answers.keys())
                    if missing_answers:
                        raise ApplicationError(
                            message="Some answers were not found for this question.",
                            extra={
                                "question_id": question.id,
                                "missing_ids": sorted(missing_answers),
                            },
                        )

                    for a_data in answer_updates:
                        answer = existing_answers[a_data["id"]]
                        answer.text = a_data["text"]
                        answer.is_correct = a_data["is_correct"]
                        answer.save(update_fields=["text", "is_correct"])

        # Refetch for response
        test = self._get_test(test_id, request.user)
        test = Test.objects.prefetch_related("questions__answers").get(id=test.id)
        return Response(TestResponseSerializer(test).data)


class QuestionDetail(APIView):
    """DELETE a single question from a test."""

    permission_classes = [IsAuthenticated]
    serializer_class = QuestionResponseSerializer

    def delete(self, request: Request, test_id: int, question_id: int) -> Response:
        try:
            question = Question.objects.select_related("test").get(
                id=question_id,
                test_id=test_id,
                test__user=request.user,
            )
        except Question.DoesNotExist:
            raise NotFound("Question not found in this test.")

        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
