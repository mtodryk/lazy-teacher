import logging
import os

import chromadb
from chromadb import ClientAPI, Collection
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from django.conf import settings

logger: logging.Logger = logging.getLogger(__name__)


def get_chroma_client() -> ClientAPI:
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


_embedding_fn: SentenceTransformerEmbeddingFunction | None = None


def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
    global _embedding_fn
    if _embedding_fn is None:
        logger.info(
            f"Initializing embedding function with model: {settings.EMBEDDING_MODEL_NAME}"
        )
        _embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME,
            trust_remote_code=True,
        )
        logger.info("Embedding function initialized successfully")
    return _embedding_fn


def get_chroma_collection() -> Collection:
    return get_chroma_client().get_or_create_collection(
        name="rag_documents",
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
