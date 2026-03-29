from rest_framework import serializers

from .models import Answer, Question, Quiz, QuizSubmission, SubmittedAnswer


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


class QuizCreateSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=1, max_length=100)
    document_id = serializers.IntegerField()

# change quiz status (active/inactive)
class QuizUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class QuizResponseSerializer(serializers.ModelSerializer):
    questions = QuestionResponseSerializer(many=True, read_only=True)
    document_id = serializers.IntegerField(source="document.id")

    class Meta:
        model = Quiz
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
class RetrieveQuizByCodeRequestSerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=1,
        max_length=100,
        required=True,
        help_text="Share code of the quiz",
    )


# Response serializers
class ShareLinkResponseSerializer(serializers.Serializer):
    code = serializers.CharField()


class AnswerForShareSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class QuizQuestionForShareSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    topic = serializers.CharField()
    answers = AnswerForShareSerializer(many=True)


class RetrieveQuizByCodeResponseSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    questions = QuizQuestionForShareSerializer(many=True)

# For incoming submission data
class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer_id = serializers.IntegerField()

class QuizSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    answers = SubmitAnswerSerializer(many=True)

# For response data
class SubmissionAnswerResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    correct_answer_id = serializers.IntegerField()
    selected_answer_id = serializers.IntegerField()
    is_correct = serializers.BooleanField()

class QuizSubmissionResponseSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    max_score = serializers.IntegerField()
    percentage = serializers.FloatField()
    passed = serializers.BooleanField()
    answers = SubmissionAnswerResponseSerializer(many=True)

# For checking submissions by quiz author
class SubmittedAnswerDetailSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    selected_answer_text = serializers.CharField(source="selected_answer.text", read_only=True, allow_null=True)
    correct_answer_id = serializers.SerializerMethodField()

    class Meta:
        model = SubmittedAnswer
        fields = ["question_id", "selected_answer_id", "is_correct", "question_text", "selected_answer_text", "correct_answer_id"]

    def get_correct_answer_id(self, obj):
        # Finding correct answer for the question
        correct = obj.question.answers.filter(is_correct=True).first()
        return correct.id if correct else None

class QuizSubmissionDetailSerializer(serializers.ModelSerializer):
    answers = SubmittedAnswerDetailSerializer(source="submitted_answers", many=True, read_only=True)

    class Meta:
        model = QuizSubmission
        fields = ["id", "student_name", "score", "max_score", "percentage", "passed", "submitted_at", "answers"]