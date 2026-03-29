import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from documents.models import Document
from quizes.models import Quiz, Question, Answer


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
def quiz_obj(user, document):
    """Create a test with questions and answers."""
    quiz = Quiz.objects.create(
        user=user,
        document=document,
        code="quiz-1-testcode",
    )
    q1 = Question.objects.create(quiz=quiz, text="Question 1?", topic="Topic A")
    Answer.objects.create(question=q1, text="Correct answer", is_correct=True)
    Answer.objects.create(question=q1, text="Wrong answer 1", is_correct=False)
    Answer.objects.create(question=q1, text="Wrong answer 2", is_correct=False)
    Answer.objects.create(question=q1, text="Wrong answer 3", is_correct=False)

    q2 = Question.objects.create(quiz=quiz, text="Question 2?", topic="Topic B")
    Answer.objects.create(question=q2, text="Wrong", is_correct=False)
    Answer.objects.create(question=q2, text="Correct", is_correct=True)
    Answer.objects.create(question=q2, text="Wrong2", is_correct=False)
    Answer.objects.create(question=q2, text="Wrong3", is_correct=False)

    return quiz
