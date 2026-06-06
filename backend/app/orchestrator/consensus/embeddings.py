"""Embedding-based similarity as a secondary agreement signal."""

from app.orchestrator.similarity import compute_similarity
from app.providers.nvidia_provider import NvidiaProvider
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def compute_embedding_similarity(
    provider: NvidiaProvider | None,
    texts: list[str],
    embedding_model_id: str,
    use_api: bool = False,
) -> float:
    """
    Mean pairwise cosine similarity across response embeddings.

    When ``use_api`` is False (default), uses fast lexical similarity with no
    network call. Enable API only via AGREEMENT_USE_EMBEDDINGS=true.
    """
    if len(texts) < 2:
        return 1.0

    if use_api and provider is not None and provider.is_configured():
        try:
            score = await provider.embedding_similarity(texts, embedding_model_id)
            logger.info("consulate.embedding | source=api | similarity=%.3f", score)
            return score
        except Exception as exc:
            logger.warning("consulate.embedding | api_failed | error=%s", exc)

    pairwise: list[float] = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            pairwise.append(compute_similarity(texts[i], texts[j]))

    score = sum(pairwise) / len(pairwise) if pairwise else 1.0
    logger.debug("consulate.embedding | source=lexical | similarity=%.3f", score)
    return score
