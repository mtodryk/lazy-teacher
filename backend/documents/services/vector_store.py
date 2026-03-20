from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .chroma_client import get_chroma_collection, get_embedding_function


@dataclass
class SearchResult:
    text: str
    chunk_idx: int
    distance: float
    source: str
    metadata: dict = field(default_factory=dict)


class BaseVectorStore(ABC):

    @abstractmethod
    def add_documents(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict],
    ) -> None: ...

    @abstractmethod
    def search(
        self,
        query: str,
        n_results: int,
        where: dict,
    ) -> list[SearchResult]: ...

    @abstractmethod
    def delete(self, where: dict) -> None: ...


class ChromaVectorStore(BaseVectorStore):

    BATCH_SIZE = 5000

    def __init__(self):
        self._collection = get_chroma_collection()
        self._embed = get_embedding_function()

    # ------------------------------------------------------------------
    # WRITE OPERATIONS - Call only from Celery workers!
    # ------------------------------------------------------------------

    def add_documents(
        self, documents: list[str], ids: list[str], metadatas: list[dict]
    ) -> None:
        for i in range(0, len(documents), self.BATCH_SIZE):
            end = i + self.BATCH_SIZE
            self._collection.add(
                documents=documents[i:end],
                ids=ids[i:end],
                metadatas=metadatas[i:end],
            )

    def delete(self, where: dict) -> None:
        chroma_where = self._build_where(where)
        if chroma_where:
            self._collection.delete(where=chroma_where)

    # ------------------------------------------------------------------
    # READ OPERATIONS - Safe to call from Django web process
    # ------------------------------------------------------------------

    def search(
        self, query: str, n_results: int = 5, where: dict | None = None
    ) -> list[SearchResult]:
        query_embedding = self._embed([query])
        kwargs: dict = {
            "query_embeddings": query_embedding,
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        chroma_where = self._build_where(where)
        if chroma_where:
            kwargs["where"] = chroma_where

        results = self._collection.query(**kwargs)

        hits: list[SearchResult] = []
        if not results["documents"] or not results["documents"][0]:
            return hits

        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                SearchResult(
                    text=text,
                    chunk_idx=meta.get("chunk_idx", 0),
                    distance=round(float(dist), 4),
                    source=meta.get("source", ""),
                    metadata=meta,
                )
            )
        return hits

    def get_all_documents(self, where: dict | None = None) -> list[str]:
        kwargs: dict = {"include": ["documents", "metadatas"]}
        chroma_where = self._build_where(where)
        if chroma_where:
            kwargs["where"] = chroma_where

        results = self._collection.get(**kwargs)

        if not results["documents"]:
            return []

        pairs = zip(results["documents"], results["metadatas"])
        sorted_pairs = sorted(pairs, key=lambda p: p[1].get("chunk_idx", 0))
        return [text for text, _ in sorted_pairs]

    # ------------------------------------------------------------------

    @staticmethod
    def _build_where(filters: dict | None) -> dict | None:
        if not filters:
            return None
        if len(filters) == 1:
            return filters
        return {"$and": [{k: v} for k, v in filters.items()]}
