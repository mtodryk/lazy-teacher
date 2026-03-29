from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ..models import Quiz
from ..serializers import QuizResponseSerializer, QuizUpdateSerializer


class ListQuizes(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizResponseSerializer

    def get(self, request: Request) -> Response:
        serializer = QuizResponseSerializer(
            Quiz.objects.filter(user=request.user).prefetch_related(
                "questions__answers"
            ),
            many=True,
        )
        return Response(serializer.data)


class QuizDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizResponseSerializer

    def _get_test(self, quiz_id: int, user):
        try:
            return Quiz.objects.prefetch_related("questions__answers").get(
                id=quiz_id, user=user
            )
        except Quiz.DoesNotExist:
            raise NotFound("Quiz not found.")

    def get(self, request: Request, quiz_id: int) -> Response:
        quiz = self._get_test(quiz_id, request.user)
        return Response(QuizResponseSerializer(quiz).data)

    def delete(self, request: Request, quiz_id: int) -> Response:
        quiz = self._get_test(quiz_id, request.user)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, quiz_id: int) -> Response:
        quiz = self._get_test(quiz_id, request.user)

        if "is_active" not in request.data:
            return Response(
                {"detail": "is_active field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quiz.is_active = bool(request.data["is_active"])
        quiz.save(update_fields=["is_active"])

        return Response(QuizResponseSerializer(quiz).data, status=status.HTTP_200_OK)
