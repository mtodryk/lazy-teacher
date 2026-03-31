import pytest
from django.urls import reverse
from rest_framework import status

from documents.models import Document
from quizes.models import Quiz, Question, Answer


@pytest.mark.django_db
class TestQuestionsAddApi:
    """Tests for TestQuestions.post — adding questions to a test."""

    @pytest.fixture
    def questions_url(self, quiz_obj):
        return reverse("quiz_questions", kwargs={"quiz_id": quiz_obj.id})

    def test_add_single_question(self, auth_client, questions_url, quiz_obj):
        data = {
            "questions": [
                {
                    "text": "New question?",
                    "topic": "New Topic",
                    "answers": [
                        {"text": "Answer A", "is_correct": True},
                        {"text": "Answer B", "is_correct": False},
                        {"text": "Answer C", "is_correct": False},
                        {"text": "Answer D", "is_correct": False},
                    ],
                }
            ]
        }
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 1
        assert response.data[0]["text"] == "New question?"
        assert len(response.data[0]["answers"]) == 4

    def test_add_multiple_questions(self, auth_client, questions_url, quiz_obj):
        data = {
            "questions": [
                {
                    "text": "Q1?",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                },
                {
                    "text": "Q2?",
                    "answers": [
                        {"text": "B1", "is_correct": False},
                        {"text": "B2", "is_correct": True},
                    ],
                },
            ]
        }
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 2

    def test_add_question_increments_count(self, auth_client, questions_url, quiz_obj):
        initial_count = quiz_obj.questions.count()
        data = {
            "questions": [
                {
                    "text": "Extra?",
                    "answers": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                    ],
                }
            ]
        }
        auth_client.post(questions_url, data, format="json")
        assert quiz_obj.questions.count() == initial_count + 1

    def test_add_question_no_correct_answer(self, auth_client, questions_url):
        data = {
            "questions": [
                {
                    "text": "Q?",
                    "answers": [
                        {"text": "A", "is_correct": False},
                        {"text": "B", "is_correct": False},
                    ],
                }
            ]
        }
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_question_too_few_answers(self, auth_client, questions_url):
        data = {
            "questions": [
                {
                    "text": "Q?",
                    "answers": [
                        {"text": "A", "is_correct": True},
                    ],
                }
            ]
        }
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_question_empty_list(self, auth_client, questions_url):
        data = {"questions": []}
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_question_test_not_found(self, auth_client):
        url = reverse("quiz_questions", kwargs={"quiz_id": 9999})
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
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_question_other_users_test(self, auth_client, other_user, document):
        other_quiz = Quiz.objects.create(
            user=other_user, document=document, code="other-code"
        )
        url = reverse("quiz_questions", kwargs={"quiz_id": other_quiz.id})
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
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_question_unauthenticated(self, api_client, quiz_obj):
        url = reverse("quiz_questions", kwargs={"quiz_id": quiz_obj.id})
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_question_with_default_topic(self, auth_client, questions_url):
        data = {
            "questions": [
                {
                    "text": "No topic question?",
                    "answers": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                    ],
                }
            ]
        }
        response = auth_client.post(questions_url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data[0]["topic"] == ""


@pytest.mark.django_db
class TestQuestionsBulkUpdateApi:
    """Tests for TestQuestions.patch — bulk updating questions."""

    @pytest.fixture
    def questions_url(self, quiz_obj):
        return reverse("quiz_questions", kwargs={"quiz_id": quiz_obj.id})

    def test_update_question_text(self, auth_client, questions_url, quiz_obj):
        question = quiz_obj.questions.first()
        answers = list(question.answers.all())
        data = {
            "questions": [
                {
                    "id": question.id,
                    "text": "Updated question text?",
                    "topic": question.topic,
                    "answers": [
                        {
                            "id": a.id,
                            "text": a.text,
                            "is_correct": a.is_correct,
                        }
                        for a in answers
                    ],
                }
            ]
        }
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        question.refresh_from_db()
        assert question.text == "Updated question text?"

    def test_update_answer_text(self, auth_client, questions_url, quiz_obj):
        question = quiz_obj.questions.first()
        answers = list(question.answers.all())
        data = {
            "questions": [
                {
                    "id": question.id,
                    "text": question.text,
                    "answers": [
                        {
                            "id": answers[0].id,
                            "text": "Updated answer",
                            "is_correct": answers[0].is_correct,
                        },
                    ]
                    + [
                        {
                            "id": a.id,
                            "text": a.text,
                            "is_correct": a.is_correct,
                        }
                        for a in answers[1:]
                    ],
                }
            ]
        }
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        answers[0].refresh_from_db()
        assert answers[0].text == "Updated answer"

    def test_update_nonexistent_question(self, auth_client, questions_url):
        data = {
            "questions": [
                {
                    "id": 99999,
                    "text": "Ghost question",
                }
            ]
        }
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_requires_all_answers(self, auth_client, questions_url, quiz_obj):
        question = quiz_obj.questions.first()
        first_answer = question.answers.first()
        # Only provide one answer instead of all
        data = {
            "questions": [
                {
                    "id": question.id,
                    "text": question.text,
                    "answers": [
                        {
                            "id": first_answer.id,
                            "text": "A",
                            "is_correct": True,
                        },
                    ],
                }
            ]
        }
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_no_correct_answer_rejected(
        self, auth_client, questions_url, quiz_obj
    ):
        question = quiz_obj.questions.first()
        answers = list(question.answers.all())
        data = {
            "questions": [
                {
                    "id": question.id,
                    "text": question.text,
                    "answers": [
                        {
                            "id": a.id,
                            "text": a.text,
                            "is_correct": False,
                        }
                        for a in answers
                    ],
                }
            ]
        }
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_test_not_found(self, auth_client):
        url = reverse("quiz_questions", kwargs={"quiz_id": 9999})
        data = {"questions": [{"id": 1, "text": "Q?"}]}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_other_users_test(self, auth_client, other_user, document):
        other_quiz = Quiz.objects.create(
            user=other_user, document=document, code="other-test"
        )
        url = reverse("quiz_questions", kwargs={"quiz_id": other_quiz.id})
        data = {"questions": [{"id": 1, "text": "Q?"}]}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_preserves_unchanged_questions(
        self, auth_client, questions_url, quiz_obj
    ):
        questions = list(quiz_obj.questions.all())
        q1 = questions[0]
        q2 = questions[1]
        q2_original_text = q2.text

        answers = list(q1.answers.all())
        data = {
            "questions": [
                {
                    "id": q1.id,
                    "text": "Only Q1 updated",
                    "topic": q1.topic,
                    "answers": [
                        {"id": a.id, "text": a.text, "is_correct": a.is_correct}
                        for a in answers
                    ],
                }
            ]
        }
        auth_client.patch(questions_url, data, format="json")
        q2.refresh_from_db()
        assert q2.text == q2_original_text

    def test_update_empty_questions_list(self, auth_client, questions_url):
        data = {"questions": []}
        response = auth_client.patch(questions_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestQuestionDetailDeleteApi:
    """Tests for QuestionDetail.delete."""

    def test_delete_question(self, auth_client, quiz_obj):
        question = quiz_obj.questions.first()
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": quiz_obj.id, "question_id": question.id},
        )
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Question.objects.filter(id=question.id).exists()

    def test_delete_question_cascades_answers(self, auth_client, quiz_obj):
        question = quiz_obj.questions.first()
        answer_ids = list(question.answers.values_list("id", flat=True))
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": quiz_obj.id, "question_id": question.id},
        )
        auth_client.delete(url)
        assert Answer.objects.filter(id__in=answer_ids).count() == 0

    def test_delete_question_not_found(self, auth_client, quiz_obj):
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": quiz_obj.id, "question_id": 9999},
        )
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_question_wrong_test(self, auth_client, user, document, quiz_obj):
        other_quiz = Quiz.objects.create(
            user=user, document=document, code="other-test2"
        )
        question = quiz_obj.questions.first()
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": other_quiz.id, "question_id": question.id},
        )
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_question_other_users_test(self, auth_client, other_user, document):
        other_quiz = Quiz.objects.create(
            user=other_user, document=document, code="foreign-test"
        )
        q = Question.objects.create(quiz=other_quiz, text="Q?")
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": other_quiz.id, "question_id": q.id},
        )
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Question.objects.filter(id=q.id).exists()

    def test_delete_question_unauthenticated(self, api_client, quiz_obj):
        question = quiz_obj.questions.first()
        url = reverse(
            "question_detail",
            kwargs={"quiz_id": quiz_obj.id, "question_id": question.id},
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
