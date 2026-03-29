from django.urls import path

from .apis import (
    DocumentApi,
    DocumentDownloadURL,
    GenerateQuiz,
    GetRelevantChunks,
    ListDocuments,
    ManageTopic,
    QuizTaskStatus,
    TopicExtractionDetail,
    UploadPDF,
)

urlpatterns = [
    path("upload/", UploadPDF.as_view(), name="documents-upload"),
    path("search/", GetRelevantChunks.as_view(), name="documents-search"),
    path("", ListDocuments.as_view(), name="documents-documents"),
    path(
        "<int:doc_id>/",
        DocumentApi.as_view(),
        name="documents-document-detail",
    ),
    path(
        "<int:doc_id>/download-url/",
        DocumentDownloadURL.as_view(),
        name="documents-download-url",
    ),
    path(
        "<int:doc_id>/topics/",
        TopicExtractionDetail.as_view(),
        name="documents-topics-detail",
    ),
    path(
        "<int:doc_id>/topics/manage/",
        ManageTopic.as_view(),
        name="documents-topic-manage",
    ),
    path(
        "<int:doc_id>/generate-quiz/",
        GenerateQuiz.as_view(),
        name="documents-generate-quiz",
    ),
    path(
        "quiz-task/<str:task_id>/",
        QuizTaskStatus.as_view(),
        name="documents-quiz-task-status",
    ),
]
