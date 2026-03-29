import pytest
from django.urls import reverse
from rest_framework import status

from documents.models import Document, TopicExtractionResult


@pytest.mark.django_db
class TestTopicExtractionDetailApi:

    def test_get_topics(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topics-detail",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["topics"] == ["Temat 1", "Temat 2", "Temat 3"]
        assert response.data["model_used"] == "gpt-4o"

    def test_get_topics_not_found(self, auth_client, document):
        url = reverse(
            "documents-topics-detail",
            kwargs={"doc_id": document.id},
        )
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_topics_other_users_doc(self, auth_client, other_user):
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
        url = reverse("documents-topics-detail", kwargs={"doc_id": doc.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_topics_unauthenticated(self, api_client, document_with_topics):
        url = reverse(
            "documents-topics-detail",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestManageTopicAddApi:

    def test_add_topic(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.post(url, {"topic": "Nowy Temat"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "Nowy Temat" in response.data["topics"]
        assert len(response.data["topics"]) == 4

    def test_add_duplicate_topic(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.post(url, {"topic": "Temat 1"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_topic_empty(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.post(url, {"topic": ""}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_topic_no_extraction(self, auth_client, document):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document.id},
        )
        response = auth_client.post(url, {"topic": "Topic"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_topic_persists_in_db(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        auth_client.post(url, {"topic": "Persisted Topic"}, format="json")
        extraction = TopicExtractionResult.objects.get(document=document_with_topics)
        assert "Persisted Topic" in extraction.topics


@pytest.mark.django_db
class TestManageTopicDeleteApi:

    def test_delete_topic(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.delete(url, {"topic": "Temat 1"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "Temat 1" not in response.data["topics"]
        assert len(response.data["topics"]) == 2

    def test_delete_nonexistent_topic(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        response = auth_client.delete(url, {"topic": "Nonexistent"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_topic_no_extraction(self, auth_client, document):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document.id},
        )
        response = auth_client.delete(url, {"topic": "Topic"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_topic_persists(self, auth_client, document_with_topics):
        url = reverse(
            "documents-topic-manage",
            kwargs={"doc_id": document_with_topics.id},
        )
        auth_client.delete(url, {"topic": "Temat 2"}, format="json")
        extraction = TopicExtractionResult.objects.get(document=document_with_topics)
        assert "Temat 2" not in extraction.topics
        assert len(extraction.topics) == 2

    def test_delete_topic_other_users_doc(self, auth_client, other_user):
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
        url = reverse("documents-topic-manage", kwargs={"doc_id": doc.id})
        response = auth_client.delete(url, {"topic": "T1"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
