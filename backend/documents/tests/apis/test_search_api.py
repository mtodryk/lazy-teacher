import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status

from documents.models import Document, TopicExtractionResult


@pytest.mark.django_db
class TestSearchApi:

    @pytest.fixture
    def search_url(self):
        return reverse("documents-search")

    def test_search_success(self, auth_client, document, search_url, mocker):
        mock_retrieve = mocker.patch("documents.apis.search.retrieve_chunks")
        mock_hit = MagicMock()
        mock_hit.text = "Some relevant text"
        mock_hit.chunk_idx = 0
        mock_hit.distance = 0.15
        mock_hit.source = "test.pdf"
        mock_retrieve.return_value = [mock_hit]

        response = auth_client.post(
            search_url,
            {"document_id": document.id, "query": "test query", "n_results": 5},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["query"] == "test query"
        assert response.data["document_id"] == document.id
        assert response.data["count"] == 1
        assert len(response.data["hits"]) == 1
        assert response.data["hits"][0]["text"] == "Some relevant text"

    def test_search_document_not_found(self, auth_client, search_url):
        response = auth_client.post(
            search_url,
            {"document_id": 999, "query": "test query"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_document_not_ready(self, auth_client, pending_document, search_url):
        response = auth_client.post(
            search_url,
            {"document_id": pending_document.id, "query": "test query"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_other_users_document(self, auth_client, other_user, search_url):
        other_doc = Document.objects.create(
            user=other_user,
            title="Other",
            file_name="o.pdf",
            status=Document.Status.READY,
        )
        response = auth_client.post(
            search_url,
            {"document_id": other_doc.id, "query": "test"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_invalid_data(self, auth_client, search_url):
        response = auth_client.post(search_url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_empty_query(self, auth_client, search_url, document):
        response = auth_client.post(
            search_url,
            {"document_id": document.id, "query": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_unauthenticated(self, api_client, search_url, document):
        response = api_client.post(
            search_url,
            {"document_id": document.id, "query": "test"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_passes_correct_params(
        self, auth_client, document, search_url, mocker
    ):
        mock_retrieve = mocker.patch("documents.apis.search.retrieve_chunks")
        mock_retrieve.return_value = []

        auth_client.post(
            search_url,
            {"document_id": document.id, "query": "my query", "n_results": 10},
            format="json",
        )
        mock_retrieve.assert_called_once_with(
            query="my query",
            doc_id=document.id,
            user_id=document.user.id,
            n_results=10,
        )

    def test_search_empty_results(self, auth_client, document, search_url, mocker):
        mocker.patch("documents.apis.search.retrieve_chunks", return_value=[])

        response = auth_client.post(
            search_url,
            {"document_id": document.id, "query": "nothing"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["hits"] == []
