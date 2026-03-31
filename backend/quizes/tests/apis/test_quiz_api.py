import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from quizes.models import QuizSubmission, SubmittedAnswer


@pytest.mark.django_db
class TestQuizEndpoints:
    def test_list_quizes_auth(self, auth_client, quiz_obj):
        url = reverse("list_quizes")
        r = auth_client.get(url)
        assert r.status_code == status.HTTP_200_OK
        assert any(q["id"] == quiz_obj.id for q in r.json())

    def test_quiz_detail_get(self, auth_client, quiz_obj):
        url = reverse("quiz_detail", kwargs={"quiz_id": quiz_obj.id})
        r = auth_client.get(url)
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["code"] == quiz_obj.code
        assert len(r.json()["questions"]) == quiz_obj.questions.count()

    def test_quiz_detail_patch_enable_disable(self, auth_client, quiz_obj):
        url = reverse("quiz_detail", kwargs={"quiz_id": quiz_obj.id})

        r = auth_client.patch(url, {"is_active": False}, format="json")
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["is_active"] is False
        quiz_obj.refresh_from_db()
        assert quiz_obj.is_active is False

        r2 = auth_client.patch(url, {"is_active": True}, format="json")
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["is_active"] is True

    def test_quiz_detail_patch_missing_is_active(self, auth_client, quiz_obj):
        url = reverse("quiz_detail", kwargs={"quiz_id": quiz_obj.id})
        r = auth_client.patch(url, {}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST
        assert r.json()["detail"] == "is_active field is required."

    def test_quiz_detail_delete(self, auth_client, quiz_obj):
        url = reverse("quiz_detail", kwargs={"quiz_id": quiz_obj.id})
        r = auth_client.delete(url)
        assert r.status_code == status.HTTP_204_NO_CONTENT
        assert not QuizSubmission.objects.filter(quiz=quiz_obj).exists()  # optional

    def test_list_quizes_unauth(self, api_client):
        url = reverse("list_quizes")
        r = api_client.get(url)
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSubmitQuiz:
    def test_submit_quiz_success(self, api_client, quiz_obj):
        url = reverse("submit_quiz", kwargs={"quiz_id": quiz_obj.id})
        answers_payload = [
            {"question": quiz_obj.questions.first().id, "answer_id": quiz_obj.questions.first().answers.filter(is_correct=True).first().id},
            {"question": quiz_obj.questions.last().id, "answer_id": quiz_obj.questions.last().answers.filter(is_correct=True).first().id},
        ]
        r = api_client.post(url, {"name": "Student A", "answers": answers_payload}, format="json")
        assert r.status_code == status.HTTP_200_OK
        d = r.json()
        assert d["score"] == 2
        assert d["max_score"] == 2
        assert d["passed"] is True
        assert len(d["answers"]) == 2

        # zapisane w DB
        submission = QuizSubmission.objects.get(quiz=quiz_obj, student_name="Student A")
        assert submission.score == 2
        assert submission.passed is True
        assert submission.submitted_answers.count() == 2

    def test_submit_quiz_invalid_question_mismatch(self, api_client, quiz_obj):
        url = reverse("submit_quiz", kwargs={"quiz_id": quiz_obj.id})
        payload = {"name": "Student B", "answers": [{"question": 99999, "answer_id": 1}]}
        r = api_client.post(url, payload, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_quiz_submissions_view_owner(self, auth_client, quiz_obj):
        # majac submissiony
        QuizSubmission.objects.create(
            quiz=quiz_obj,
            student_name="XYZ",
            score=1,
            max_score=2,
            percentage=50.0,
            passed=True,
        )
        url = reverse("quiz_submissions", kwargs={"quiz_id": quiz_obj.id})
        r = auth_client.get(url)
        assert r.status_code == status.HTTP_200_OK
        assert len(r.json()) >= 1

    def test_quiz_submissions_view_not_owner(self, other_auth_client, quiz_obj):
        url = reverse("quiz_submissions", kwargs={"quiz_id": quiz_obj.id})
        r = other_auth_client.get(url)
        assert r.status_code == status.HTTP_404_NOT_FOUND