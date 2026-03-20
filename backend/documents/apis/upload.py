import logging
import os
import uuid

from django.conf import settings as django_settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from settings.utils import ApplicationError
from ..models import Document
from ..tasks import process_pdf_upload
from .serializers import UploadPDFRequestSerializer, UploadSuccessResponseSerializer

logger: logging.Logger = logging.getLogger(__name__)


class UploadPDF(APIView):
    """Upload PDF for RAG processing."""

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]
    serializer_class = UploadPDFRequestSerializer

    @extend_schema(
        summary="Wgraj plik PDF",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Plik PDF",
                    }
                },
                "required": ["file"],
            }
        },
        responses={202: UploadSuccessResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = UploadPDFRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]

        temp_dir = os.path.join(django_settings.BASE_DIR, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.pdf")

        try:
            with open(temp_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            doc = Document.objects.create(
                user=request.user,
                title=file.name,
                file_name=file.name,
                status=Document.Status.PENDING,
            )

            process_pdf_upload.delay(
                doc_id=doc.id,
                temp_file_path=temp_path,
                user_id=request.user.id,
                file_name=file.name,
            )

            response_data = {
                "document_id": doc.id,
                "status": "processing",
                "title": doc.title,
                "message": "Document queued for processing",
            }
            return Response(
                UploadSuccessResponseSerializer(response_data).data,
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception:
            logger.exception("Failed to queue PDF upload")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ApplicationError(message="Failed to queue document for processing")
