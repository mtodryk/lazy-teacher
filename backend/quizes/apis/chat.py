import logging

from celery.result import AsyncResult
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from documents.services.explanation import MAX_CHAT_MESSAGES
from documents.tasks import generate_explanation_task, generate_followup_task
from quizes.models import ChatMessage, Question, QuestionChat
from settings.utils import ApplicationError

logger = logging.getLogger(__name__)


class ChatSendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=2000)


class QuestionChatView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_operation"

    def get(self, request: Request, quiz_id: int, question_id: int) -> Response:
        question = self._get_question(question_id, quiz_id)

        try:
            chat = QuestionChat.objects.get(user=request.user, question=question)
        except QuestionChat.DoesNotExist:
            return Response({"messages": []})

        messages = chat.messages.all().values("role", "content", "created_at")
        return Response({"messages": list(messages)})

    def post(self, request: Request, quiz_id: int, question_id: int) -> Response:
        question = self._get_question(question_id, quiz_id)
        correct_answer = question.answers.filter(is_correct=True).first()
        if not correct_answer:
            raise ApplicationError("No correct answer found for this question.")

        chat, created = QuestionChat.objects.get_or_create(
            user=request.user,
            question=question,
        )

        if created:
            task = generate_explanation_task.delay(
                chat_id=chat.id,
                question_id=question.id,
            )
            return Response(
                {"task_id": task.id, "status": "PENDING"},
                status=202,
            )

        # Existing chat — handle followup message
        serializer = ChatSendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data["message"]

        msg_count = chat.messages.count()
        if msg_count >= MAX_CHAT_MESSAGES:
            raise ApplicationError(
                f"Osiągnięto limit wiadomości ({MAX_CHAT_MESSAGES}). "
                "Wyczyść czat, aby kontynuować.",
            )

        ChatMessage.objects.create(
            chat=chat,
            role=ChatMessage.Role.USER,
            content=user_message,
        )

        chat_history = list(
            chat.messages.order_by("created_at").values("role", "content")
        )

        task = generate_followup_task.delay(
            chat_id=chat.id,
            user_message=user_message,
            chat_history=chat_history[:-1],  # exclude the just-added user msg
        )

        return Response(
            {"task_id": task.id, "status": "PENDING"},
            status=202,
        )

    def delete(self, request: Request, quiz_id: int, question_id: int) -> Response:
        question = self._get_question(question_id, quiz_id)

        try:
            chat = QuestionChat.objects.get(user=request.user, question=question)
        except QuestionChat.DoesNotExist:
            return Response(status=204)

        # Keep the first assistant message (initial explanation), delete the rest
        first_msg = chat.messages.order_by("created_at").first()
        if first_msg and first_msg.role == ChatMessage.Role.ASSISTANT:
            chat.messages.exclude(id=first_msg.id).delete()
        else:
            chat.messages.all().delete()

        messages = chat.messages.all().values("role", "content", "created_at")
        return Response({"messages": list(messages)})

    def _get_question(self, question_id: int, quiz_id: int) -> Question:
        try:
            return Question.objects.select_related("quiz__document").get(
                id=question_id, quiz_id=quiz_id
            )
        except Question.DoesNotExist:
            raise ApplicationError(
                "Question not found.",
                extra={"question_id": question_id, "quiz_id": quiz_id},
            )


class ChatTaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, task_id: str) -> Response:
        result = AsyncResult(task_id)

        if result.state in ("PENDING", "STARTED"):
            return Response({"status": result.state})

        if result.state == "SUCCESS":
            task_result = result.result or {}

            if isinstance(task_result, dict) and task_result.get("status") == "error":
                raise ApplicationError(
                    task_result.get("message", "Unknown error"),
                )

            chat_id = (
                task_result.get("chat_id") if isinstance(task_result, dict) else None
            )
            if chat_id:
                try:
                    chat = QuestionChat.objects.get(id=chat_id, user=request.user)
                    messages = list(
                        chat.messages.all().values("role", "content", "created_at")
                    )
                    return Response({"status": "SUCCESS", "messages": messages})
                except QuestionChat.DoesNotExist:
                    pass

            return Response({"status": "SUCCESS", "messages": []})

        if result.state == "FAILURE":
            raise ApplicationError("Chat task failed.")

        return Response({"status": result.state})
