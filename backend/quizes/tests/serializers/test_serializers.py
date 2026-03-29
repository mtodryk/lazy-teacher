import pytest
from rest_framework import serializers

from quizes.models import QuizSubmission, SubmittedAnswer, Quiz
from quizes.serializers import (
    AddQuestionsSerializer,
    QuizResponseSerializer,
    QuizSubmissionDetailSerializer,
    QuizSubmissionSerializer,
)


@pytest.mark.django_db
class TestAddQuestionsSerializer:

    def test_valid_data(self):
        data = {
            "questions": [
                {
                    "text": "What is 2+2?",
                    "topic": "Math",
                    "answers": [
                        {"text": "3", "is_correct": False},
                        {"text": "4", "is_correct": True},
                        {"text": "5", "is_correct": False},
                    ],
                },
                {
                    "text": "What is the capital of France?",
                    "answers": [
                        {"text": "London", "is_correct": False},
                        {"text": "Paris", "is_correct": True},
                    ],
                },
            ]
        }
        serializer = AddQuestionsSerializer(data=data)
        assert serializer.is_valid()
        assert len(serializer.validated_data["questions"]) == 2

    def test_no_correct_answer(self):
        data = {
            "questions": [
                {
                    "text": "What is 2+2?",
                    "answers": [
                        {"text": "3", "is_correct": False},
                        {"text": "5", "is_correct": False},
                    ],
                }
            ]
        }
        serializer = AddQuestionsSerializer(data=data)
        assert not serializer.is_valid()
        assert "questions" in serializer.errors
        assert "At least one answer must be marked as correct." in str(serializer.errors)

    def test_too_few_answers(self):
        data = {
            "questions": [
                {
                    "text": "What is 2+2?",
                    "answers": [
                        {"text": "4", "is_correct": True},
                    ],
                }
            ]
        }
        serializer = AddQuestionsSerializer(data=data)
        assert not serializer.is_valid()
        assert "questions" in serializer.errors
        assert "answers" in serializer.errors["questions"][0]

    def test_empty_questions_list(self):
        data = {"questions": []}
        serializer = AddQuestionsSerializer(data=data)
        assert not serializer.is_valid()
        assert "questions" in serializer.errors

    def test_missing_text(self):
        data = {
            "questions": [
                {
                    "answers": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                    ],
                }
            ]
        }
        serializer = AddQuestionsSerializer(data=data)
        assert not serializer.is_valid()
        assert "text" in serializer.errors["questions"][0]

    def test_topic_default_empty(self):
        data = {
            "questions": [
                {
                    "text": "Q?",
                    "answers": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                    ],
                }
            ]
        }
        serializer = AddQuestionsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["questions"][0]["topic"] == ""


@pytest.mark.django_db
class TestQuizResponseSerializer:

    def test_serialize_quiz_with_questions(self, quiz_obj):
        serializer = QuizResponseSerializer(quiz_obj)
        data = serializer.data

        assert data["id"] == quiz_obj.id
        assert data["code"] == quiz_obj.code
        assert data["document_id"] == quiz_obj.document.id
        assert data["is_active"] == quiz_obj.is_active
        assert len(data["questions"]) == 2  # From fixture

        # Check first question
        q1_data = data["questions"][0]
        assert "id" in q1_data
        assert "text" in q1_data
        assert "topic" in q1_data
        assert "answers" in q1_data
        assert len(q1_data["answers"]) == 4  # From fixture
        assert any(a["is_correct"] for a in q1_data["answers"])  # At least one correct

    def test_serialize_empty_quiz(self, user, document):
        empty_quiz = Quiz.objects.create(user=user, document=document, code="empty")
        serializer = QuizResponseSerializer(empty_quiz)
        data = serializer.data

        assert data["questions"] == []


@pytest.mark.django_db
class TestQuizSubmissionDetailSerializer:

    def test_serialize_submission_with_answers(self, quiz_obj, user):
        # Create a submission
        submission = QuizSubmission.objects.create(
            quiz=quiz_obj,
            student_name="Test Student",
            score=1,
            max_score=2,
            percentage=50.0,
            passed=False,
        )

        # Create submitted answers
        q1 = quiz_obj.questions.first()
        q2 = quiz_obj.questions.last()
        correct_a1 = q1.answers.filter(is_correct=True).first()
        wrong_a2 = q2.answers.filter(is_correct=False).first()

        SubmittedAnswer.objects.create(
            submission=submission,
            question=q1,
            selected_answer=correct_a1,
            is_correct=True,
        )
        SubmittedAnswer.objects.create(
            submission=submission,
            question=q2,
            selected_answer=wrong_a2,
            is_correct=False,
        )

        serializer = QuizSubmissionDetailSerializer(submission)
        data = serializer.data

        assert data["id"] == submission.id
        assert data["student_name"] == "Test Student"
        assert data["score"] == 1
        assert data["max_score"] == 2
        assert data["percentage"] == 50.0
        assert not data["passed"]
        assert len(data["answers"]) == 2

        answer_data = data["answers"][0]
        assert "question_id" in answer_data
        assert "selected_answer_id" in answer_data
        assert "is_correct" in answer_data
        assert "question_text" in answer_data
        assert "selected_answer_text" in answer_data
        assert "correct_answer_id" in answer_data

    def test_serialize_submission_no_answers(self, quiz_obj, user):
        submission = QuizSubmission.objects.create(
            quiz=quiz_obj,
            student_name="Empty Student",
            score=0,
            max_score=2,
            percentage=0.0,
            passed=False,
        )

        serializer = QuizSubmissionDetailSerializer(submission)
        data = serializer.data

        assert data["answers"] == []


@pytest.mark.django_db
class TestQuizSubmissionSerializer:

    def test_valid_submission_data(self, quiz_obj):
        data = {
            "name": "John Doe",
            "answers": [
                {"question": quiz_obj.questions.first().id, "answer_id": 1},
                {"question": quiz_obj.questions.last().id, "answer_id": 2},
            ],
        }
        serializer = QuizSubmissionSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_name(self):
        data = {
            "answers": [
                {"question": 1, "answer_id": 1},
            ],
        }
        serializer = QuizSubmissionSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_empty_answers(self): # pusty quiz przechodzi
        data = {"name": "John", "answers": []}
        serializer = QuizSubmissionSerializer(data=data)
        assert serializer.is_valid() is True
