from .types import RetrievalContext
from settings.utils import ApplicationError
import logging
from chromadb import Collection

logger = logging.getLogger(__name__)


class ChromaRetriever:

    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def retrieve_for_topics(
        self,
        topics: list[str],
        max_results: int = 5,
        max_distance: float = 0.5,
        doc_id: int | None = None,
    ) -> dict[str, RetrievalContext]:

        if not topics:
            return {}

        results = self._query_collection(
            topics=topics,
            max_results=max_results,
            doc_id=doc_id,
        )

        return self._build_topic_contexts(
            topics=topics,
            results=results,
            max_results=max_results,
            max_distance=max_distance,
        )

    def _query_collection(
        self,
        topics: list[str],
        max_results: int,
        doc_id: int | None,
    ) -> dict:

        try:
            kwargs = self._build_query_kwargs(topics, max_results, doc_id)
            results = self.collection.query(**kwargs)
            self._validate_batch_response(results)
            return results

        except Exception as e:
            logger.exception(f"Chroma batch query failed for {len(topics)} topics")
            raise ApplicationError(
                "Batch document retrieval from Chroma failed",
                extra={
                    "error_type": type(e).__name__,
                    "topics_count": len(topics),
                },
            )

    def _build_query_kwargs(
        self,
        topics: list[str],
        max_results: int,
        doc_id: int | None,
    ) -> dict:

        kwargs = {
            "query_texts": topics,
            "n_results": max_results + 2,
            "include": ["documents", "distances"],
        }

        if doc_id is not None:
            kwargs["where"] = {"doc_id": str(doc_id)}

        return kwargs

    def _validate_batch_response(self, results: dict) -> None:
        if not results or "documents" not in results or "distances" not in results:
            raise ValueError("Invalid Chroma batch response structure")

    def _build_topic_contexts(
        self,
        topics: list[str],
        results: dict,
        max_results: int,
        max_distance: float,
    ) -> dict[str, RetrievalContext]:

        topic_contexts: dict[str, RetrievalContext] = {}

        for i, topic in enumerate(topics):
            docs, dists = self._extract_topic_results(results, i)

            filtered_docs, filtered_dists = self._filter_by_distance(
                docs,
                dists,
                max_results,
                max_distance,
            )

            topic_contexts[topic] = RetrievalContext(
                documents=filtered_docs,
                distances=filtered_dists,
            )

        return topic_contexts

    def _extract_topic_results(
        self,
        results: dict,
        index: int,
    ) -> tuple[list, list]:

        try:
            docs = results["documents"][index]
            dists = results["distances"][index]

            if not isinstance(docs, list) or not isinstance(dists, list):
                raise TypeError("Documents or distances is not a list")

            return docs, dists

        except (IndexError, TypeError):
            logger.warning(f"Invalid or missing results for topic index {index}")
            return [], []

    def _filter_by_distance(
        self,
        docs: list,
        dists: list,
        max_results: int,
        max_distance: float,
    ) -> tuple[list, list]:

        good_docs = []
        good_dists = []

        for doc, dist in zip(docs, dists):
            try:
                if float(dist) < max_distance:
                    good_docs.append(doc)
                    good_dists.append(dist)

                if len(good_docs) >= max_results:
                    break

            except (ValueError, TypeError):
                logger.warning(f"Invalid distance value {dist}")
                continue

        return good_docs, good_dists
