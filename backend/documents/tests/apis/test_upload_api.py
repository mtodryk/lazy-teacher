import pytest
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from documents.models import Document


@pytest.mark.django_db
class TestUploadPDFApi:

    @pytest.fixture
    def upload_url(self):
        return reverse("documents-upload")

    def test_upload_pdf_success(self, auth_client, upload_url, mocker):
        mocker.patch("documents.apis.upload.process_pdf_upload.delay")
        mocker.patch("documents.apis.upload.os.makedirs")
        mock_open = mocker.patch("builtins.open", mocker.mock_open())

        pdf_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )
        response = auth_client.post(upload_url, {"file": pdf_file}, format="multipart")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["status"] == "processing"
        assert response.data["title"] == "test.pdf"
        assert "document_id" in response.data
        assert Document.objects.count() == 1

    def test_upload_non_pdf_rejected(self, auth_client, upload_url):
        txt_file = SimpleUploadedFile(
            "test.txt", b"text content", content_type="text/plain"
        )
        response = auth_client.post(upload_url, {"file": txt_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_unauthenticated(self, api_client, upload_url):
        pdf_file = SimpleUploadedFile(
            "test.pdf", b"%PDF content", content_type="application/pdf"
        )
        response = api_client.post(upload_url, {"file": pdf_file}, format="multipart")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_no_file(self, auth_client, upload_url):
        response = auth_client.post(upload_url, {}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_creates_document_with_pending_status(
        self, auth_client, upload_url, mocker
    ):
        mocker.patch("documents.apis.upload.process_pdf_upload.delay")
        mocker.patch("documents.apis.upload.os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())

        pdf_file = SimpleUploadedFile(
            "document.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )
        auth_client.post(upload_url, {"file": pdf_file}, format="multipart")

        doc = Document.objects.first()
        assert doc.status == Document.Status.PENDING
        assert doc.title == "document.pdf"
        assert doc.file_name == "document.pdf"

    def test_upload_triggers_celery_task(self, auth_client, upload_url, user, mocker):
        mock_task = mocker.patch("documents.apis.upload.process_pdf_upload.delay")
        mocker.patch("documents.apis.upload.os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())

        pdf_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )
        auth_client.post(upload_url, {"file": pdf_file}, format="multipart")

        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]
        assert call_kwargs["user_id"] == user.id
        assert call_kwargs["file_name"] == "test.pdf"
        assert "doc_id" in call_kwargs
        assert "temp_file_path" in call_kwargs

    def test_upload_cleanup_on_error(self, auth_client, upload_url, mocker):
        mocker.patch("documents.apis.upload.os.makedirs")
        mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("documents.apis.upload.os.path.exists", return_value=True)
        mock_remove = mocker.patch("documents.apis.upload.os.remove")
        mocker.patch(
            "documents.apis.upload.Document.objects.create",
            side_effect=Exception("DB error"),
        )

        pdf_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )
        response = auth_client.post(upload_url, {"file": pdf_file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_remove.assert_called_once()
