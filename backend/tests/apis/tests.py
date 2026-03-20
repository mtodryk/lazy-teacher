from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Test
from ..serializers import TestResponseSerializer


class ListTests(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TestResponseSerializer

    def get(self, request: Request) -> Response:
        serializer = TestResponseSerializer(
            Test.objects.filter(user=request.user).prefetch_related(
                "questions__answers"
            ),
            many=True,
        )
        return Response(serializer.data)


class TestDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TestResponseSerializer

    def _get_test(self, test_id: int, user):
        try:
            return Test.objects.prefetch_related("questions__answers").get(
                id=test_id, user=user
            )
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

    def get(self, request: Request, test_id: int) -> Response:
        test = self._get_test(test_id, request.user)
        return Response(TestResponseSerializer(test).data)

    def delete(self, request: Request, test_id: int) -> Response:
        test = self._get_test(test_id, request.user)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
