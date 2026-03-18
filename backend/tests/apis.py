from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document

from .models import Question, Test
from .serializers import (
    QuestionCreateSerializer,
    QuestionResponseSerializer,
    TestCreateSerializer,
    TestResponseSerializer,
)


class ListCreateQuestions(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = QuestionResponseSerializer(
            Question.objects.filter(user=request.user),
            many=True,
        )
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = Question.objects.create(
            user=request.user,
            text=serializer.validated_data["text"],
        )
        return Response(QuestionResponseSerializer(question).data, status=status.HTTP_201_CREATED)


class QuestionDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, question_id: int, user):
        try:
            return Question.objects.get(id=question_id, user=user)
        except Question.DoesNotExist:
            raise NotFound("Question not found.")

    def get(self, request: Request, question_id: int) -> Response:
        question = self.get_object(question_id, request.user)
        return Response(QuestionResponseSerializer(question).data)

    def put(self, request: Request, question_id: int) -> Response:
        question = self.get_object(question_id, request.user)
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question.text = serializer.validated_data["text"]
        question.save(update_fields=["text"])
        return Response(QuestionResponseSerializer(question).data)

    def delete(self, request: Request, question_id: int) -> Response:
        question = self.get_object(question_id, request.user)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListCreateTests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = TestResponseSerializer(
            Test.objects.filter(user=request.user).prefetch_related("questions"),
            many=True,
        )
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = TestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            document = Document.objects.get(id=serializer.validated_data["document_id"], user=request.user)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        test = Test.objects.create(
            user=request.user,
            document=document,
            code=serializer.validated_data["code"],
        )

        question_ids = serializer.validated_data.get("question_ids", [])
        if question_ids:
            questions = list(
                Question.objects.filter(user=request.user, id__in=question_ids)
            )
            if len(questions) != len(set(question_ids)):
                raise NotFound("One or more questions were not found.")
            test.questions.set(questions)

        return Response(TestResponseSerializer(test).data, status=status.HTTP_201_CREATED)


class TestDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, test_id: int, user):
        try:
            return Test.objects.prefetch_related("questions").get(id=test_id, user=user)
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

    def get(self, request: Request, test_id: int) -> Response:
        test = self.get_object(test_id, request.user)
        return Response(TestResponseSerializer(test).data)

    def put(self, request: Request, test_id: int) -> Response:
        test = self.get_object(test_id, request.user)
        serializer = TestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["code"] != test.code:
            # enforce uniqueness per user
            if Test.objects.filter(user=request.user, code=serializer.validated_data["code"]).exclude(id=test.id).exists():
                raise PermissionDenied("Test code must be unique per user.")

        try:
            document = Document.objects.get(id=serializer.validated_data["document_id"], user=request.user)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        test.code = serializer.validated_data["code"]
        test.document = document
        test.save(update_fields=["code", "document"])

        question_ids = serializer.validated_data.get("question_ids", [])
        if question_ids is not None:
            questions = list(
                Question.objects.filter(user=request.user, id__in=question_ids)
            )
            if len(questions) != len(set(question_ids)):
                raise NotFound("One or more questions were not found.")
            test.questions.set(questions)

        return Response(TestResponseSerializer(test).data)

    def delete(self, request: Request, test_id: int) -> Response:
        test = self.get_object(test_id, request.user)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
