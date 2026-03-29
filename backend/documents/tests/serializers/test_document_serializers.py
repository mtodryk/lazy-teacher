import pytest
from io import BytesIO
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.apis.serializers import (
    UploadPDFRequestSerializer,
    SearchRequestSerializer,
    QuizRequestSerializer,
    TopicAddRequestSerializer,
    TopicDeleteRequestSerializer,
    DocumentItemResponseSerializer,
    TopicExtractionResponseSerializer,
    DocumentURLResponseSerializer,
    UploadSuccessResponseSerializer,
    SearchHitResponseSerializer,
    SearchSuccessResponseSerializer,
)


class TestUploadPDFRequestSerializer:

    def test_valid_pdf_file(self):
        file = SimpleUploadedFile(
            "document.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert serializer.is_valid()

    def test_reject_non_pdf_file(self):
        file = SimpleUploadedFile(
            "document.txt", b"text content", content_type="text/plain"
        )
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_reject_file_with_pdf_in_name_but_wrong_extension(self):
        file = SimpleUploadedFile(
            "pdf_doc.docx", b"content", content_type="application/octet-stream"
        )
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert not serializer.is_valid()

    def test_case_insensitive_pdf_extension(self):
        file = SimpleUploadedFile(
            "document.PDF", b"%PDF-1.4 content", content_type="application/pdf"
        )
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert serializer.is_valid()

    @patch("django.conf.settings.RAG_MAX_UPLOAD_SIZE_MB", 1)
    def test_reject_file_too_large(self):
        large_content = b"%PDF-1.4 " + b"x" * (2 * 1024 * 1024)
        file = SimpleUploadedFile(
            "big.pdf", large_content, content_type="application/pdf"
        )
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_accept_file_within_size_limit(self):
        content = b"%PDF-1.4 " + b"x" * 1000
        file = SimpleUploadedFile("small.pdf", content, content_type="application/pdf")
        serializer = UploadPDFRequestSerializer(data={"file": file})
        assert serializer.is_valid()

    def test_missing_file(self):
        serializer = UploadPDFRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "file" in serializer.errors


class TestSearchRequestSerializer:

    def test_valid_search_request(self):
        data = {"document_id": 1, "query": "What is machine learning?", "n_results": 5}
        serializer = SearchRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_default_n_results(self):
        data = {"document_id": 1, "query": "test query"}
        serializer = SearchRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["n_results"] == 5

    def test_empty_query_rejected(self):
        data = {"document_id": 1, "query": ""}
        serializer = SearchRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_query_max_length(self):
        data = {"document_id": 1, "query": "x" * 2001}
        serializer = SearchRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_n_results_min_value(self):
        data = {"document_id": 1, "query": "test", "n_results": 0}
        serializer = SearchRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_n_results_max_value(self):
        data = {"document_id": 1, "query": "test", "n_results": 21}
        serializer = SearchRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_missing_document_id(self):
        data = {"query": "test"}
        serializer = SearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "document_id" in serializer.errors


class TestQuizRequestSerializer:

    def test_valid_quiz_request(self):
        data = {"count": 10, "max_distance": 0.5, "chunks_per_question": 3}
        serializer = QuizRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_defaults(self):
        serializer = QuizRequestSerializer(data={})
        assert serializer.is_valid()
        assert serializer.validated_data["count"] == 5
        assert serializer.validated_data["max_distance"] == 0.5
        assert serializer.validated_data["chunks_per_question"] == 3

    def test_count_min_value(self):
        serializer = QuizRequestSerializer(data={"count": 0})
        assert not serializer.is_valid()

    def test_count_max_value(self):
        serializer = QuizRequestSerializer(data={"count": 31})
        assert not serializer.is_valid()

    def test_max_distance_bounds(self):
        serializer = QuizRequestSerializer(data={"max_distance": -0.1})
        assert not serializer.is_valid()

        serializer = QuizRequestSerializer(data={"max_distance": 2.1})
        assert not serializer.is_valid()

    def test_chunks_per_question_bounds(self):
        serializer = QuizRequestSerializer(data={"chunks_per_question": 0})
        assert not serializer.is_valid()

        serializer = QuizRequestSerializer(data={"chunks_per_question": 11})
        assert not serializer.is_valid()


class TestTopicAddRequestSerializer:

    def test_valid_topic(self):
        serializer = TopicAddRequestSerializer(data={"topic": "Machine Learning"})
        assert serializer.is_valid()

    def test_empty_topic_rejected(self):
        serializer = TopicAddRequestSerializer(data={"topic": ""})
        assert not serializer.is_valid()

    def test_topic_max_length(self):
        serializer = TopicAddRequestSerializer(data={"topic": "x" * 501})
        assert not serializer.is_valid()

    def test_missing_topic(self):
        serializer = TopicAddRequestSerializer(data={})
        assert not serializer.is_valid()


class TestTopicDeleteRequestSerializer:

    def test_valid_topic(self):
        serializer = TopicDeleteRequestSerializer(data={"topic": "ML"})
        assert serializer.is_valid()

    def test_empty_topic_rejected(self):
        serializer = TopicDeleteRequestSerializer(data={"topic": ""})
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestDocumentItemResponseSerializer:

    def test_serializes_document(self, document):
        serializer = DocumentItemResponseSerializer(document)
        data = serializer.data
        assert data["id"] == document.id
        assert data["title"] == "Quiz Document"
        assert data["status"] == "ready"
        assert data["chunk_count"] == 10
        assert "uploaded_at" in data
        assert "error_message" in data

    def test_serializes_multiple_documents(self, user):
        from documents.models import Document

        Document.objects.create(user=user, title="Doc1", file_name="d1.pdf")
        Document.objects.create(user=user, title="Doc2", file_name="d2.pdf")
        docs = Document.objects.filter(user=user)
        serializer = DocumentItemResponseSerializer(docs, many=True)
        assert len(serializer.data) == 2


@pytest.mark.django_db
class TestTopicExtractionResponseSerializer:

    def test_serializes_extraction(self, document_with_topics, topic_extraction):
        serializer = TopicExtractionResponseSerializer(topic_extraction)
        data = serializer.data
        assert data["id"] == topic_extraction.id
        assert data["document"] == document_with_topics.id
        assert data["topics"] == ["Temat 1", "Temat 2", "Temat 3"]
        assert data["model_used"] == "gpt-4o"
        assert data["chunk_count_used"] == 5
        assert "extracted_at" in data


class TestDocumentURLResponseSerializer:

    def test_serializes_url_data(self):
        data = {
            "document_id": 1,
            "url": "https://s3.amazonaws.com/bucket/key?signature=abc",
            "expires_in": 3600,
        }
        serializer = DocumentURLResponseSerializer(data)
        assert serializer.data == data


class TestUploadSuccessResponseSerializer:

    def test_serializes_upload_response(self):
        data = {
            "document_id": 1,
            "status": "processing",
            "title": "test.pdf",
            "message": "Document queued for processing",
        }
        serializer = UploadSuccessResponseSerializer(data)
        assert serializer.data == data
