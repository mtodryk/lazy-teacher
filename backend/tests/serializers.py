from rest_framework import serializers

from .models import Question, Test


class QuestionCreateSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=2000)


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "created_at"]


class TestCreateSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=1, max_length=100)
    document_id = serializers.IntegerField()
    question_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )


class TestResponseSerializer(serializers.ModelSerializer):
    questions = QuestionResponseSerializer(many=True)
    document_id = serializers.IntegerField(source="document.id")

    class Meta:
        model = Test
        fields = ["id", "code", "document_id", "questions", "created_at"]
