import pytest
from unittest.mock import patch

from documents.services.pdf_processor import extract_and_chunk_pdf


class TestExtractAndChunkPdf:

    def test_extract_and_chunk_success(self, mocker, settings):
        settings.RAG_CHUNK_SIZE = 100
        settings.RAG_CHUNK_OVERLAP = 20

        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value="This is some text. " * 50,
        )

        result = extract_and_chunk_pdf("/fake/path.pdf")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(chunk, str) for chunk in result)

    def test_extract_empty_pdf(self, mocker):
        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value="",
        )

        result = extract_and_chunk_pdf("/fake/empty.pdf")
        assert result == []

    def test_extract_whitespace_only(self, mocker):
        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value="   \n\n  \t  ",
        )

        result = extract_and_chunk_pdf("/fake/whitespace.pdf")
        assert result == []

    def test_extract_none_text(self, mocker):
        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value=None,
        )

        result = extract_and_chunk_pdf("/fake/none.pdf")
        assert result == []

    def test_chunk_size_from_settings(self, mocker, settings):
        settings.RAG_CHUNK_SIZE = 50
        settings.RAG_CHUNK_OVERLAP = 10

        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value="word " * 200,
        )

        result = extract_and_chunk_pdf("/fake/path.pdf")
        # With smaller chunk size, we should get more chunks
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 50 + 20  # chunk_size + some tolerance

    def test_single_chunk_small_document(self, mocker, settings):
        settings.RAG_CHUNK_SIZE = 800
        settings.RAG_CHUNK_OVERLAP = 120

        mocker.patch(
            "documents.services.pdf_processor.pymupdf4llm.to_markdown",
            return_value="Short document text.",
        )

        result = extract_and_chunk_pdf("/fake/short.pdf")
        assert len(result) == 1
        assert result[0] == "Short document text."
