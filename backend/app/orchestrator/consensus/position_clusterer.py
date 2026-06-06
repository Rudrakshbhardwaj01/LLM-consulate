"""Cluster council members by semantic position."""

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
)

_KEY_ALIASES: dict[str, str] = {
    "association_football_soccer": "soccer",
    "association_football": "soccer",
}


def cluster_positions(claims: list[ExtractedClaims]) -> list[PositionCluster]:
    """
    Group responses by canonical position_key.

    Clustering is driven by extracted interpretation keys (majority vote input),
    not surface text similarity, so paraphrases cluster together but genuinely
    different interpretations (soccer vs american football) stay separate.
    """
    if not claims:
        return []

    clusters: list[PositionCluster] = []

    for item in claims:
        placed = False
        item_key = _canonical_key(item.position_key)

        for cluster in clusters:
            if _same_cluster(item, item_key, cluster):
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

    total = len(claims)
    for cluster in clusters:
        cluster.support = round(cluster.count / total, 3)

    clusters.sort(key=lambda c: c.count, reverse=True)
    logger.info(
        "consulate.cluster | clusters=%s",
        ", ".join(f"{c.position_key}={c.count}" for c in clusters),
    )
    return clusters


def _canonical_key(key: str) -> str:
    return _KEY_ALIASES.get(key, key)


def _same_cluster(
    item: ExtractedClaims,
    item_key: str,
    cluster: PositionCluster,
) -> bool:
    cluster_key = _canonical_key(cluster.position_key)

    if item_key and cluster_key:
        if item_key == cluster_key:
            return True
        # Explicit incompatible interpretations — never merge
        pair = frozenset({item_key, cluster_key})
        for incompatible in _INCOMPATIBLE_KEYS:
            if pair == incompatible or pair.issuperset(incompatible):
                return False
        return False

    # No reliable key — fall back to full response text similarity
    if item.sanitized_text:
        for other in _claims_in_cluster(cluster):
            if compute_similarity(item.sanitized_text, other) >= 0.72:
                return True

    return False


def _claims_in_cluster(cluster: PositionCluster) -> list[str]:
    # Position summary alone is not stored per member; use summary as proxy
    return [cluster.position_summary] if cluster.position_summary else []
