from django.conf import settings
from django.db import models

from documents.models import Document


class Question(models.Model):
    # pytanie można dać do wielu testów

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_questions",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.text[:80]


class Test(models.Model):
    # test stworzony dla dokumentu

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tests",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="tests",
    )
    code = models.CharField(max_length=100)
    questions = models.ManyToManyField(Question, related_name="tests", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "code")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} ({self.document.title})"
