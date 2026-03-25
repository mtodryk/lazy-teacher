import logging

import chromadb
from chromadb import ClientAPI, Collection
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from django.conf import settings
from celery.signals import worker_process_init

logger: logging.Logger = logging.getLogger(__name__)

_chroma_client: ClientAPI | None = None
_embedding_fn: SentenceTransformerEmbeddingFunction | None = None
_collection: Collection | None = None


@worker_process_init.connect
def initialize_on_worker_start(**kwargs):
    get_chroma_client()
    get_embedding_function()
    get_chroma_collection()


def get_chroma_client() -> ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        logger.info(
            "Connecting to ChromaDB at %s:%s",
            settings.CHROMA_HOST,
            settings.CHROMA_PORT,
        )
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        logger.info("ChromaDB client initialized")
    return _chroma_client


def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
    global _embedding_fn
    if _embedding_fn is None:
        logger.info(
            "Initializing embedding function with model: %s",
            settings.EMBEDDING_MODEL_NAME,
        )
        _embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME,
            trust_remote_code=True,
        )
        logger.info("Embedding function initialized successfully")
    return _embedding_fn


def get_chroma_collection() -> Collection:
    global _collection
    if _collection is None:
        _collection = get_chroma_client().get_or_create_collection(
            name="rag_documents",
            embedding_function=get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def warmup_embedding_model() -> None:
    get_embedding_function()
    logger.info("Embedding model warmed up and ready")
