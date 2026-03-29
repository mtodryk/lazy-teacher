from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from settings.utils import ApplicationError
from ..models import TopicExtractionResult
from .serializers import (
    TopicAddRequestSerializer,
    TopicDeleteRequestSerializer,
    TopicExtractionResponseSerializer,
)


class TopicExtractionDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicExtractionResponseSerializer

    @extend_schema(
        summary="Get topic extraction result for a document",
        responses={200: TopicExtractionResponseSerializer},
    )
    def get(self, request: Request, doc_id: int) -> Response:
        try:
            result = TopicExtractionResult.objects.select_related("document").get(
                document_id=doc_id,
                document__user=request.user,
            )
        except TopicExtractionResult.DoesNotExist:
            raise ApplicationError(
                message="No topic extraction found for this document"
            )

        return Response(TopicExtractionResponseSerializer(result).data)


class ManageTopic(APIView):
    """Add or delete individual topics from a document's extraction result."""

    permission_classes = [IsAuthenticated]
    serializer_class = TopicExtractionResponseSerializer

    def _get_extraction(self, doc_id: int, user) -> TopicExtractionResult:
        try:
            return TopicExtractionResult.objects.select_related("document").get(
                document_id=doc_id,
                document__user=user,
            )
        except TopicExtractionResult.DoesNotExist:
            raise ApplicationError(
                message="No topic extraction found for this document"
            )

    @extend_schema(
        summary="Add a topic to the document's extracted topics",
        request=TopicAddRequestSerializer,
        responses={200: TopicExtractionResponseSerializer},
    )
    def post(self, request: Request, doc_id: int) -> Response:
        serializer = TopicAddRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = self._get_extraction(doc_id, request.user)
        topic = serializer.validated_data["topic"]

        if topic in result.topics:
            raise ApplicationError(message="Topic already exists")

        result.topics = result.topics + [topic]
        result.save(update_fields=["topics"])
        return Response(TopicExtractionResponseSerializer(result).data)

    @extend_schema(
        summary="Delete a topic from the document's extracted topics",
        request=TopicDeleteRequestSerializer,
        responses={200: TopicExtractionResponseSerializer},
    )
    def delete(self, request: Request, doc_id: int) -> Response:
        serializer = TopicDeleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = self._get_extraction(doc_id, request.user)
        topic = serializer.validated_data["topic"]

        if topic not in result.topics:
            raise ApplicationError(message="Topic not found")

        result.topics = [t for t in result.topics if t != topic]
        result.save(update_fields=["topics"])
        return Response(TopicExtractionResponseSerializer(result).data)
