from rest_framework import serializers

from ..models import Document, TopicExtractionResult


# ── Request serializers ──────────────────────────────────────────────


class SearchRequestSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    query = serializers.CharField(min_length=1, max_length=2000)
    n_results = serializers.IntegerField(default=5, min_value=1, max_value=20)


class UploadPDFRequestSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are allowed.")
        from django.conf import settings as django_settings

        max_mb = getattr(django_settings, "RAG_MAX_UPLOAD_SIZE_MB", 30)
        max_size = max_mb * 1024 * 1024
        if value.size and value.size > max_size:
            raise serializers.ValidationError(f"File too large (max {max_mb} MB).")
        return value


# ── Response serializers ─────────────────────────────────────────────


class UploadSuccessResponseSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    status = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()


class SearchHitResponseSerializer(serializers.Serializer):
    text = serializers.CharField()
    chunk_idx = serializers.IntegerField()
    distance = serializers.FloatField()
    source = serializers.CharField()


class SearchSuccessResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    document_id = serializers.IntegerField()
    hits = SearchHitResponseSerializer(many=True)
    count = serializers.IntegerField()


class DocumentItemResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "status",
            "chunk_count",
            "uploaded_at",
            "error_message",
        ]



class TopicExtractionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicExtractionResult
        fields = [
            "id",
            "document",
            "topics",
            "extracted_at",
            "model_used",
            "chunk_count_used",
        ]


class TopicAddRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(min_length=1, max_length=500)


class TopicDeleteRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(min_length=1, max_length=500)


class DocumentURLResponseSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    url = serializers.URLField()
    expires_in = serializers.IntegerField()


# ── Quiz serializers ─────────────────────────────────────────────────


class QuizRequestSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=5, min_value=1, max_value=30)
    max_distance = serializers.FloatField(default=0.5, min_value=0.0, max_value=2.0)
    chunks_per_question = serializers.IntegerField(default=3, min_value=1, max_value=10)
