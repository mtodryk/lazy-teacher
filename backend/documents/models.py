from django.conf import settings
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        TOPICS_EXTRACTED = "topics_extracted", "Topics Extracted"
        ERROR = "error", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rag_documents",
    )
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=512, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    chunk_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class TopicExtractionResult(models.Model):
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name="topic_extraction",
    )
    topics = models.JSONField(default=list)
    extracted_at = models.DateTimeField(auto_now_add=True)
    model_used = models.CharField(max_length=30)
    chunk_count_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Topics for {self.document.title} ({len(self.topics)} topics)"
