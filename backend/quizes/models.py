from django.conf import settings
from django.db import models

from documents.models import Document


class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizes",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="quizes",
    )
    code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} ({self.document.title})"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    topic = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.text[:80]


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        mark = "✓" if self.is_correct else "✗"
        return f"{self.text[:50]} [{mark}]"


class QuizSubmission(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student_name = models.CharField(max_length=100)  # Student's name from the request
    score = models.IntegerField()  # Number of correct answers
    max_score = models.IntegerField()  # Total number of questions
    percentage = models.FloatField()  # Score as a percentage
    passed = models.BooleanField()  # True if percentage >= some threshold (e.g., 60%)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.student_name} - {self.quiz.code} ({self.score}/{self.max_score})"


class SubmittedAnswer(models.Model):
    submission = models.ForeignKey(
        QuizSubmission,
        on_delete=models.CASCADE,
        related_name="submitted_answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        null=True,  # Allow null if no answer selected
    )
    is_correct = models.BooleanField()

    def __str__(self) -> str:
        return f"Q{self.question.id}: {'Correct' if self.is_correct else 'Incorrect'}"
