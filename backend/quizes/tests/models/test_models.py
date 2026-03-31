import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from quizes.models import Quiz, Answer, QuizSubmission


@pytest.mark.django_db
class TestQuiz:

    def test_create_quiz(self, user, document):
        quiz = Quiz.objects.create(
            user=user,
            document=document,
            code="TEST123",
            is_active=True
        )
        assert quiz.user == user
        assert quiz.document == document
        assert quiz.code == "TEST123"
        assert quiz.is_active is True
        assert quiz.created_at is not None

    def test_quiz_str(self, user, document):
        quiz = Quiz.objects.create(
            user=user,
            document=document,
            code="QUIZ001"
        )
        assert str(quiz) == "QUIZ001 (Test Document)" 

    def test_quiz_unique_code(self, user, document):
        Quiz.objects.create(user=user, document=document, code="UNIQUE")
        with pytest.raises(Exception):  # ValidationError lub IntegrityError
            Quiz.objects.create(user=user, document=document, code="UNIQUE")

    def test_quiz_ordering(self, user, document):
        quiz1 = Quiz.objects.create(user=user, document=document, code="QUIZ1")
        quiz2 = Quiz.objects.create(user=user, document=document, code="QUIZ2")
        quizzes = list(Quiz.objects.all())
        assert quizzes[0] == quiz2  # Najnowszy pierwszy
        assert quizzes[1] == quiz1


@pytest.mark.django_db
class TestAnswer:

    def test_create_answer(self, quiz_obj):
        question = quiz_obj.questions.first()  
        answer = Answer.objects.create(
            question=question,
            text="Test Answer",
            is_correct=True
        )
        assert answer.question == question
        assert answer.text == "Test Answer"
        assert answer.is_correct is True

    def test_answer_str(self, quiz_obj):
        question = quiz_obj.questions.first()
        correct_answer = Answer.objects.create(
            question=question,
            text="Correct Answer",
            is_correct=True
        )
        incorrect_answer = Answer.objects.create(
            question=question,
            text="Incorrect Answer",
            is_correct=False
        )
        assert str(correct_answer) == "Correct Answer [✓]"
        assert str(incorrect_answer) == "Incorrect Answer [✗]"

    def test_answer_ordering(self, quiz_obj):
        question = quiz_obj.questions.first()
        answer1 = Answer.objects.create(question=question, text="Answer 1", is_correct=False)
        answer2 = Answer.objects.create(question=question, text="Answer 2", is_correct=True)
        answers = list(Answer.objects.filter(question=question))
        assert answers[4] == answer1
        assert answers[5] == answer2


@pytest.mark.django_db
class TestQuizSubmission:

    def test_create_submission(self, quiz_obj):
        submission = QuizSubmission.objects.create(
            quiz=quiz_obj,
            student_name="John Doe",
            score=8,
            max_score=10,
            percentage=80.0,
            passed=True
        )
        assert submission.quiz == quiz_obj
        assert submission.student_name == "John Doe"
        assert submission.score == 8
        assert submission.max_score == 10
        assert submission.percentage == 80.0
        assert submission.passed is True
        assert submission.submitted_at is not None

    def test_submission_str(self, quiz_obj):
        submission = QuizSubmission.objects.create(
            quiz=quiz_obj,
            student_name="Jane Smith",
            score=5,
            max_score=10,
            percentage=50.0,
            passed=False
        )
        assert str(submission) == "Jane Smith - quiz-1-testcode (5/10)" 

    def test_submission_ordering(self, quiz_obj):
        sub1 = QuizSubmission.objects.create(
            quiz=quiz_obj, student_name="Student1", score=7, max_score=10, percentage=70.0, passed=True
        )
        sub2 = QuizSubmission.objects.create(
            quiz=quiz_obj, student_name="Student2", score=9, max_score=10, percentage=90.0, passed=True
        )
        submissions = list(QuizSubmission.objects.all())
        assert submissions[0] == sub2  # Najnowszy pierwszy
        assert submissions[1] == sub1