from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ..models import Document
from ..tasks import delete_document_vectors_task
from .serializers import DocumentItemResponseSerializer


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

        delete_document_vectors_task.delay(doc.id)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
