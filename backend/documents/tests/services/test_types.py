import pytest
from documents.services.types import (
    QuestionData,
    QuizData,
    RetrievalContext,
    LlmResponse,
    QuestionOption,
)


class TestQuestionData:

    def test_create_question_data(self):
        q = QuestionData(
            question="What is ML?",
            options=["A", "B", "C", "D"],
            correct_index=0,
        )
        assert q.question == "What is ML?"
        assert q.options == ["A", "B", "C", "D"]
        assert q.correct_index == 0
        assert q.topic == ""
        assert q.used_chunks_count == 0
        assert q.max_distance_used == 0.0

    def test_create_with_all_fields(self):
        q = QuestionData(
            question="Q?",
            options=["A", "B", "C", "D"],
            correct_index=2,
            topic="ML",
            used_chunks_count=3,
            max_distance_used=0.5,
        )
        assert q.topic == "ML"
        assert q.used_chunks_count == 3
        assert q.max_distance_used == 0.5


class TestQuizData:

    def test_empty_quiz(self):
        quiz = QuizData()
        assert quiz.count() == 0
        assert quiz.to_dict() == []

    def test_add_question(self):
        quiz = QuizData()
        q = QuestionData(
            question="Q1?",
            options=["A", "B", "C", "D"],
            correct_index=1,
            topic="Topic 1",
        )
        quiz.add_question(q)
        assert quiz.count() == 1

    def test_to_dict(self):
        quiz = QuizData()
        quiz.add_question(
            QuestionData(
                question="Q1?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                topic="T1",
                used_chunks_count=2,
                max_distance_used=0.3,
            )
        )
        result = quiz.to_dict()
        assert len(result) == 1
        assert result[0]["question"] == "Q1?"
        assert result[0]["options"] == ["A", "B", "C", "D"]
        assert result[0]["correct_index"] == 0
        assert result[0]["topic"] == "T1"
        assert result[0]["used_chunks_count"] == 2
        assert result[0]["max_distance_used"] == 0.3

    def test_multiple_questions(self):
        quiz = QuizData()
        for i in range(5):
            quiz.add_question(
                QuestionData(
                    question=f"Q{i}?",
                    options=["A", "B", "C", "D"],
                    correct_index=i % 4,
                )
            )
        assert quiz.count() == 5
        assert len(quiz.to_dict()) == 5


class TestRetrievalContext:

    def test_get_good_chunks(self):
        ctx = RetrievalContext(
            documents=["doc1", "doc2", "doc3"],
            distances=[0.1, 0.6, 0.3],
        )
        good = ctx.get_good_chunks(max_distance=0.5)
        assert good == ["doc1", "doc3"]

    def test_get_good_chunks_all_good(self):
        ctx = RetrievalContext(
            documents=["doc1", "doc2"],
            distances=[0.1, 0.2],
        )
        assert ctx.get_good_chunks(0.5) == ["doc1", "doc2"]

    def test_get_good_chunks_none_good(self):
        ctx = RetrievalContext(
            documents=["doc1", "doc2"],
            distances=[0.8, 0.9],
        )
        assert ctx.get_good_chunks(0.5) == []

    def test_has_good_context_true(self):
        ctx = RetrievalContext(documents=["doc1"], distances=[0.1])
        assert ctx.has_good_context(0.5) is True

    def test_has_good_context_false(self):
        ctx = RetrievalContext(documents=["doc1"], distances=[0.8])
        assert ctx.has_good_context(0.5) is False

    def test_empty_context(self):
        ctx = RetrievalContext(documents=[], distances=[])
        assert ctx.get_good_chunks(0.5) == []
        assert ctx.has_good_context(0.5) is False


class TestLlmResponse:

    def test_extract_json_plain(self):
        response = LlmResponse(content='{"key": "value"}')
        assert response.extract_json() == '{"key": "value"}'

    def test_extract_json_with_markdown_fences(self):
        response = LlmResponse(content='```json\n{"key": "value"}\n```')
        result = response.extract_json()
        assert '"key"' in result
        assert "```" not in result

    def test_extract_json_with_whitespace(self):
        response = LlmResponse(content='  \n{"key": "value"}\n  ')
        assert response.extract_json() == '{"key": "value"}'

    def test_extract_json_complex(self):
        content = '```\n{"topics": ["A", "B", "C"]}\n```'
        response = LlmResponse(content=content)
        result = response.extract_json()
        assert "topics" in result
        assert "```" not in result
