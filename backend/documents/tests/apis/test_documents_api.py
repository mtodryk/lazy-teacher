import pytest
from django.urls import reverse
from rest_framework import status

from documents.models import Document


@pytest.mark.django_db
class TestListDocumentsApi:

    def test_list_documents_authenticated(self, auth_client, document):
        url = reverse("documents-documents")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Test Document"

    def test_list_documents_empty(self, auth_client):
        url = reverse("documents-documents")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_documents_only_own(self, auth_client, document, other_user):
        Document.objects.create(
            user=other_user, title="Other Doc", file_name="other.pdf"
        )
        url = reverse("documents-documents")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_documents_unauthenticated(self, api_client):
        url = reverse("documents-documents")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_documents_returns_correct_fields(self, auth_client, document):
        url = reverse("documents-documents")
        response = auth_client.get(url)
        doc_data = response.data[0]
        assert set(doc_data.keys()) == {
            "id",
            "title",
            "status",
            "chunk_count",
            "uploaded_at",
            "error_message",
        }


@pytest.mark.django_db
class TestDocumentDetailApi:

    def test_get_document(self, auth_client, document):
        url = reverse("documents-document-detail", kwargs={"doc_id": document.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == document.id
        assert response.data["title"] == "Test Document"

    def test_get_document_not_found(self, auth_client):
        url = reverse("documents-document-detail", kwargs={"doc_id": 999})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_users_document(self, auth_client, other_user):
        other_doc = Document.objects.create(
            user=other_user, title="Other", file_name="o.pdf"
        )
        url = reverse("documents-document-detail", kwargs={"doc_id": other_doc.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_document_unauthenticated(self, api_client, document):
        url = reverse("documents-document-detail", kwargs={"doc_id": document.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDocumentDeleteApi:

    def test_delete_document(self, auth_client, document, mocker):
        mocker.patch("documents.apis.documents.delete_document_vectors_task.delay")
        url = reverse("documents-document-detail", kwargs={"doc_id": document.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document.id).exists()

    def test_delete_document_triggers_task(self, auth_client, user, mocker):
        doc = Document.objects.create(
            user=user, title="Del", file_name="del.pdf", s3_key="docs/1.pdf"
        )
        mock_task = mocker.patch(
            "documents.apis.documents.delete_document_vectors_task.delay"
        )
        url = reverse("documents-document-detail", kwargs={"doc_id": doc.id})
        auth_client.delete(url)
        mock_task.assert_called_once_with(doc.id, s3_key="docs/1.pdf")

    def test_delete_nonexistent_document(self, auth_client):
        url = reverse("documents-document-detail", kwargs={"doc_id": 999})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_users_document(self, auth_client, other_user, mocker):
        mocker.patch("documents.apis.documents.delete_document_vectors_task.delay")
        other_doc = Document.objects.create(
            user=other_user, title="Other", file_name="o.pdf"
        )
        url = reverse("documents-document-detail", kwargs={"doc_id": other_doc.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Document.objects.filter(id=other_doc.id).exists()


@pytest.mark.django_db
class TestDocumentDownloadURLApi:

    def test_get_download_url(self, auth_client, user, mocker):
        doc = Document.objects.create(
            user=user,
            title="Doc",
            file_name="doc.pdf",
            s3_key="documents/1/1.pdf",
            status=Document.Status.READY,
        )
        mock_s3 = mocker.patch("documents.apis.documents.S3Client")
        mock_s3.return_value.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned-url"
        )

        url = reverse("documents-download-url", kwargs={"doc_id": doc.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["document_id"] == doc.id
        assert response.data["url"] == "https://s3.example.com/presigned-url"
        assert "expires_in" in response.data

    def test_download_url_no_s3_key(self, auth_client, user):
        doc = Document.objects.create(
            user=user,
            title="Doc",
            file_name="doc.pdf",
            s3_key="",
            status=Document.Status.READY,
        )
        url = reverse("documents-download-url", kwargs={"doc_id": doc.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_download_url_not_found(self, auth_client):
        url = reverse("documents-download-url", kwargs={"doc_id": 999})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_url_other_users_doc(self, auth_client, other_user):
        doc = Document.objects.create(
            user=other_user,
            title="Other",
            file_name="o.pdf",
            s3_key="docs/other.pdf",
        )
        url = reverse("documents-download-url", kwargs={"doc_id": doc.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
