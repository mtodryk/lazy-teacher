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


def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
    logger.info(
        f"Initializing embedding function with model: {settings.EMBEDDING_MODEL_NAME}"
    )
    ef = SentenceTransformerEmbeddingFunction(
        model_name=settings.EMBEDDING_MODEL_NAME,
        cache_folder=os.environ.get("HF_HOME", "/root/.cache/huggingface"),
        trust_remote_code=True,
    )

    logger.info("Embedding function initialized successfully")

    return ef


def get_chroma_collection() -> Collection:
    client: ClientAPI = get_chroma_client()
    embedding_fn = get_embedding_function()

    return client.get_or_create_collection(
        name="rag_documents",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
