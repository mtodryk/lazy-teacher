import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from documents.models import Document, TopicExtractionResult


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="otherpass123",
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=other_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def document(user):
    return Document.objects.create(
        user=user,
        title="Test Document",
        file_name="test.pdf",
        status=Document.Status.READY,
        chunk_count=10,
    )


@pytest.fixture
def pending_document(user):
    return Document.objects.create(
        user=user,
        title="Pending Document",
        file_name="pending.pdf",
        status=Document.Status.PENDING,
    )


@pytest.fixture
def document_with_topics(user):
    doc = Document.objects.create(
        user=user,
        title="Document With Topics",
        file_name="topics.pdf",
        status=Document.Status.TOPICS_EXTRACTED,
        chunk_count=5,
        s3_key="documents/1/1.pdf",
    )
    TopicExtractionResult.objects.create(
        document=doc,
        topics=["Temat 1", "Temat 2", "Temat 3"],
        model_used="gpt-4o",
        chunk_count_used=5,
    )
    return doc


@pytest.fixture
def topic_extraction(document_with_topics):
    return TopicExtractionResult.objects.get(document=document_with_topics)
