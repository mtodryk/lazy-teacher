from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from settings.utils import ApplicationError
from ..models import Test
from ..serializers import (
    ShareLinkResponseSerializer,
    RetrieveTestByCodeResponseSerializer,
)
from ..utils import generate_share_code


class ShareLink(APIView):
    """Get or generate share link code for a test."""

    permission_classes = [IsAuthenticated]
    serializer_class = ShareLinkResponseSerializer

    @extend_schema(
        responses={200: ShareLinkResponseSerializer},
    )
    def get(self, request: Request, test_id: int) -> Response:
        """Get share link code for a test (only owner can access)."""
        try:
            test = Test.objects.get(id=test_id, user=request.user)
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

        return Response(
            ShareLinkResponseSerializer({"code": test.code}).data,
        )

    @extend_schema(
        responses={200: ShareLinkResponseSerializer},
    )
    def post(self, request: Request, test_id: int) -> Response:
        """Regenerate share link code for a test (only owner can access)."""

        try:
            test = Test.objects.get(id=test_id, user=request.user)
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

        try:
            test.code = generate_share_code(test.document.id)
            test.save(update_fields=["code"])

            return Response(
                ShareLinkResponseSerializer({"code": test.code}).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise ApplicationError(
                message="Failed to regenerate share code.",
                extra={"error": str(e)},
            )


class RetrieveTestByCode(APIView):
    """Retrieve test questions by share code (without answers)."""

    permission_classes = [IsAuthenticated]
    serializer_class = RetrieveTestByCodeResponseSerializer

    @extend_schema(
        responses={200: RetrieveTestByCodeResponseSerializer},
    )
    def get(self, request: Request, code: str) -> Response:
        """Get test questions by code without answers."""
        try:
            test = Test.objects.prefetch_related("questions__answers").get(code=code, is_active=True)
        except Test.DoesNotExist:
            raise NotFound("Test with this code not found.")

        return Response(
            RetrieveTestByCodeResponseSerializer(
                {
                    "test_id": test.id,
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
                        for q in test.questions.all()
                    ],
                }
            ).data
        )
