from django.urls import path

from .apis import (
    AnswerDetail,
    ListTests,
    QuestionDetail,
    TestDetail,
    TestQuestions,
    ShareLink,
    RetrieveTestByCode,
)

urlpatterns = [
    path("", ListTests.as_view(), name="list_tests"),
    path("<int:test_id>/", TestDetail.as_view(), name="test_detail"),
    path(
        "<int:test_id>/questions/",
        TestQuestions.as_view(),
        name="test_questions",
    ),
    path(
        "<int:test_id>/questions/<int:question_id>/",
        QuestionDetail.as_view(),
        name="question_detail",
    ),
    path(
        "<int:test_id>/questions/<int:question_id>/answers/<int:answer_id>/",
        AnswerDetail.as_view(),
        name="answer_detail",
    ),
    path(
        "<int:test_id>/generate-link/",
        ShareLink.as_view(),
        name="generate_share_link",
    ),
    path(
        "by-code/<str:code>/",
        RetrieveTestByCode.as_view(),
        name="retrieve_test_by_code",
    ),
]
