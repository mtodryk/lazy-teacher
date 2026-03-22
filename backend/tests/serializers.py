from rest_framework import serializers

from .models import Answer, Question, Test


class AnswerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "is_correct"]


class QuestionCreateSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=2000)
    topic = serializers.CharField(max_length=500, required=False, default="")


class QuestionResponseSerializer(serializers.ModelSerializer):
    answers = AnswerResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "topic", "answers", "created_at"]


class TestCreateSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=1, max_length=100)
    document_id = serializers.IntegerField()

# change test status (active/inactive)
class TestUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class TestResponseSerializer(serializers.ModelSerializer):
    questions = QuestionResponseSerializer(many=True, read_only=True)
    document_id = serializers.IntegerField(source="document.id")

    class Meta:
        model = Test
        fields = ["id", "code", "document_id", "is_active", "questions", "created_at"]



# ── Bulk update serializers ──────────────────────────────────────────


class AnswerUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField(min_length=1, max_length=1000)
    is_correct = serializers.BooleanField()


class QuestionUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField(min_length=1, max_length=2000, required=False)
    topic = serializers.CharField(max_length=500, required=False)
    answers = AnswerUpdateSerializer(many=True, required=False)


class BulkUpdateQuestionsSerializer(serializers.Serializer):
    questions = QuestionUpdateSerializer(many=True, min_length=1)


# ── Add question serializers ─────────────────────────────────────────


class AnswerCreateSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=1000)
    is_correct = serializers.BooleanField()


class AddQuestionSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=2000)
    topic = serializers.CharField(max_length=500, required=False, default="")
    answers = AnswerCreateSerializer(many=True, min_length=2, max_length=6)

    def validate_answers(self, value):
        correct_count = sum(1 for a in value if a["is_correct"])
        if correct_count < 1:
            raise serializers.ValidationError(
                "At least one answer must be marked as correct."
            )
        return value


class AddQuestionsSerializer(serializers.Serializer):
    questions = AddQuestionSerializer(many=True, min_length=1)


# ── Share link serializers ───────────────────────────────────────────
class RetrieveTestByCodeRequestSerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=1,
        max_length=100,
        required=True,
        help_text="Share code of the test",
    )


# Response serializers
class ShareLinkResponseSerializer(serializers.Serializer):
    code = serializers.CharField()


class AnswerForShareSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class TestQuestionForShareSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    topic = serializers.CharField()
    answers = AnswerForShareSerializer(many=True)


class RetrieveTestByCodeResponseSerializer(serializers.Serializer):
    test_id = serializers.IntegerField()
    questions = TestQuestionForShareSerializer(many=True)

# For incoming submission data
class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer_id = serializers.IntegerField()

class TestSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    answers = SubmitAnswerSerializer(many=True)

# For response data
class SubmissionAnswerResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    correct_answer_id = serializers.IntegerField()
    selected_answer_id = serializers.IntegerField()
    is_correct = serializers.BooleanField()

class TestSubmissionResponseSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    max_score = serializers.IntegerField()
    percentage = serializers.FloatField()
    passed = serializers.BooleanField()
    answers = SubmissionAnswerResponseSerializer(many=True)
