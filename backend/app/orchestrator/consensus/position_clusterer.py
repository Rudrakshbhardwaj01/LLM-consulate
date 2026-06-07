"""Cluster council members by semantic position."""

import time
from dataclasses import dataclass

from app.config.constants import SIMILARITY_MAX_CHARS
from app.orchestrator.consensus.models import ExtractedClaims, PositionCluster
from app.orchestrator.similarity import compute_similarity
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Canonical keys that must never be merged with each other.
_INCOMPATIBLE_KEYS = (
    frozenset({"soccer", "american_football"}),
    frozenset({"aggressive_investment", "conservative_investment"}),
    frozenset({"depth_first", "breadth_first"}),
    frozenset({"depth_first", "context_dependent"}),
    frozenset({"breadth_first", "context_dependent"}),
    frozenset({"pro_vc", "anti_vc"}),
    frozenset({"apartment_friendly_pet", "active_pet"}),
)

_KEY_ALIASES: dict[str, str] = {
    "association_football_soccer": "soccer",
    "association_football": "soccer",
}

_GENERIC_KEYS = frozenset(
    {
        "general",
        "general_position",
        "general_recommendation",
        "general_investment",
        "context_dependent",
        "balanced_career",
    }
)

# Merge when full-response semantic similarity exceeds this threshold.
_SIMILARITY_MERGE_THRESHOLD = 0.58
# Slightly relaxed when both sides use generic interpretation keys.
_GENERIC_SIMILARITY_THRESHOLD = 0.52


@dataclass
class ClusterTiming:
    assign_ms: int = 0
    merge_ms: int = 0
    similarity_ms: int = 0
    comparisons: int = 0

    @property
    def total_ms(self) -> int:
        return self.assign_ms + self.merge_ms


def cluster_positions(
    claims: list[ExtractedClaims],
) -> tuple[list[PositionCluster], ClusterTiming]:
    """
    Group responses by semantic agreement on conclusions.

    Uses interpretation keys when they are canonical and distinct, then falls
    back to composite text similarity so paraphrased recommendations cluster
    together even when surface wording differs (e.g. different dog breeds with
    the same apartment-friendly conclusion).
    """
    timing = ClusterTiming()
    if not claims:
        return [], timing

    logger.info("consulate.cluster.start | claims=%d", len(claims))
    cluster_start = time.perf_counter()
    similarity_cache: dict[tuple[str, str], float] = {}

    claims_by_id = {claim.model_id: claim for claim in claims}
    clusters: list[PositionCluster] = []

    assign_start = time.perf_counter()
    for item in claims:
        placed = False
        item_key = _canonical_key(item.position_key)

        for cluster in clusters:
            if _same_cluster(item, item_key, cluster, claims_by_id, timing, similarity_cache):
                cluster.model_ids.append(item.model_id)
                cluster.model_names.append(item.model_name)
                cluster.count += 1
                placed = True
                break

        if not placed:
            clusters.append(
                PositionCluster(
                    positionKey=item_key or item.position_key,
                    positionLabel=item.interpretation or item.position_summary,
                    positionSummary=item.position_summary,
                    modelIds=[item.model_id],
                    modelNames=[item.model_name],
                    count=1,
                )
            )
    timing.assign_ms = int((time.perf_counter() - assign_start) * 1000)

    merge_start = time.perf_counter()
    clusters = _merge_similar_clusters(clusters, claims_by_id, timing, similarity_cache)
    timing.merge_ms = int((time.perf_counter() - merge_start) * 1000)

    total = len(claims)
    for cluster in clusters:
        cluster.support = round(cluster.count / total, 3)

    clusters.sort(key=lambda c: c.count, reverse=True)
    logger.info(
        "consulate.cluster | clusters=%s",
        ", ".join(f"{c.position_key}={c.count}" for c in clusters),
    )
    cluster_wall_ms = int((time.perf_counter() - cluster_start) * 1000)
    logger.info(
        "consulate.timing | stage=cluster | cluster_wall_ms=%d | assign_ms=%d | merge_ms=%d | "
        "similarity_ms=%d | comparisons=%d",
        cluster_wall_ms,
        timing.assign_ms,
        timing.merge_ms,
        timing.similarity_ms,
        timing.comparisons,
    )
    logger.info(
        "consulate.cluster.end | cluster_wall_ms=%d | similarity_ms=%d | comparisons=%d",
        cluster_wall_ms,
        timing.similarity_ms,
        timing.comparisons,
    )
    return clusters, timing


def _merge_similar_clusters(
    clusters: list[PositionCluster],
    claims_by_id: dict[str, ExtractedClaims],
    timing: ClusterTiming,
    similarity_cache: dict[tuple[str, str], float],
) -> list[PositionCluster]:
    """Second pass: merge clusters whose member responses semantically align."""
    if len(clusters) < 2:
        return clusters

    merged = True
    while merged:
        merged = False
        i = 0
        while i < len(clusters):
            j = i + 1
            while j < len(clusters):
                if _clusters_compatible(
                    clusters[i], clusters[j], claims_by_id, timing, similarity_cache
                ):
                    a, b = clusters[i], clusters[j]
                    a.model_ids.extend(b.model_ids)
                    a.model_names.extend(b.model_names)
                    a.count += b.count
                    if len(b.position_summary) > len(a.position_summary):
                        a.position_summary = b.position_summary
                        a.position_label = b.position_label
                    clusters.pop(j)
                    merged = True
                else:
                    j += 1
            i += 1

    return clusters


def _clusters_compatible(
    left: PositionCluster,
    right: PositionCluster,
    claims_by_id: dict[str, ExtractedClaims],
    timing: ClusterTiming,
    similarity_cache: dict[tuple[str, str], float],
) -> bool:
    left_key = _canonical_key(left.position_key)
    right_key = _canonical_key(right.position_key)
    if left_key and right_key and left_key != right_key:
        pair = frozenset({left_key, right_key})
        for incompatible in _INCOMPATIBLE_KEYS:
            if pair == incompatible or pair.issuperset(incompatible):
                return False

    left_texts = _cluster_texts(left, claims_by_id)
    right_texts = _cluster_texts(right, claims_by_id)
    threshold = _GENERIC_SIMILARITY_THRESHOLD
    if left_key and right_key and left_key == right_key and not _is_generic_key(left_key):
        threshold = _SIMILARITY_MERGE_THRESHOLD

    best = 0.0
    for a in left_texts:
        for b in right_texts:
            best = max(best, _timed_similarity(a, b, timing, similarity_cache))
    return best >= threshold


def _canonical_key(key: str) -> str:
    return _KEY_ALIASES.get(key, key)


def _is_generic_key(key: str) -> bool:
    if not key:
        return True
    if key in _GENERIC_KEYS:
        return True
    return key.startswith("general_")


def _same_cluster(
    item: ExtractedClaims,
    item_key: str,
    cluster: PositionCluster,
    claims_by_id: dict[str, ExtractedClaims],
    timing: ClusterTiming,
    similarity_cache: dict[tuple[str, str], float],
) -> bool:
    cluster_key = _canonical_key(cluster.position_key)

    if item_key and cluster_key:
        pair = frozenset({item_key, cluster_key})
        for incompatible in _INCOMPATIBLE_KEYS:
            if pair == incompatible or pair.issuperset(incompatible):
                return False

        if item_key == cluster_key:
            if _is_generic_key(item_key):
                return _texts_semantically_align(
                    item, cluster, claims_by_id, timing, similarity_cache
                )
            return True

        if item_key and cluster_key and item_key != cluster_key:
            return False

    return _texts_semantically_align(item, cluster, claims_by_id, timing, similarity_cache)


def _texts_semantically_align(
    item: ExtractedClaims,
    cluster: PositionCluster,
    claims_by_id: dict[str, ExtractedClaims],
    timing: ClusterTiming,
    similarity_cache: dict[tuple[str, str], float],
) -> bool:
    item_texts = _claim_text_variants(item)
    member_texts = _cluster_texts(cluster, claims_by_id)
    if not item_texts or not member_texts:
        return False

    threshold = _GENERIC_SIMILARITY_THRESHOLD
    item_key = _canonical_key(item.position_key)
    cluster_key = _canonical_key(cluster.position_key)
    if item_key and cluster_key and item_key == cluster_key and not _is_generic_key(item_key):
        threshold = _SIMILARITY_MERGE_THRESHOLD

    for left in item_texts:
        for right in member_texts:
            if _timed_similarity(left, right, timing, similarity_cache) >= threshold:
                return True
    return False


def _timed_similarity(
    text_a: str,
    text_b: str,
    timing: ClusterTiming,
    similarity_cache: dict[tuple[str, str], float],
) -> float:
    key = (text_a, text_b) if text_a <= text_b else (text_b, text_a)
    cached = similarity_cache.get(key)
    if cached is not None:
        return cached

    start = time.perf_counter()
    score = compute_similarity(text_a, text_b)
    timing.similarity_ms += int((time.perf_counter() - start) * 1000)
    timing.comparisons += 1
    similarity_cache[key] = score
    return score


def _claim_text_variants(claim: ExtractedClaims) -> list[str]:
    parts: list[str] = []
    if claim.position_summary:
        parts.append(claim.position_summary[:SIMILARITY_MAX_CHARS])
    if claim.claims:
        parts.append(" ".join(claim.claims[:4])[:SIMILARITY_MAX_CHARS])
    if claim.sanitized_text:
        parts.append(claim.sanitized_text[:SIMILARITY_MAX_CHARS])
    return [part for part in parts if part.strip()]


def _cluster_texts(
    cluster: PositionCluster,
    claims_by_id: dict[str, ExtractedClaims],
) -> list[str]:
    texts: list[str] = []
    for model_id in cluster.model_ids:
        claim = claims_by_id.get(model_id)
        if claim:
            texts.extend(_claim_text_variants(claim))
    if cluster.position_summary:
        texts.append(cluster.position_summary)
    return texts
