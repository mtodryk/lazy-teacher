import logging
import os
from typing import Dict, Any, Tuple, Union, Optional

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)

MAX_ERROR_MESSAGE_LENGTH = 500
ERROR_STATUS = "error"
SUCCESS_STATUS = "success"


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_pdf_upload(
    self, doc_id: int, temp_file_path: str, user_id: int, file_name: str
) -> Dict[str, Any]:
    from documents.models import Document
    from documents.services.vector_store import ChromaVectorStore
    from documents.services.pdf_processor import extract_and_chunk_pdf

    def _cleanup_temp_file() -> None:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                logger.warning(f"Could not remove temp file: {temp_file_path}")

    try:
        doc = Document.objects.get(id=doc_id)
        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=["status"])

        from documents.services.s3_client import S3Client

        s3_key = f"documents/{user_id}/{doc_id}.pdf"
        S3Client().upload_file(temp_file_path, s3_key)
        doc.s3_key = s3_key
        doc.save(update_fields=["s3_key"])

        chunks = extract_and_chunk_pdf(temp_file_path)

        if not chunks:
            doc.status = Document.Status.ERROR
            doc.error_message = "No text could be extracted from PDF"
            doc.save(update_fields=["status", "error_message"])
            logger.warning(f"No text extracted from document {doc_id}")
            _cleanup_temp_file()
            return {
                "status": ERROR_STATUS,
                "message": "No text extracted",
            }

        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "user_id": str(user_id),
                "doc_id": str(doc_id),
                "chunk_idx": i,
                "source": file_name,
            }
            for i in range(len(chunks))
        ]

        ChromaVectorStore().add_documents(
            documents=chunks, ids=ids, metadatas=metadatas
        )

        doc.chunk_count = len(chunks)
        doc.status = Document.Status.READY
        doc.save(update_fields=["chunk_count", "status"])

        logger.info(f"Document {doc_id} processed: {len(chunks)} chunks")
        _cleanup_temp_file()

        _extract_and_save_topics(doc, chunks)

        return {
            "status": SUCCESS_STATUS,
            "document_id": doc_id,
            "chunks": len(chunks),
        }

    except Exception as exc:
        logger.exception(f"Failed to process document {doc_id}")
        try:
            doc = Document.objects.get(id=doc_id)
            doc.status = Document.Status.ERROR
            doc.error_message = str(exc)[:MAX_ERROR_MESSAGE_LENGTH]
            doc.save(update_fields=["status", "error_message"])
        except Document.DoesNotExist:
            pass

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        _cleanup_temp_file()
        raise


def _extract_and_save_topics(doc: "Document", chunks: list) -> None:
    """Extract topics from document chunks and save to database."""
    try:
        from documents.services.topic_extraction import extract_topics
        from documents.models import TopicExtractionResult, Document
        from django.conf import settings as django_settings

        topics = extract_topics(chunks)

        with transaction.atomic():
            TopicExtractionResult.objects.update_or_create(
                document=doc,
                defaults={
                    "topics": topics,
                    "model_used": django_settings.AZURE_OPENAI_DEPLOYMENT,
                    "chunk_count_used": len(chunks),
                },
            )
            doc.refresh_from_db()
            doc.status = Document.Status.TOPICS_EXTRACTED
            doc.save(update_fields=["status"])

        logger.info(f"Extracted {len(topics)} topics for document {doc.id}")
    except Exception:
        logger.exception(f"Topic extraction failed for document {doc.id}")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def delete_document_vectors_task(self, doc_id: int, s3_key: str = "") -> Dict[str, Any]:
    """Delete document vectors from database and associated S3 file."""
    from documents.services.vector_store import ChromaVectorStore

    try:
        vector_store = ChromaVectorStore()
        vector_store.delete(where={"doc_id": str(doc_id)})

        if s3_key:
            from documents.services.s3_client import S3Client

            S3Client().delete_file(s3_key)

        logger.info(f"Deleted vectors and S3 file for document {doc_id}")
        return {"status": SUCCESS_STATUS, "document_id": doc_id}

    except Exception as exc:
        logger.exception(f"Failed to delete resources for document {doc_id}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def extract_topics_task(self, doc_id: int, user_id: int) -> Dict[str, Any]:
    """Extract topics from document chunks."""
    from documents.models import Document, TopicExtractionResult
    from documents.services.vector_store import ChromaVectorStore
    from documents.services.topic_extraction import extract_topics
    from django.conf import settings

    try:
        doc = Document.objects.get(id=doc_id, user_id=user_id)
    except Document.DoesNotExist:
        logger.error(f"Document {doc_id} not found for topic extraction")
        return {"status": ERROR_STATUS, "message": "Document not found"}

    try:
        chunks = ChromaVectorStore().get_all_documents(
            where={"doc_id": str(doc_id), "user_id": str(user_id)}
        )

        if not chunks:
            doc.error_message = "No chunks found in vector store"
            doc.save(update_fields=["error_message"])
            return {"status": ERROR_STATUS, "message": "No chunks found"}

        topics = extract_topics(chunks)

        TopicExtractionResult.objects.update_or_create(
            document=doc,
            defaults={
                "topics": topics,
                "model_used": settings.AZURE_OPENAI_DEPLOYMENT,
                "chunk_count_used": len(chunks),
            },
        )

        logger.info(f"Extracted {len(topics)} topics for document {doc_id}")
        return {
            "status": SUCCESS_STATUS,
            "document_id": doc_id,
            "topic_count": len(topics),
        }

    except Exception as exc:
        logger.exception(f"Failed to extract topics for document {doc_id}")
        doc.error_message = (
            f"Topic extraction failed: {str(exc)[:MAX_ERROR_MESSAGE_LENGTH]}"
        )
        doc.save(update_fields=["error_message"])

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


def _validate_quiz_prerequisites(
    doc_id: int, user_id: int
) -> Union[Tuple[Any, Any, Any], Tuple[None, None, Dict[str, Any]]]:
    """Validate user, document, and topic extraction status.

    Returns:
        Tuple of (user, document, topics) or (None, None, error_dict) if validation fails
    """
    try:
        user = User.objects.get(id=user_id)
    except ObjectDoesNotExist:
        return (
            None,
            None,
            {
                "status": ERROR_STATUS,
                "message": "User not found",
            },
        )

    from documents.models import Document, TopicExtractionResult

    try:
        doc = Document.objects.get(
            id=doc_id, user=user, status=Document.Status.TOPICS_EXTRACTED
        )
    except ObjectDoesNotExist:
        return (
            None,
            None,
            {
                "status": ERROR_STATUS,
                "message": "Document not found or not analyzed",
                "details": {"doc_id": doc_id},
            },
        )

    try:
        topics = TopicExtractionResult.objects.get(document=doc).topics
    except ObjectDoesNotExist:
        return (
            None,
            None,
            {
                "status": ERROR_STATUS,
                "message": "Topics not extracted",
                "details": {"doc_id": doc_id},
            },
        )

    if not topics:
        return (
            None,
            None,
            {
                "status": ERROR_STATUS,
                "message": "No topics available",
            },
        )

    return user, doc, topics


def _generate_quiz_data(
    doc_id: int,
    topics: list,
    count: int = 5,
    max_distance: float = 0.5,
    chunks_per_question: int = 3,
) -> Tuple[list, Optional[Dict[str, Any]]]:
    """Generate quiz questions from topics.

    Returns:
        Tuple of (quiz_data, error_dict) or (quiz_data, None) on success
    """
    from documents.services.chroma_client import get_chroma_collection
    from documents.services.topic_extraction import generate_rag_quiz

    try:
        quiz_data = generate_rag_quiz(
            topics=topics,
            count=count,
            collection=get_chroma_collection(),
            max_distance=max_distance,
            chunks_per_question=chunks_per_question,
            doc_id=doc_id,
        )
        return quiz_data, None
    except Exception as e:
        logger.exception(f"Quiz generation failed for doc {doc_id}")
        return [], {
            "status": ERROR_STATUS,
            "message": "Quiz generation failed",
            "details": {"error_type": type(e).__name__},
        }


def _save_quiz(
    user: "User", doc: "Document", quiz_data: list
) -> Tuple[Optional["Test"], Optional[Dict[str, Any]]]:
    """Save generated quiz to database.

    Returns:
        Tuple of (test_object, error_dict) or (test_object, None) on success
    """
    from documents.services.quiz import create_quiz_from_topics

    try:
        test = create_quiz_from_topics(user, doc, quiz_data)
        return test, None
    except Exception as e:
        logger.exception(f"Failed to create quiz for doc {doc.id}")
        return None, {
            "status": ERROR_STATUS,
            "message": "Failed to save quiz to database",
            "details": {"error_type": type(e).__name__},
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_quiz_task(
    self,
    doc_id: int,
    user_id: int,
    count: int = 5,
    max_distance: float = 0.5,
    chunks_per_question: int = 3,
) -> Dict[str, Any]:
    """Generate quiz from document topics using RAG."""
    try:
        user, doc, topics = _validate_quiz_prerequisites(doc_id, user_id)
        if user is None:
            return topics

        quiz_data, error = _generate_quiz_data(
            doc_id, topics, count, max_distance, chunks_per_question
        )
        if error:
            return error

        if not quiz_data:
            return {
                "status": ERROR_STATUS,
                "message": "Failed to generate quiz questions",
            }

        test, error = _save_quiz(user, doc, quiz_data)
        if error:
            return error

        logger.info(
            f"Quiz generated for document {doc_id}: test_id={test.id}, "
            f"questions={len(quiz_data)}"
        )
        return {
            "status": SUCCESS_STATUS,
            "test_id": test.id,
            "question_count": len(quiz_data),
        }

    except Exception as exc:
        logger.exception(f"Unexpected error generating quiz for document {doc_id}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {
            "status": ERROR_STATUS,
            "message": "Unexpected error during quiz generation",
            "details": {"error_type": type(exc).__name__},
        }
