import logging

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from tests.models import Answer, Question, Test
from tests.utils import generate_share_code

from ..models import Document, TopicExtractionResult
from ..services.chroma_client import get_chroma_collection
from ..services.topic_extraction import generate_rag_quiz
from .serializers import QuizRequestSerializer

logger = logging.getLogger(__name__)


class GenerateQuiz(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizRequestSerializer

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

        if not quiz:
            return Response(
                {"error": "No questions could be generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                test = Test.objects.create(
                    user=request.user,
                    document=doc,
                    code=generate_share_code(doc.id),
                )

                for q_data in quiz:
                    question = Question.objects.create(
                        test=test,
                        text=q_data["question"],
                        topic=q_data.get("topic", ""),
                    )

                    options = q_data.get("options", [])
                    correct_idx = q_data.get("correct_index", -1)

                    answers_to_create = []
                    for idx, option_text in enumerate(options):
                        answers_to_create.append(
                            Answer(
                                question=question,
                                text=option_text,
                                is_correct=(idx == correct_idx),
                            )
                        )
                    Answer.objects.bulk_create(answers_to_create)
        except Exception:
            logger.exception("Failed to save quiz to database for document %s", doc_id)
            return Response(
                {"error": "Failed to save quiz. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        from tests.serializers import TestResponseSerializer

        test = Test.objects.prefetch_related("questions__answers").get(id=test.id)

        return Response(
            {
                "test_id": test.id,
                "test": TestResponseSerializer(test).data,
            },
            status=status.HTTP_201_CREATED,
        )
