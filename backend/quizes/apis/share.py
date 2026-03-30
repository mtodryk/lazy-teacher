from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from settings.utils import ApplicationError
from ..models import Quiz
from ..serializers import (
    ShareLinkResponseSerializer,
    RetrieveQuizByCodeResponseSerializer,
)
from ..utils import generate_share_code


class ShareLink(APIView):
    """Get or generate share link code for a quiz."""

    permission_classes = [IsAuthenticated]
    serializer_class = ShareLinkResponseSerializer

    @extend_schema(
        responses={200: ShareLinkResponseSerializer},
    )
    def get(self, request: Request, quiz_id: int) -> Response:
        """Get share link code for a quiz (only owner can access)."""
        try:
            quiz = Quiz.objects.get(id=quiz_id, user=request.user)
        except Quiz.DoesNotExist:
            raise NotFound("Quiz not found.")

        return Response(
            ShareLinkResponseSerializer({"code": quiz.code}).data,
        )

    @extend_schema(
        responses={200: ShareLinkResponseSerializer},
    )
    def post(self, request: Request, quiz_id: int) -> Response:
        """Regenerate share link code for a quiz (only owner can access)."""

        try:
            quiz = Quiz.objects.get(id=quiz_id, user=request.user)
        except Quiz.DoesNotExist:
            raise NotFound("Quiz not found.")

        try:
            quiz.code = generate_share_code(quiz.document.id)
            quiz.save(update_fields=["code"])

            return Response(
                ShareLinkResponseSerializer({"code": quiz.code}).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise ApplicationError(
                message="Failed to regenerate share code.",
                extra={"error": str(e)},
            )


class RetrieveQuizByCode(APIView):
    """Retrieve quiz questions by share code (without answers)."""

    permission_classes = []
    serializer_class = RetrieveQuizByCodeResponseSerializer

    @extend_schema(
        responses={200: RetrieveQuizByCodeResponseSerializer},
    )
    def get(self, request: Request, code: str) -> Response:
        """Get quiz questions by code without answers."""
        try:
            quiz = Quiz.objects.prefetch_related("questions__answers").get(code=code, is_active=True)
        except Quiz.DoesNotExist:
            raise NotFound("Quiz with this code not found.")

        return Response(
            RetrieveQuizByCodeResponseSerializer(
                {
                    "quiz_id": quiz.id,
                    "questions": [
                        {
                            "id": q.id,
                            "text": q.text,
                            "topic": q.topic,
                            "answers": [
                                {
                                    "id": a.id,
                                    "text": a.text,
                                }
                                for a in q.answers.all()
                            ],
                        }
                        for q in quiz.questions.all()
                    ],
                }
            ).data
        )
