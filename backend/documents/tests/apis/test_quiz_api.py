import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.urls import reverse
from rest_framework import status

from documents.models import Document, TopicExtractionResult
from tests.models import Test, Question, Answer


@pytest.mark.django_db
class TestGenerateQuizApi:

    @pytest.fixture
    def quiz_url(self, document_with_topics):
        return reverse(
            "documents-generate-quiz",
            kwargs={"doc_id": document_with_topics.id},
        )

    def test_generate_quiz_success(
        self, auth_client, quiz_url, document_with_topics, mocker
    ):
        mock_task = mocker.patch("documents.apis.quiz.generate_quiz_task.delay")
        mock_task.return_value.id = "task-123"

        response = auth_client.post(
            quiz_url,
            {"count": 5, "max_distance": 0.5, "chunks_per_question": 3},
            format="json",
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["task_id"] == "task-123"
        assert response.data["status"] == "PENDING"

    def test_generate_quiz_default_params(
        self, auth_client, quiz_url, document_with_topics, user, mocker
    ):
        mock_task = mocker.patch("documents.apis.quiz.generate_quiz_task.delay")
        mock_task.return_value.id = "task-456"

        auth_client.post(quiz_url, {}, format="json")

        mock_task.assert_called_once_with(
            doc_id=document_with_topics.id,
            user_id=user.id,
            count=5,
            max_distance=0.5,
            chunks_per_question=3,
        )

    def test_generate_quiz_document_not_found(self, auth_client):
        url = reverse("documents-generate-quiz", kwargs={"doc_id": 999})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_quiz_document_not_analyzed(self, auth_client, document):
        url = reverse("documents-generate-quiz", kwargs={"doc_id": document.id})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_quiz_no_topics(self, auth_client, user):
        doc = Document.objects.create(
            user=user,
            title="No Topics",
            file_name="nt.pdf",
            status=Document.Status.TOPICS_EXTRACTED,
        )
        TopicExtractionResult.objects.create(
            document=doc,
            topics=[],
            model_used="gpt-4o",
            chunk_count_used=0,
        )
        url = reverse("documents-generate-quiz", kwargs={"doc_id": doc.id})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_quiz_invalid_count(self, auth_client, quiz_url):
        response = auth_client.post(quiz_url, {"count": 0}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_quiz_unauthenticated(self, api_client, document_with_topics):
        url = reverse(
            "documents-generate-quiz",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_generate_quiz_other_users_doc(self, auth_client, other_user):
        doc = Document.objects.create(
            user=other_user,
            title="Other",
            file_name="o.pdf",
            status=Document.Status.TOPICS_EXTRACTED,
        )
        TopicExtractionResult.objects.create(
            document=doc,
            topics=["T1"],
            model_used="gpt-4o",
            chunk_count_used=1,
        )
        url = reverse("documents-generate-quiz", kwargs={"doc_id": doc.id})
        response = auth_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskStatusApi:

    @pytest.fixture
    def task_url(self):
        def _url(task_id="task-123"):
            return reverse("documents-quiz-task-status", kwargs={"task_id": task_id})

        return _url

    def test_task_pending(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PENDING"

    def test_task_started(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "STARTED"
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "STARTED"

    def test_task_success_with_test(self, auth_client, task_url, user, mocker):
        doc = Document.objects.create(
            user=user,
            title="Doc",
            file_name="d.pdf",
            status=Document.Status.TOPICS_EXTRACTED,
        )
        test = Test.objects.create(user=user, document=doc, code="quiz-1-abc")
        q = Question.objects.create(test=test, text="Question?")
        Answer.objects.create(question=q, text="Answer", is_correct=True)

        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"test_id": test.id}
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "SUCCESS"
        assert response.data["test_id"] == test.id
        assert "test" in response.data

    def test_task_success_error_result(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"status": "error", "message": "Something failed"}
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_task_failure(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.result = Exception("Task crashed")
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_task_success_test_not_found(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"test_id": 9999}
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "SUCCESS"
        assert "message" in response.data

    def test_task_unauthenticated(self, api_client, task_url):
        response = api_client.get(task_url())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_task_unknown_state(self, auth_client, task_url, mocker):
        mock_result = MagicMock()
        mock_result.state = "CUSTOM_STATE"
        mocker.patch("documents.apis.quiz.AsyncResult", return_value=mock_result)

        response = auth_client.get(task_url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "CUSTOM_STATE"
