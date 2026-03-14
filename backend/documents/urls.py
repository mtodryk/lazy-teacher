from django.urls import path

from .apis import (
    DeleteDocument,
    GetRelevantChunks,
    ListDocuments,
    UploadPDF,
)

urlpatterns = [
    path("upload/", UploadPDF.as_view(), name="rag-upload"),
    path("search/", GetRelevantChunks.as_view(), name="rag-search"),
    path("documents/", ListDocuments.as_view(), name="rag-documents"),
    path(
        "documents/<int:doc_id>/",
        DeleteDocument.as_view(),
        name="rag-document-delete",
    ),
]
