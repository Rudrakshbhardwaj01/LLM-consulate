"""Embedding-based similarity as a secondary agreement signal."""

import time

from app.config.constants import SIMILARITY_MAX_CHARS
from app.orchestrator.similarity import compute_similarity
from app.providers.nvidia_provider import NvidiaProvider
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def compute_embedding_similarity(
    provider: NvidiaProvider | None,
    texts: list[str],
    embedding_model_id: str,
    use_api: bool = False,
    request_id: str = "",
) -> tuple[float, int]:
    """
    Mean pairwise cosine similarity across response embeddings.

    When ``use_api`` is False (default), uses fast lexical similarity with no
    network call. Enable API only via AGREEMENT_USE_EMBEDDINGS=true.
    """
    logger.info(
        "consulate.embeddings.start | request_id=%s | texts=%d | use_api=%s",
        request_id or "n/a",
        len(texts),
        use_api,
    )
    start = time.perf_counter()
    if len(texts) < 2:
        return 1.0, 0

    compact_texts = [text[:SIMILARITY_MAX_CHARS] for text in texts]
    source = "lexical"
    if use_api and provider is not None and provider.is_configured():
        try:
            score = await provider.embedding_similarity(compact_texts, embedding_model_id)
            source = "api"
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "consulate.timing | stage=embeddings | source=%s | embeddings_ms=%d | similarity=%.3f",
                source,
                elapsed_ms,
                score,
            )
            return score, elapsed_ms
        except Exception as exc:
            logger.warning("consulate.embedding | api_failed | error=%s", exc)

    pairwise: list[float] = []
    for i in range(len(compact_texts)):
        for j in range(i + 1, len(compact_texts)):
            pairwise.append(compute_similarity(compact_texts[i], compact_texts[j]))

    score = sum(pairwise) / len(pairwise) if pairwise else 1.0
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "consulate.timing | stage=embeddings | source=%s | embeddings_ms=%d | similarity=%.3f",
        source,
        elapsed_ms,
        score,
    )
    logger.info("consulate.embeddings.end | source=%s | embeddings_ms=%d", source, elapsed_ms)
    return score, elapsed_ms
