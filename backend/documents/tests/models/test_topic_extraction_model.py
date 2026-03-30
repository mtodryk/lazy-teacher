import pytest

from documents.models import Document, TopicExtractionResult


@pytest.mark.django_db
class TestTopicExtractionResultModel:

    def test_create_topic_extraction(self, document_with_topics, topic_extraction):
        assert topic_extraction.topics == ["Temat 1", "Temat 2", "Temat 3"]
        assert topic_extraction.model_used == "gpt-4o"
        assert topic_extraction.chunk_count_used == 5
        assert topic_extraction.extracted_at is not None

    def test_str_representation(self, document_with_topics, topic_extraction):
        expected = f"Topics for {document_with_topics.title} (3 topics)"
        assert str(topic_extraction) == expected

    def test_one_to_one_relationship(self, document_with_topics, topic_extraction):
        assert topic_extraction.document == document_with_topics
        assert document_with_topics.topic_extraction == topic_extraction

    def test_cascade_delete_with_document(self, document_with_topics):
        assert TopicExtractionResult.objects.count() == 1
        document_with_topics.delete()
        assert TopicExtractionResult.objects.count() == 0

    def test_topics_json_field_empty_list(self, user):
        doc = Document.objects.create(
            user=user,
            title="No Topics",
            file_name="empty.pdf",
            status=Document.Status.READY,
        )
        extraction = TopicExtractionResult.objects.create(
            document=doc,
            topics=[],
            model_used="gpt-4o",
            chunk_count_used=0,
        )
        extraction.refresh_from_db()
        assert extraction.topics == []

    def test_topics_json_field_stores_list_of_strings(self, user):
        doc = Document.objects.create(
            user=user,
            title="Doc",
            file_name="doc.pdf",
            status=Document.Status.READY,
        )
        topics = ["Machine Learning", "Deep Learning", "NLP"]
        extraction = TopicExtractionResult.objects.create(
            document=doc,
            topics=topics,
            model_used="gpt-4o",
            chunk_count_used=10,
        )
        extraction.refresh_from_db()
        assert extraction.topics == topics

    def test_update_or_create_topics(self, document_with_topics, topic_extraction):
        new_topics = ["Nowy Temat 1", "Nowy Temat 2"]
        TopicExtractionResult.objects.update_or_create(
            document=document_with_topics,
            defaults={"topics": new_topics, "model_used": "gpt-4o-mini"},
        )
        topic_extraction.refresh_from_db()
        assert topic_extraction.topics == new_topics
        assert topic_extraction.model_used == "gpt-4o-mini"
        assert TopicExtractionResult.objects.count() == 1

    def test_unique_constraint_one_extraction_per_document(self, document_with_topics):
        with pytest.raises(Exception):
            TopicExtractionResult.objects.create(
                document=document_with_topics,
                topics=["Duplicate"],
                model_used="gpt-4o",
            )
