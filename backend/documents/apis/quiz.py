from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from tests.models import Test
from tests.serializers import TestResponseSerializer

from ..models import Document, TopicExtractionResult
from ..services.chroma_client import get_chroma_collection
from ..services.topic_extraction import generate_rag_quiz
from ..services.quiz import create_quiz_from_topics
from .serializers import QuizRequestSerializer


class GenerateQuiz(APIView):
    permission_classes = [IsAuthenticated]
    #throttle_classes = [ScopedRateThrottle]
    # throttle_scope = "expensive_operation"
    serializer_class = QuizRequestSerializer

    def post(self, request: Request, doc_id: int) -> Response:
        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)
        data = data.validated_data

        doc = Document.objects.get(
            id=doc_id, user=request.user, status=Document.Status.READY
        )
        topics = TopicExtractionResult.objects.get(document=doc).topics

        if not topics:
            raise ValidationError("No topics available for this document.")

        quiz_data = generate_rag_quiz(
            topics=topics,
            count=data["count"],
            collection=get_chroma_collection(),
            max_distance=data["max_distance"],
            chunks_per_question=data["chunks_per_question"],
        )

        if not quiz_data:
            raise ValidationError("No questions could be generated.")

        test = create_quiz_from_topics(request.user, doc, quiz_data)
        test = Test.objects.prefetch_related("questions__answers").get(pk=test.pk)

        return Response(
            {
                "test_id": test.id,
                "test": TestResponseSerializer(test).data,
            },
            status=201,
        )
