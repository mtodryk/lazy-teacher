
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated  # Or IsAuthenticated if you want to restrict
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from ..models import Test, Question, Answer, TestSubmission, SubmittedAnswer
from ..serializers import TestSubmissionSerializer, TestSubmissionResponseSerializer, TestSubmissionDetailSerializer


class SubmitTest(APIView):
    permission_classes = [AllowAny]  # Anyone can submit
    serializer_class = TestSubmissionSerializer

    def _get_test(self, test_id: int):
        try:
            return Test.objects.prefetch_related("questions__answers").get(id=test_id, is_active=True)
        except Test.DoesNotExist:
            raise NotFound("Test not found or inactive.")

    @extend_schema(
        request=TestSubmissionSerializer,
        responses={200: TestSubmissionResponseSerializer},
    )
    def post(self, request: Request, test_id: int) -> Response:
        test = self._get_test(test_id)
        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        answers_data = serializer.validated_data["answers"]

        # Build a dict of question_id -> selected_answer_id
        submitted_answers = {ans["question"]: ans["answer_id"] for ans in answers_data}

        # Validate questions exist and belong to the test
        question_ids = set(submitted_answers.keys())
        questions = {q.id: q for q in test.questions.all()}
        if question_ids != set(questions.keys()):
            raise ValidationError("Submitted questions do not match the test.")

        # Calculate results
        score = 0
        max_score = len(questions)
        response_answers = []

        for q_id, q in questions.items():
            selected_id = submitted_answers.get(q_id)
            selected_answer = None
            is_correct = False
            correct_answer_id = None

            # Find the correct answer (assume one correct per question)
            for ans in q.answers.all():
                if ans.is_correct:
                    correct_answer_id = ans.id
                if ans.id == selected_id:
                    selected_answer = ans
                    is_correct = ans.is_correct

            if is_correct:
                score += 1

            response_answers.append({
                "question_id": q_id,
                "correct_answer_id": correct_answer_id,
                "selected_answer_id": selected_id,
                "is_correct": is_correct,
            })

        percentage = (score / max_score) * 100 if max_score > 0 else 0
        passed = percentage >= 50  # More than half to pass, adjust if needed

        # Save to database
        submission = TestSubmission.objects.create(
            test=test,
            student_name=name,
            score=score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
        )
        for ans_data in response_answers:
            SubmittedAnswer.objects.create(
                submission=submission,
                question=questions[ans_data["question_id"]],
                selected_answer=selected_answer,
                is_correct=ans_data["is_correct"],
            )

        response_serializer = TestSubmissionResponseSerializer({
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "passed": passed,
            "answers": response_answers,
        })
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# View for submissions
User = get_user_model()

class TestSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_test(self, test_id: int, user: User):
        try:
            return Test.objects.get(id=test_id, user=user)  # Filtr po właścicielu!
        except Test.DoesNotExist:
            raise NotFound("Test not found or you don't have permission.")

    @extend_schema(
        responses={200: TestSubmissionDetailSerializer(many=True)},
    )
    def get(self, request: Request, test_id: int) -> Response:
        test = self._get_test(test_id, request.user)
        submissions = TestSubmission.objects.filter(test=test).prefetch_related(
            "submitted_answers__question__answers",  # Dla correct_answer_id
            "submitted_answers__selected_answer"
        )
        serializer = TestSubmissionDetailSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)