from django.urls import path

from .apis import (
    ListCreateQuestions,
    QuestionDetail,
    ListCreateTests,
    TestDetail,
)

urlpatterns = [
    path("questions/", ListCreateQuestions.as_view(), name="list_create_questions"),
    path("questions/<int:question_id>/", QuestionDetail.as_view(), name="question_detail"),

    path("tests/", ListCreateTests.as_view(), name="list_create_tests"),
    path("tests/<int:test_id>/", TestDetail.as_view(), name="test_detail"),
]
