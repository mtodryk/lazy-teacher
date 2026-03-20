from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Document
from ..services.rag import retrieve_chunks
from .serializers import SearchRequestSerializer, SearchSuccessResponseSerializer


class GetRelevantChunks(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SearchRequestSerializer

    def post(self, request: Request) -> Response:
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            doc = Document.objects.get(
                id=data["document_id"],
                user=request.user,
                status=Document.Status.READY,
            )
        except Document.DoesNotExist:
            raise NotFound("Document not found or not ready.")

        hits = retrieve_chunks(
            query=data["query"],
            doc_id=doc.id,
            user_id=request.user.id,
            n_results=data["n_results"],
        )

        response_data = {
            "query": data["query"],
            "document_id": doc.id,
            "hits": [
                {
                    "text": h.text,
                    "chunk_idx": h.chunk_idx,
                    "distance": h.distance,
                    "source": h.source,
                }
                for h in hits
            ],
            "count": len(hits),
        }
        return Response(SearchSuccessResponseSerializer(response_data).data)
