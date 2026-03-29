import pytest
from django.contrib.auth.models import User

from documents.models import Document


@pytest.mark.django_db
class TestDocumentModel:

    def test_create_document_with_defaults(self, user):
        doc = Document.objects.create(
            user=user,
            title="My Document",
            file_name="doc.pdf",
        )
        assert doc.status == Document.Status.PENDING
        assert doc.chunk_count == 0
        assert doc.error_message == ""
        assert doc.s3_key == ""
        assert doc.uploaded_at is not None

    def test_str_representation(self, user):
        doc = Document.objects.create(
            user=user,
            title="Quiz Doc",
            file_name="test.pdf",
            status=Document.Status.READY,
        )
        assert str(doc) == "Quiz Doc (ready)"

    def test_status_choices(self):
        assert Document.Status.PENDING == "pending"
        assert Document.Status.PROCESSING == "processing"
        assert Document.Status.READY == "ready"
        assert Document.Status.TOPICS_EXTRACTED == "topics_extracted"
        assert Document.Status.ERROR == "error"

    def test_ordering_by_uploaded_at_desc(self, user):
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        doc1 = Document.objects.create(user=user, title="First", file_name="first.pdf")
        Document.objects.filter(pk=doc1.pk).update(uploaded_at=now - timedelta(hours=1))
        doc2 = Document.objects.create(
            user=user, title="Second", file_name="second.pdf"
        )
        Document.objects.filter(pk=doc2.pk).update(uploaded_at=now)

        docs = list(Document.objects.all())
        assert docs[0].pk == doc2.pk
        assert docs[1].pk == doc1.pk

    def test_cascade_delete_with_user(self, user):
        Document.objects.create(user=user, title="Doc", file_name="doc.pdf")
        assert Document.objects.count() == 1
        user.delete()
        assert Document.objects.count() == 0

    def test_document_with_all_fields(self, user):
        doc = Document.objects.create(
            user=user,
            title="Full Doc",
            file_name="full.pdf",
            s3_key="documents/1/1.pdf",
            chunk_count=42,
            status=Document.Status.READY,
            error_message="",
        )
        doc.refresh_from_db()
        assert doc.s3_key == "documents/1/1.pdf"
        assert doc.chunk_count == 42
        assert doc.status == Document.Status.READY

    def test_status_transition(self, user):
        doc = Document.objects.create(user=user, title="Doc", file_name="doc.pdf")
        assert doc.status == Document.Status.PENDING

        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=["status"])
        doc.refresh_from_db()
        assert doc.status == Document.Status.PROCESSING

        doc.status = Document.Status.READY
        doc.save(update_fields=["status"])
        doc.refresh_from_db()
        assert doc.status == Document.Status.READY

    def test_related_name_rag_documents(self, user):
        Document.objects.create(user=user, title="Doc1", file_name="d1.pdf")
        Document.objects.create(user=user, title="Doc2", file_name="d2.pdf")
        assert user.rag_documents.count() == 2

    def test_error_status_with_message(self, user):
        doc = Document.objects.create(
            user=user,
            title="Error Doc",
            file_name="err.pdf",
            status=Document.Status.ERROR,
            error_message="PDF extraction failed: corrupt file",
        )
        doc.refresh_from_db()
        assert doc.status == Document.Status.ERROR
        assert "corrupt file" in doc.error_message
