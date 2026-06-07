"""Majority vote, consensus outcome classification, and semantic disagreement summaries."""

import time
from collections import Counter
from enum import StrEnum

from app.orchestrator.consensus.models import ExtractedClaims, PositionCluster
from app.schemas.consulate import DisagreementSummary
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAJORITY_THRESHOLD = 0.50


class ConsensusOutcome(StrEnum):
    CONSENSUS_STRONG = "consensus_strong"
    CONSENSUS_MODERATE = "consensus_moderate"
    CONSENSUS_WEAK = "consensus_weak"
    DEADLOCK = "deadlock"


def classify_outcome(majority_support: float, is_deadlock: bool) -> ConsensusOutcome:
    """Map vote support to a council outcome. Deadlock is vote-driven only."""
    if is_deadlock or majority_support < MAJORITY_THRESHOLD:
        return ConsensusOutcome.DEADLOCK
    if majority_support >= 0.80:
        return ConsensusOutcome.CONSENSUS_STRONG
    if majority_support >= 0.60:
        return ConsensusOutcome.CONSENSUS_MODERATE
    return ConsensusOutcome.CONSENSUS_WEAK


def confidence_label(agreement_score: float) -> str:
    """Agreement score reflects linguistic alignment — not consensus existence."""
    if agreement_score >= 0.67:
        return "high"
    if agreement_score >= 0.45:
        return "moderate"
    return "low"


def outcome_display_label(outcome: ConsensusOutcome) -> str:
    return {
        ConsensusOutcome.CONSENSUS_STRONG: "Strong Consensus",
        ConsensusOutcome.CONSENSUS_MODERATE: "Moderate Consensus",
        ConsensusOutcome.CONSENSUS_WEAK: "Weak Consensus",
        ConsensusOutcome.DEADLOCK: "Council Deadlocked",
    }[outcome]


def analyze_majority(
    clusters: list[PositionCluster],
    prompt: str = "",
    topic: str = "",
    request_id: str = "",
) -> tuple[
    PositionCluster | None,
    PositionCluster | None,
    float,
    float,
    bool,
    ConsensusOutcome,
    DisagreementSummary | None,
]:
    """
    Determine majority/minority positions and whether the council is deadlocked.

    Deadlock ONLY when:
    - no cluster exceeds 50% support, OR
    - top clusters are tied (2-2, 3-3, 2-2-1, etc.)

    Agreement score never influences this decision.
    """
    logger.info("consulate.majority.start | request_id=%s", request_id or "n/a")
    start = time.perf_counter()
    if not clusters:
        return None, None, 0.0, 0.0, True, ConsensusOutcome.DEADLOCK, None

    total = sum(c.count for c in clusters)
    if total == 0:
        return None, None, 0.0, 0.0, True, ConsensusOutcome.DEADLOCK, None

    majority = clusters[0]
    minority = clusters[1] if len(clusters) > 1 else None

    majority_support = majority.count / total
    minority_support = (minority.count / total) if minority else 0.0

    top_count = majority.count
    tied_at_top = sum(1 for c in clusters if c.count == top_count) > 1
    is_deadlock = majority_support < MAJORITY_THRESHOLD or tied_at_top
    outcome = classify_outcome(majority_support, is_deadlock)

    majority_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "consulate.majority | request_id=%s | winner=%s | topic_support=%.0f%% | "
        "outcome=%s | deadlock=%s | tied=%s",
        request_id or "n/a",
        majority.position_key,
        majority_support * 100,
        outcome.value,
        is_deadlock,
        tied_at_top,
    )
    logger.info("consulate.timing | stage=majority_vote | majority_ms=%d", majority_ms)
    logger.info("consulate.majority.end | majority_ms=%d", majority_ms)

    disagreement = None
    if minority:
        disagreement = build_disagreement_summary(
            prompt, topic, majority, minority, majority_support, minority_support
        )

    return (
        majority,
        minority,
        majority_support,
        minority_support,
        is_deadlock,
        outcome,
        disagreement,
    )


def analyze_recommendation_vote(
    claims: list[ExtractedClaims],
) -> tuple[float, float, str, list[str], list[str], bool]:
    """
    Vote support by specific recommendation, not broad position/topic bucket.

    Returns:
        recommendation_support, minority_recommendation_support, top_recommendation,
        supporting_model_names, minority_model_names, is_deadlock
    """
    if not claims:
        return 0.0, 0.0, "", [], [], True

    counts = Counter(
        claim.primary_recommendation or claim.position_key or "general_recommendation"
        for claim in claims
    )
    total = len(claims)
    ranked = counts.most_common()
    top_key, top_count = ranked[0]
    second_count = ranked[1][1] if len(ranked) > 1 else 0

    recommendation_support = top_count / total
    minority_recommendation_support = second_count / total
    tied_at_top = sum(1 for _, count in ranked if count == top_count) > 1
    is_deadlock = recommendation_support < MAJORITY_THRESHOLD or tied_at_top

    supporting_models = [
        claim.model_name
        for claim in claims
        if (claim.primary_recommendation or claim.position_key) == top_key
    ]
    minority_models = [
        claim.model_name
        for claim in claims
        if (claim.primary_recommendation or claim.position_key) != top_key
    ]

    logger.debug(
        "consulate.recommendation_vote | recommendation_support=%.0f%% | "
        "top_recommendation=%s | deadlock=%s | distribution=%s",
        recommendation_support * 100,
        top_key,
        is_deadlock,
        ", ".join(f"{key}={count}" for key, count in ranked),
    )

    return (
        recommendation_support,
        minority_recommendation_support,
        top_key,
        supporting_models,
        minority_models,
        is_deadlock,
    )


def build_disagreement_summary(
    prompt: str,
    topic: str,
    majority: PositionCluster,
    minority: PositionCluster,
    majority_support: float,
    minority_support: float,
) -> DisagreementSummary:
    """Produce a human-readable sentence describing what the council disagrees about."""
    sentence = summarize_disagreement(prompt, topic, majority, minority)

    return DisagreementSummary(
        disputed_concept=sentence,
        majority_position=majority.position_label,
        minority_position=minority.position_label,
        majority_support=round(majority_support, 3),
        minority_support=round(minority_support, 3),
        explanation=sentence,
    )


def summarize_disagreement(
    prompt: str,
    topic: str,
    majority: PositionCluster,
    minority: PositionCluster,
) -> str:
    """
    Return a single sentence describing the substantive disagreement.

    Never returns keyword bags — always a moderator-style explanation.
    """
    maj_key = majority.position_key
    min_key = minority.position_key
    pair = frozenset({maj_key, min_key})
    prompt_lower = prompt.lower()

    # Known semantic disagreement patterns (order-independent key pairs)
    templates: dict[frozenset[str], str] = {
        frozenset({"soccer", "american_football"}): (
            'The models disagree about the meaning of the word "football" — '
            "association football (soccer) versus American football."
        ),
        frozenset({"depth_first", "context_dependent"}): (
            "Whether there is a generally optimal career progression (prioritizing depth early) "
            "versus a fully context-dependent approach where the best path varies by situation."
        ),
        frozenset({"breadth_first", "context_dependent"}): (
            "Whether breadth should be prioritized early in a career "
            "versus whether the optimal path depends entirely on individual context."
        ),
        frozenset({"depth_first", "breadth_first"}): (
            "Whether to prioritize depth (specialization) or breadth (exploration) "
            "when building a career."
        ),
        frozenset({"aggressive_investment", "conservative_investment"}): (
            "Whether to pursue aggressive growth and accept higher risk "
            "versus prioritizing capital preservation with conservative investments."
        ),
        frozenset({"pro_vc", "anti_vc"}): (
            "Whether the benefits of rapid growth from venture capital "
            "outweigh dilution and loss of control."
        ),
    }

    if pair in templates:
        return templates[pair]

    # Prompt-aware fallbacks
    if "football" in prompt_lower or topic == "football":
        return (
            'The models disagree about the meaning of the term "football" '
            "and which sport or definition applies."
        )

    if "depth" in prompt_lower and "breadth" in prompt_lower:
        return (
            "Whether there is a generally optimal balance between depth and breadth in career development "
            "versus an approach that depends entirely on individual goals and context."
        )

    if "venture" in prompt_lower or "raise" in prompt_lower and "capital" in prompt_lower:
        return (
            "Whether rapid growth from outside funding outweighs "
            "the tradeoffs of dilution and reduced founder control."
        )

    if majority.position_label and minority.position_label:
        maj = majority.position_label.rstrip(".")
        mino = minority.position_label.rstrip(".")
        if (
            maj.lower() != mino.lower()
            and _position_label_matches_topic(topic, maj)
            and _position_label_matches_topic(topic, mino)
        ):
            return (
                f"The majority favors {maj.lower()}, while the minority argues for {mino.lower()}."
            )

    return (
        "The council holds substantively different interpretations of the question "
        "that lead to different recommendations."
    )


_OFF_TOPIC_LABEL_PHRASES = (
    "pet breed",
    "pet advice",
    "apartment-friendly breed",
    "active/large breed",
)


def _position_label_matches_topic(topic: str, label: str) -> bool:
    """Reject misclassified labels (e.g. pet wording on a non-pet question)."""
    if topic == "pets":
        return True
    lowered = label.lower()
    return not any(phrase in lowered for phrase in _OFF_TOPIC_LABEL_PHRASES)
