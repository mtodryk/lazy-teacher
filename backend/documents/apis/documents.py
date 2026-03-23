from django.conf import settings as django_settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from settings.utils import ApplicationError
from ..models import Document
from ..services.s3_client import S3Client
from ..tasks import delete_document_vectors_task
from .serializers import DocumentItemResponseSerializer, DocumentURLResponseSerializer


class ListDocuments(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentItemResponseSerializer

    def get(self, request: Request) -> Response:
        serializer = DocumentItemResponseSerializer(
            Document.objects.filter(user=request.user), many=True
        )
        return Response(serializer.data)


class DocumentApi(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentItemResponseSerializer

    def get(self, request: Request, doc_id: int) -> Response:
        """Retrieve a single document by ID."""
        try:
            doc = Document.objects.get(id=doc_id, user=request.user)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        serializer = DocumentItemResponseSerializer(doc)
        return Response(serializer.data)

    @extend_schema(responses={204: None})
    def delete(self, request: Request, doc_id: int) -> Response:
        try:
            doc = Document.objects.get(id=doc_id, user=request.user)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        delete_document_vectors_task.delay(doc.id, s3_key=doc.s3_key)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadURL(APIView):
    """Generate a presigned S3 URL to download the original document."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get presigned download URL for a document",
        responses={200: DocumentURLResponseSerializer},
    )
    def get(self, request: Request, doc_id: int) -> Response:
        try:
            doc = Document.objects.get(id=doc_id, user=request.user)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        if not doc.s3_key:
            raise ApplicationError(message="Document file is not available")

        expiry = django_settings.AWS_S3_PRESIGNED_URL_EXPIRY
        url = S3Client().generate_presigned_url(
            doc.s3_key,
            filename=doc.file_name,
            expiration=expiry,
        )
        return Response(
            DocumentURLResponseSerializer(
                {"document_id": doc.id, "url": url, "expires_in": expiry}
            ).data
        )
