import logging

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Document, TopicExtractionResult
from ..services.chroma_client import get_chroma_collection
from ..services.topic_extraction import generate_rag_quiz
from .serializers import QuizRequestSerializer

logger = logging.getLogger(__name__)


class GenerateQuiz(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, doc_id: int) -> Response:
        serializer = QuizRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            doc = Document.objects.get(
                id=doc_id,
                user=request.user,
                status=Document.Status.READY,
            )
        except Document.DoesNotExist:
            raise NotFound("Document not found or not ready.")

        try:
            topic_result = TopicExtractionResult.objects.get(document=doc)
        except TopicExtractionResult.DoesNotExist:
            raise NotFound(
                "No topic extraction found for this document. Run extract-topics first."
            )

        topics = topic_result.topics
        if not topics:
            return Response(
                {"error": "No topics available for this document."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quiz = generate_rag_quiz(
                topics=topics,
                count=data["count"],
                collection=get_chroma_collection(),
                max_distance=data["max_distance"],
                chunks_per_question=data["chunks_per_question"],
            )
        except Exception:
            logger.exception("Quiz generation failed for document %s", doc_id)
            return Response(
                {"error": "Quiz generation failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "document_id": doc.id,
                "quiz": quiz,
                "count": len(quiz),
            }
        )
