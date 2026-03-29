from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from quizes.models import Quiz
from quizes.serializers import QuizResponseSerializer

from ..models import Document, TopicExtractionResult
from ..tasks import generate_quiz_task
from .serializers import QuizRequestSerializer
from settings.utils import ApplicationError


class GenerateQuiz(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "expensive_operation"
    serializer_class = QuizRequestSerializer

    def post(self, request: Request, doc_id: int) -> Response:
        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)
        data = data.validated_data

        try:
            doc = Document.objects.get(
                id=doc_id, user=request.user, status=Document.Status.TOPICS_EXTRACTED
            )
            topics = TopicExtractionResult.objects.get(document=doc).topics
        except ObjectDoesNotExist:
            raise ApplicationError(
                "Document not found, not analyzed, or topics not extracted.",
                extra={"doc_id": doc_id},
            )

        if not topics:
            raise ApplicationError("No topics available for this document.")

        result = generate_quiz_task.delay(
            doc_id=doc_id,
            user_id=request.user.id,
            count=data["count"],
            max_distance=data["max_distance"],
            chunks_per_question=data["chunks_per_question"],
        )

        return Response(
            {"task_id": result.id, "status": "PENDING"},
            status=202,
        )


class QuizTaskStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, task_id: str) -> Response:
        result = AsyncResult(task_id)

        if result.state == "PENDING":
            return Response({"status": "PENDING"})

        if result.state == "STARTED":
            return Response({"status": "STARTED"})

        if result.state == "SUCCESS":
            task_result = result.result or {}

            if isinstance(task_result, dict) and task_result.get("status") == "error":
                raise ApplicationError(
                    task_result.get("message", "Unknown error"),
                    extra={"details": task_result.get("details", {})},
                )

            quiz_id = (
                task_result.get("quiz_id") if isinstance(task_result, dict) else None
            )
            response_data = {"status": "SUCCESS", "quiz_id": quiz_id}

            if quiz_id:
                try:
                    quiz = Quiz.objects.prefetch_related("questions__answers").get(
                        pk=quiz_id, user=request.user
                    )
                    response_data["quiz"] = QuizResponseSerializer(quiz).data
                except ObjectDoesNotExist:
                    response_data["message"] = "Quiz generated, but quiz not found."

            return Response(response_data)

        if result.state == "FAILURE":
            raise ApplicationError(
                "Quiz generation failed.",
                extra={"error": str(result.result)[:200]},
            )

        return Response({"status": result.state})
