from __future__ import annotations

import pymupdf4llm
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_and_chunk_pdf(pdf_path: str) -> list[str]:
    """Extract text from a PDF and split into overlapping chunks."""
    chunk_size = getattr(settings, "RAG_CHUNK_SIZE", 800)
    chunk_overlap = getattr(settings, "RAG_CHUNK_OVERLAP", 120)

    markdown_text = pymupdf4llm.to_markdown(pdf_path)
    if not markdown_text or not markdown_text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(markdown_text)
