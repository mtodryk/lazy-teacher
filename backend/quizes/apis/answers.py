from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from settings.utils import ApplicationError
from ..models import Answer
from ..serializers import QuestionResponseSerializer


class AnswerDetail(APIView):
    """DELETE a single answer from a question."""

    permission_classes = [IsAuthenticated]
    serializer_class = QuestionResponseSerializer

    def delete(
        self, request: Request, quiz_id: int, question_id: int, answer_id: int
    ) -> Response:
        try:
            answer = Answer.objects.select_related("question__test").get(
                id=answer_id,
                question_id=question_id,
                question__quiz_id=quiz_id,
                question__test__user=request.user,
            )
        except Answer.DoesNotExist:
            raise NotFound("Answer not found.")

        # Prevent deleting the last correct answer
        remaining_correct = (
            Answer.objects.filter(question_id=question_id, is_correct=True)
            .exclude(id=answer_id)
            .count()
        )
        if answer.is_correct and remaining_correct == 0:
            raise ApplicationError(
                message="Cannot delete the only correct answer. Update another answer to be correct first.",
                extra={"answer_id": answer_id},
            )

        answer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
