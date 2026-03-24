import logging
import os

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_pdf_upload(
    self, doc_id: int, temp_file_path: str, user_id: int, file_name: str
):
    from documents.models import Document
    from documents.services.vector_store import ChromaVectorStore
    from documents.services.pdf_processor import extract_and_chunk_pdf

    def _cleanup_temp_file():
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

        # Extract and chunk PDF
        chunks = extract_and_chunk_pdf(temp_file_path)

        if not chunks:
            doc.status = Document.Status.ERROR
            doc.error_message = "No text could be extracted from PDF"
            doc.save(update_fields=["status", "error_message"])
            logger.warning(f"No text extracted from document {doc_id}")
            _cleanup_temp_file()
            return {"status": "error", "message": "No text extracted"}

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

        # ZMIANA 1: Aktualizujemy tylko liczbę chunków. Usuwamy stąd nadawanie statusu READY
        doc.chunk_count = len(chunks)
        doc.save(update_fields=["chunk_count"])

        logger.info(f"Document {doc_id} processed: {len(chunks)} chunks")
        _cleanup_temp_file()

        try:
            from documents.services.topic_extraction import extract_topics
            from documents.models import TopicExtractionResult
            from django.conf import settings as django_settings

            topics = extract_topics(chunks)
            TopicExtractionResult.objects.update_or_create(
                document=doc,
                defaults={
                    "topics": topics,
                    "model_used": django_settings.AZURE_OPENAI_DEPLOYMENT,
                    "chunk_count_used": len(chunks),
                },
            )
            logger.info(f"Extracted {len(topics)} topics for document {doc_id}")
        except Exception:
            logger.exception(f"Topic extraction failed for document {doc_id}")

        # ZMIANA 2: Dodajemy status READY dopiero tutaj, gdy tematy są już na 100% w bazie
        doc.status = Document.Status.READY
        doc.save(update_fields=["status"])

        return {"status": "success", "document_id": doc_id, "chunks": len(chunks)}

    except Exception as exc:
        logger.exception(f"Failed to process document {doc_id}")
        try:
            doc = Document.objects.get(id=doc_id)
            doc.status = Document.Status.ERROR
            doc.error_message = str(exc)[:500]
            doc.save(update_fields=["status", "error_message"])
        except Document.DoesNotExist:
            pass

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        # Final failure — clean up temp file
        _cleanup_temp_file()
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def delete_document_vectors_task(self, doc_id: int, s3_key: str = ""):
    from documents.services.vector_store import ChromaVectorStore

    try:
        vector_store = ChromaVectorStore()
        vector_store.delete(where={"doc_id": str(doc_id)})

        if s3_key:
            from documents.services.s3_client import S3Client

            S3Client().delete_file(s3_key)

        logger.info(f"Deleted vectors and S3 file for document {doc_id}")
        return {"status": "success", "document_id": doc_id}

    except Exception as exc:
        logger.exception(f"Failed to delete resources for document {doc_id}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def extract_topics_task(self, doc_id: int, user_id: int):
    from documents.models import Document, TopicExtractionResult
    from documents.services.vector_store import ChromaVectorStore
    from documents.services.topic_extraction import extract_topics
    from django.conf import settings

    try:
        doc = Document.objects.get(id=doc_id, user_id=user_id)
    except Document.DoesNotExist:
        logger.error(f"Document {doc_id} not found for topic extraction")
        return {"status": "error", "message": "Document not found"}

    try:
        chunks = ChromaVectorStore().get_all_documents(
            where={"doc_id": str(doc_id), "user_id": str(user_id)}
        )

        if not chunks:
            doc.error_message = "No chunks found in vector store"
            doc.save(update_fields=["error_message"])
            return {"status": "error", "message": "No chunks found"}

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
            "status": "success",
            "document_id": doc_id,
            "topic_count": len(topics),
        }

    except Exception as exc:
        logger.exception(f"Failed to extract topics for document {doc_id}")
        doc.error_message = f"Topic extraction failed: {str(exc)[:500]}"
        doc.save(update_fields=["error_message"])

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
