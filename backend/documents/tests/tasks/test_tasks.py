import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from documents.models import Document, TopicExtractionResult
from tests.models import Test
from documents.tasks import (
    process_pdf_upload,
    delete_document_vectors_task,
    extract_topics_task,
    generate_quiz_task,
    _validate_quiz_prerequisites,
    _generate_quiz_data,
    _save_quiz,
    ERROR_STATUS,
    SUCCESS_STATUS,
)


@pytest.mark.django_db
class TestProcessPdfUploadTask:

    @patch("documents.services.pdf_processor.extract_and_chunk_pdf")
    @patch("documents.services.s3_client.S3Client")
    @patch("documents.services.vector_store.ChromaVectorStore")
    @patch("documents.tasks._extract_and_save_topics")
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_process_pdf_upload_success(
        self,
        mock_remove,
        mock_exists,
        mock_extract_topics,
        mock_vector_store,
        mock_s3_client,
        mock_extract_chunk,
        user,
        pending_document,
    ):
        mock_extract_chunk.return_value = ["chunk1", "chunk2"]
        mock_vector_store_instance = MagicMock()
        mock_vector_store.return_value = mock_vector_store_instance

        result = process_pdf_upload(
            doc_id=pending_document.id,
            temp_file_path="/tmp/test.pdf",
            user_id=user.id,
            file_name="test.pdf",
        )

        pending_document.refresh_from_db()
        assert result["status"] == SUCCESS_STATUS
        assert result["chunks"] == 2
        assert pending_document.status == Document.Status.READY
        assert pending_document.chunk_count == 2

        mock_s3_client.return_value.upload_file.assert_called_once()
        mock_vector_store_instance.add_documents.assert_called_once()
        mock_extract_topics.assert_called_once()
        mock_remove.assert_called_once_with("/tmp/test.pdf")

    @patch("documents.services.pdf_processor.extract_and_chunk_pdf")
    @patch("documents.services.s3_client.S3Client")
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_process_pdf_upload_no_text(
        self,
        mock_remove,
        mock_exists,
        mock_s3_client,
        mock_extract_chunk,
        user,
        pending_document,
    ):
        mock_extract_chunk.return_value = []

        result = process_pdf_upload(
            doc_id=pending_document.id,
            temp_file_path="/tmp/test.pdf",
            user_id=user.id,
            file_name="test.pdf",
        )

        pending_document.refresh_from_db()
        assert result["status"] == ERROR_STATUS
        assert result["message"] == "No text extracted"
        assert pending_document.status == Document.Status.ERROR
        mock_remove.assert_called_once()

    @patch("documents.services.pdf_processor.extract_and_chunk_pdf")
    @patch("documents.services.s3_client.S3Client")
    def test_process_pdf_upload_exception(
        self,
        mock_s3_client,
        mock_extract_chunk,
        user,
        pending_document,
    ):
        mock_extract_chunk.side_effect = Exception("Test Error")

        # We need to mock the retry behavior or handle the raised exception
        with patch("celery.app.task.Task.retry") as mock_retry:
            mock_retry.side_effect = Exception("Retry Triggered")

            with pytest.raises(Exception, match="Retry Triggered"):
                process_pdf_upload(
                    doc_id=pending_document.id,
                    temp_file_path="/tmp/test.pdf",
                    user_id=user.id,
                    file_name="test.pdf",
                )

            pending_document.refresh_from_db()
            assert pending_document.status == Document.Status.ERROR
            assert "Test Error" in pending_document.error_message


@pytest.mark.django_db
class TestDeleteDocumentVectorsTask:

    @patch("documents.services.vector_store.ChromaVectorStore")
    @patch("documents.services.s3_client.S3Client")
    def test_delete_vectors_success(self, mock_s3_client, mock_vector_store):
        mock_vector_store_instance = MagicMock()
        mock_vector_store.return_value = mock_vector_store_instance

        result = delete_document_vectors_task(doc_id=1, s3_key="somedir/key.pdf")

        assert result["status"] == SUCCESS_STATUS
        assert result["document_id"] == 1
        mock_vector_store_instance.delete.assert_called_once_with(where={"doc_id": "1"})
        mock_s3_client.return_value.delete_file.assert_called_once_with(
            "somedir/key.pdf"
        )

    @patch("documents.services.vector_store.ChromaVectorStore")
    def test_delete_vectors_exception(self, mock_vector_store):
        mock_vector_store_instance = MagicMock()
        mock_vector_store_instance.delete.side_effect = Exception("Del Error")
        mock_vector_store.return_value = mock_vector_store_instance

        with patch("celery.app.task.Task.retry") as mock_retry:
            mock_retry.side_effect = Exception("Retry Triggered")

            with pytest.raises(Exception, match="Retry Triggered"):
                delete_document_vectors_task(doc_id=1)


@pytest.mark.django_db
class TestExtractTopicsTask:

    @patch("documents.services.vector_store.ChromaVectorStore")
    @patch("documents.services.topic_extraction.extract_topics")
    def test_extract_topics_success(
        self, mock_extract_topics, mock_vector_store, document
    ):
        mock_vector_store_instance = MagicMock()
        mock_vector_store_instance.get_all_documents.return_value = ["chunk1", "chunk2"]
        mock_vector_store.return_value = mock_vector_store_instance

        mock_extract_topics.return_value = ["Topic 1", "Topic 2"]

        result = extract_topics_task(doc_id=document.id, user_id=document.user.id)

        assert result["status"] == SUCCESS_STATUS
        assert result["topic_count"] == 2

        extraction_result = TopicExtractionResult.objects.get(document=document)
        assert extraction_result.topics == ["Topic 1", "Topic 2"]
        assert extraction_result.chunk_count_used == 2

    def test_extract_topics_doc_not_found(self):
        result = extract_topics_task(doc_id=999, user_id=999)
        assert result["status"] == ERROR_STATUS
        assert result["message"] == "Document not found"

    @patch("documents.services.vector_store.ChromaVectorStore")
    def test_extract_topics_no_chunks(self, mock_vector_store, document):
        mock_vector_store_instance = MagicMock()
        mock_vector_store_instance.get_all_documents.return_value = []
        mock_vector_store.return_value = mock_vector_store_instance

        result = extract_topics_task(doc_id=document.id, user_id=document.user.id)

        assert result["status"] == ERROR_STATUS
        assert result["message"] == "No chunks found"

        document.refresh_from_db()
        assert "No chunks found" in document.error_message


@pytest.mark.django_db
class TestGenerateQuizTask:

    def test_validate_prerequisites_user_not_found(self):
        user, doc, topics = _validate_quiz_prerequisites(doc_id=1, user_id=999)
        assert user is None
        assert topics["status"] == ERROR_STATUS
        assert topics["message"] == "User not found"

    def test_validate_prerequisites_doc_not_found(self, user):
        user_res, doc, topics = _validate_quiz_prerequisites(
            doc_id=999, user_id=user.id
        )
        assert user_res is None
        assert topics["status"] == ERROR_STATUS
        assert "Document not found" in topics["message"]

    def test_validate_prerequisites_no_topics(self, user, document):
        # document has status READY, but we need TOPICS_EXTRACTED
        document.status = Document.Status.TOPICS_EXTRACTED
        document.save()

        user_res, doc, topics = _validate_quiz_prerequisites(
            doc_id=document.id, user_id=user.id
        )
        assert user_res is None
        assert topics["status"] == ERROR_STATUS
        assert "Topics not extracted" in topics["message"]

    @patch("documents.services.chroma_client.get_chroma_collection")
    @patch("documents.services.topic_extraction.generate_rag_quiz")
    def test_generate_quiz_data_success(self, mock_generate_rag_quiz, mock_collection):
        mock_generate_rag_quiz.return_value = [{"q": "test"}]
        data, error = _generate_quiz_data(1, ["Topic"])
        assert data == [{"q": "test"}]
        assert error is None

    @patch("documents.services.quiz.create_quiz_from_topics")
    def test_save_quiz_success(self, mock_create_quiz, user, document):
        test_obj = Test(id=1, user=user)
        mock_create_quiz.return_value = test_obj

        saved_test, error = _save_quiz(user, document, [{"q": "test"}])
        assert saved_test == test_obj
        assert error is None

    @patch("documents.tasks._validate_quiz_prerequisites")
    @patch("documents.tasks._generate_quiz_data")
    @patch("documents.tasks._save_quiz")
    def test_generate_quiz_task_success(
        self, mock_save_quiz, mock_generate_data, mock_validate, user, document
    ):
        mock_validate.return_value = (user, document, ["Topic 1"])
        mock_generate_data.return_value = ([{"q": "test"}], None)
        test_obj = MagicMock()
        test_obj.id = 100
        mock_save_quiz.return_value = (test_obj, None)

        result = generate_quiz_task(
            doc_id=1, user_id=user.id, count=1, max_distance=0.5, chunks_per_question=2
        )

        assert result["status"] == SUCCESS_STATUS
        assert result["test_id"] == 100
        assert result["question_count"] == 1

    @patch("documents.tasks._validate_quiz_prerequisites")
    @patch("documents.tasks._generate_quiz_data")
    def test_generate_quiz_task_generate_error(
        self, mock_generate_data, mock_validate, user, document
    ):
        mock_validate.return_value = (user, document, ["Topic 1"])
        mock_generate_data.return_value = (
            [],
            {"status": ERROR_STATUS, "message": "Gen Err"},
        )

        result = generate_quiz_task(doc_id=1, user_id=user.id)
        assert result["status"] == ERROR_STATUS
        assert result["message"] == "Gen Err"

    @patch("documents.tasks._validate_quiz_prerequisites")
    def test_generate_quiz_task_exception(self, mock_validate):
        mock_validate.side_effect = Exception("Unexpected")

        with patch("celery.app.task.Task.retry") as mock_retry:
            mock_retry.side_effect = Exception("Retry Triggered")

            with pytest.raises(Exception, match="Retry Triggered"):
                generate_quiz_task(doc_id=1, user_id=1)
