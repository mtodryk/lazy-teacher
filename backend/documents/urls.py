from django.urls import path

from .apis import (
    DocumentApi,
    DocumentDownloadURL,
    ExtractTopics,
    GenerateQuiz,
    GetRelevantChunks,
    ListDocuments,
    ManageTopic,
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
        "<int:doc_id>/extract-topics/",
        ExtractTopics.as_view(),
        name="documents-extract-topics",
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
]
