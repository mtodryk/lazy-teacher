from django.urls import path

from .apis import (
    DeleteDocument,
    ExtractTopics,
    GenerateQuiz,
    GetRelevantChunks,
    ListDocuments,
    TopicExtractionDetail,
    UploadPDF,
)

urlpatterns = [
    path("upload/", UploadPDF.as_view(), name="documents-upload"),
    path("search/", GetRelevantChunks.as_view(), name="documents-search"),
    path("documents/", ListDocuments.as_view(), name="documents-documents"),
    path(
        "documents/<int:doc_id>/",
        DeleteDocument.as_view(),
        name="documents-document-delete",
    ),
    path(
        "documents/<int:doc_id>/extract-topics/",
        ExtractTopics.as_view(),
        name="documents-extract-topics",
    ),
    path(
        "documents/<int:doc_id>/topics/",
        TopicExtractionDetail.as_view(),
        name="documents-topics-detail",
    ),
    path(
        "documents/<int:doc_id>/generate-quiz/",
        GenerateQuiz.as_view(),
        name="documents-generate-quiz",
    ),
]
