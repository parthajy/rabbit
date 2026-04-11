"""
Reranker for Rabbit retrieval pipeline.

Uses a cross-encoder model to re-score candidate memories against the query.
Falls back gracefully if the reranker model is not installed.
"""

from __future__ import annotations

from typing import Any

_reranker_model = None
_reranker_available: bool | None = None


def is_available() -> bool:
    """Check if a reranker model is available."""
    global _reranker_available
    if _reranker_available is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker_available = True
        except ImportError:
            _reranker_available = False
    return _reranker_available


def _get_model():
    """Lazy-load the reranker model."""
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder(
            "jinaai/jina-reranker-v2-base-multilingual",
            trust_remote_code=True,
        )
    return _reranker_model


def rerank(query: str, documents: list[dict[str, str]], limit: int = 5) -> list[dict[str, Any]]:
    """Rerank documents against a query using a cross-encoder.

    Args:
        query: The search query.
        documents: List of dicts with at least a "text" key.
        limit: Max results to return.

    Returns:
        List of documents sorted by relevance, with "rerank_score" added.
        Falls back to returning documents unchanged if reranker unavailable.
    """
    if not documents:
        return []

    if not is_available():
        return documents[:limit]

    model = _get_model()
    texts = [d.get("text", d.get("content", ""))[:512] for d in documents]

    # Cross-encoder scores each (query, document) pair
    pairs = [[query, text] for text in texts]
    scores = model.predict(pairs)

    # Attach scores and sort
    for i, doc in enumerate(documents):
        doc["rerank_score"] = float(scores[i])

    ranked = sorted(documents, key=lambda d: d.get("rerank_score", 0), reverse=True)
    return ranked[:limit]
