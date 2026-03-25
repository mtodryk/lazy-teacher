from .types import RetrievalContext


class ChromaRetriever:

    def __init__(self, collection) -> None:
        self.collection = collection

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        doc_id: int | None = None,
    ) -> RetrievalContext:
        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "distances"],
        }

        if doc_id is not None:
            kwargs["where"] = {"doc_id": str(doc_id)}

        results = self.collection.query(**kwargs)

        return RetrievalContext(
            documents=results["documents"][0],
            distances=results["distances"][0],
        )

    def retrieve_for_topic(
        self,
        topic: str,
        max_results: int = 5,
        max_distance: float = 0.5,
        doc_id: int | None = None,
    ) -> RetrievalContext:

        context = self.retrieve(query=topic, n_results=max_results + 2, doc_id=doc_id)

        good_docs = []
        good_dists = []
        for doc, dist in zip(context.documents, context.distances):
            if dist < max_distance:
                good_docs.append(doc)
                good_dists.append(dist)
            if len(good_docs) >= max_results:
                break

        return RetrievalContext(
            documents=good_docs,
            distances=good_dists,
        )
