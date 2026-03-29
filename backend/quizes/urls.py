from django.urls import path

from .apis import (
    AnswerDetail,
    ListQuizes,
    QuestionDetail,
    QuizDetail,
    QuizQuestions,
    ShareLink,
    RetrieveQuizByCode,
    SubmitQuiz,
    QuizSubmissionsView,
)

urlpatterns = [
    path("", ListQuizes.as_view(), name="list_quizes"),
    path("<int:quiz_id>/", QuizDetail.as_view(), name="quiz_detail"),
    path(
        "<int:quiz_id>/questions/",
        QuizQuestions.as_view(),
        name="quiz_questions",
    ),
    path(
        "<int:quiz_id>/questions/<int:question_id>/",
        QuestionDetail.as_view(),
        name="question_detail",
    ),
    path(
        "<int:quiz_id>/questions/<int:question_id>/answers/<int:answer_id>/",
        AnswerDetail.as_view(),
        name="answer_detail",
    ),
    path(
        "<int:quiz_id>/generate-link/",
        ShareLink.as_view(),
        name="generate_share_link",
    ),
    path(
        "by-code/<str:code>/",
        RetrieveQuizByCode.as_view(),
        name="retrieve_quiz_by_code",
    ),
    path(
        "<int:quiz_id>/submit/",
        SubmitQuiz.as_view(),
        name="submit_quiz",
    ),
    path(
        "<int:quiz_id>/submissions/",
        QuizSubmissionsView.as_view(),
        name="quiz_submissions",
    ),
]
