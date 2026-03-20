from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ..models import Document, TopicExtractionResult
from ..tasks import extract_topics_task
from .serializers import TopicExtractionResponseSerializer


class ExtractTopics(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicExtractionResponseSerializer

    @extend_schema(responses={202: TopicExtractionResponseSerializer})
    def post(self, request: Request, doc_id: int) -> Response:
        try:
            doc = Document.objects.get(
                id=doc_id,
                user=request.user,
                status=Document.Status.READY,
            )
        except Document.DoesNotExist:
            raise NotFound("Document not found or not ready.")

        extract_topics_task.delay(doc.id, request.user.id)

        return Response(
            {
                "document_id": doc.id,
                "status": "processing",
                "message": "Topic extraction started.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TopicExtractionDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicExtractionResponseSerializer

    def get(self, request: Request, doc_id: int) -> Response:
        try:
            result = TopicExtractionResult.objects.select_related("document").get(
                document_id=doc_id,
                document__user=request.user,
            )
        except TopicExtractionResult.DoesNotExist:
            raise NotFound("No topic extraction found for this document.")

        return Response(TopicExtractionResponseSerializer(result).data)
