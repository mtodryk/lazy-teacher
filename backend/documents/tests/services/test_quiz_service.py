import pytest
from django.db import IntegrityError
from django.contrib.auth.models import User

from documents.models import Document
from documents.services.quiz import create_quiz_from_topics
from tests.models import Test, Question, Answer


@pytest.mark.django_db
class TestCreateQuizFromTopics:

    @pytest.fixture
    def quiz_data(self):
        return [
            {
                "question": "What is ML?",
                "topic": "Machine Learning",
                "options": ["AI subset", "Database", "Network", "OS"],
                "correct_index": 0,
            },
            {
                "question": "What is NLP?",
                "topic": "Natural Language Processing",
                "options": ["Text processing", "Image processing", "Audio", "Video"],
                "correct_index": 0,
            },
        ]

    def test_creates_test(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        assert isinstance(test, Test)
        assert test.user == user
        assert test.document == document
        assert test.code.startswith("quiz-")

    def test_creates_questions(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        assert test.questions.count() == 2

    def test_creates_answers(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        for question in test.questions.all():
            assert question.answers.count() == 4

    def test_correct_answer_marked(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        for question in test.questions.all():
            correct_answers = question.answers.filter(is_correct=True)
            assert correct_answers.count() == 1

    def test_question_text(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        questions = list(test.questions.order_by("id"))
        assert questions[0].text == "What is ML?"
        assert questions[1].text == "What is NLP?"

    def test_question_topic(self, user, document, quiz_data):
        test = create_quiz_from_topics(user, document, quiz_data)
        question = test.questions.first()
        assert question.topic in ["Machine Learning", "Natural Language Processing"]

    def test_atomic_transaction(self, user, document, mocker):
        bad_data = [
            {
                "question": "Q?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0,
            },
        ]
        mocker.patch(
            "documents.services.quiz.Answer.objects.bulk_create",
            side_effect=IntegrityError("DB error"),
        )

        with pytest.raises(IntegrityError):
            create_quiz_from_topics(user, document, bad_data)

        # Transaction should have rolled back
        assert Test.objects.count() == 0
        assert Question.objects.count() == 0

    def test_empty_quiz_data(self, user, document):
        test = create_quiz_from_topics(user, document, [])
        assert test.questions.count() == 0

    def test_question_without_topic(self, user, document):
        data = [
            {
                "question": "Q?",
                "options": ["A", "B"],
                "correct_index": 0,
            }
        ]
        test = create_quiz_from_topics(user, document, data)
        question = test.questions.first()
        assert question.topic == ""

    def test_correct_index_maps_correctly(self, user, document):
        data = [
            {
                "question": "Q?",
                "options": ["Wrong1", "Wrong2", "Correct", "Wrong3"],
                "correct_index": 2,
            }
        ]
        test = create_quiz_from_topics(user, document, data)
        question = test.questions.first()
        answers = list(question.answers.order_by("id"))
        assert answers[2].is_correct is True
        assert answers[0].is_correct is False
        assert answers[1].is_correct is False
        assert answers[3].is_correct is False
