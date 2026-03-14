from .vector_store import SearchResult
from .vector_store import ChromaVectorStore


def retrieve_chunks(
    query: str,
    doc_id: int | str,
    user_id: int | str,
    n_results: int = 5,
) -> list[SearchResult]:

    store = ChromaVectorStore()
    return store.search(
        query=query,
        n_results=n_results,
        where={"doc_id": str(doc_id), "user_id": str(user_id)},
    )
