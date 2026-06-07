"""Build synthesis prompts within ChatMessage length limits."""

from __future__ import annotations

import re

from app.orchestrator.consensus.models import ConsensusResult, ExtractedClaims
from app.schemas.chat import MAX_MESSAGE_CHARS, ChatMessage, guard_message_content
from app.schemas.provider import ModelResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Reserve space for system prompt overhead and final truncation marker.
USER_CONTENT_BUDGET = MAX_MESSAGE_CHARS - 200
COMBINED_FULL_TEXT_THRESHOLD = 6_000
MAX_CLAIM_BULLETS = 3
MIN_PER_MODEL_CHARS = 120
MAX_POSITION_CHARS = 200
MAX_CLAIM_CHARS = 160


def truncate_text(text: str, max_chars: int, *, suffix: str = "...") -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    if max_chars <= len(suffix):
        return suffix[:max_chars]
    return text[: max_chars - len(suffix)].rstrip() + suffix


def safe_chat_message(role: str, content: str) -> ChatMessage:
    """Create a ChatMessage without relying on Pydantic validation to catch overflow."""
    safe_content, truncated = guard_message_content(content)
    if truncated:
        logger.warning(
            "chat.message.truncated | role=%s | original_chars=%d | limit=%d",
            role,
            len(content),
            MAX_MESSAGE_CHARS,
        )
    return ChatMessage.create(role, safe_content)  # type: ignore[arg-type]


def _claims_by_model(consensus: ConsensusResult | None) -> dict[str, ExtractedClaims]:
    if not consensus:
        return {}
    return {claim.model_id: claim for claim in consensus.extracted_claims}


def _model_confidence(
    model_id: str,
    consensus: ConsensusResult | None,
) -> float | None:
    if not consensus:
        return None
    for cluster in consensus.clusters:
        if model_id in cluster.model_ids:
            return cluster.support
    return None


def _format_claim_bullets(claims: list[str], max_bullets: int = MAX_CLAIM_BULLETS) -> str:
    bullets: list[str] = []
    for claim in claims:
        cleaned = re.sub(r"\s+", " ", claim).strip()
        if cleaned:
            bullets.append(f"- {truncate_text(cleaned, MAX_CLAIM_CHARS)}")
        if len(bullets) >= max_bullets:
            break
    if not bullets:
        return "- (none extracted)"
    return "\n".join(bullets)


def compress_model_entry(
    resp: ModelResponse,
    claim: ExtractedClaims | None,
    *,
    per_model_budget: int,
    confidence: float | None = None,
) -> str:
    """Compact council entry: model, position, key reasoning, confidence."""
    position = ""
    reasoning = ""

    if claim:
        position = truncate_text(
            claim.position_summary or claim.interpretation or claim.topic,
            MAX_POSITION_CHARS,
        )
        reasoning = _format_claim_bullets(claim.claims)
    else:
        text = resp.effective_content
        position = truncate_text(text, MAX_POSITION_CHARS)
        reasoning = truncate_text(text, max(120, per_model_budget // 2))

    confidence_line = (
        f"Confidence: {confidence * 100:.0f}%"
        if confidence is not None
        else "Confidence: n/a"
    )

    entry = (
        f"Model: {resp.model_name}\n"
        f"Position: {position}\n"
        f"Key reasoning:\n{reasoning}\n"
        f"{confidence_line}"
    )
    return truncate_text(entry, per_model_budget)


def build_council_response_block(
    responses: list[ModelResponse],
    consensus: ConsensusResult | None = None,
    *,
    force_compress: bool = False,
) -> tuple[str, int, int, bool]:
    """Return council text, raw char count, final char count, and whether compressed."""
    claims_map = _claims_by_model(consensus)
    raw_parts: list[str] = []
    for resp in responses:
        if not (resp.success and resp.effective_content):
            continue
        raw_parts.append(
            f"--- {resp.model_name} ({resp.role}) ---\n{resp.effective_content}"
        )

    raw_text = "\n\n".join(raw_parts)
    raw_chars = len(raw_text)

    if not force_compress and raw_chars <= COMBINED_FULL_TEXT_THRESHOLD:
        return raw_text, raw_chars, raw_chars, False

    count = max(len(raw_parts), 1)
    per_model_budget = max(MIN_PER_MODEL_CHARS, USER_CONTENT_BUDGET // count)
    compressed_parts: list[str] = []
    for resp in responses:
        if not (resp.success and resp.effective_content):
            continue
        claim = claims_map.get(resp.model_id)
        confidence = _model_confidence(resp.model_id, consensus)
        compressed_parts.append(
            compress_model_entry(
                resp,
                claim,
                per_model_budget=per_model_budget,
                confidence=confidence,
            )
        )

    compressed_text = "\n\n".join(compressed_parts)
    compressed_chars = len(compressed_text)

    if compressed_chars > USER_CONTENT_BUDGET:
        reduced_budget = max(MIN_PER_MODEL_CHARS, USER_CONTENT_BUDGET // count - 20)
        compressed_parts = [
            compress_model_entry(
                resp,
                claims_map.get(resp.model_id),
                per_model_budget=reduced_budget,
                confidence=_model_confidence(resp.model_id, consensus),
            )
            for resp in responses
            if resp.success and resp.effective_content
        ]
        compressed_text = truncate_text("\n\n".join(compressed_parts), USER_CONTENT_BUDGET)

    return compressed_text, raw_chars, len(compressed_text), True


def build_consensus_user_content(
    prompt: str,
    responses: list[ModelResponse],
    consensus: ConsensusResult | None = None,
) -> tuple[str, dict[str, int | bool]]:
    council_block, raw_chars, compressed_chars, compressed = build_council_response_block(
        responses,
        consensus,
    )

    consensus_context = ""
    if consensus and not consensus.is_deadlock:
        minority_note = ""
        if consensus.minority_support > 0 and consensus.disagreement:
            d = consensus.disagreement
            minority_note = (
                f"\nMinority position ({consensus.minority_support * 100:.0f}% support): "
                f"{truncate_text(d.minority_position, 400)}\n"
                f"Disputed concept: {truncate_text(d.disputed_concept, 200)}\n"
                f"Why: {truncate_text(d.explanation, 300)}\n"
            )
        majority_label = (
            consensus.clusters[0].position_label if consensus.clusters else "consensus"
        )
        consensus_context = (
            f"\nConsensus Analysis:\n"
            f"- Agreement: {consensus.agreement_score * 100:.0f}%\n"
            f"- Majority ({consensus.majority_support * 100:.0f}%): "
            f"{truncate_text(majority_label, 200)}\n"
            f"- Supporting models: {', '.join(consensus.supporting_models)}\n"
            f"{minority_note}"
        )

    user_content = (
        f"User Question:\n{truncate_text(prompt, 1500)}\n\n"
        f"Council Responses:\n\n{council_block}"
        f"{consensus_context}\n\n"
        "Synthesize these responses into a single consensus answer."
    )

    truncated = False
    if len(user_content) > USER_CONTENT_BUDGET:
        user_content = truncate_text(user_content, USER_CONTENT_BUDGET)
        truncated = True

    meta = {
        "prompt_chars": len(user_content),
        "compressed_chars": compressed_chars,
        "raw_chars": raw_chars,
        "compressed": compressed,
        "truncated": truncated,
    }
    return user_content, meta


def build_deadlock_user_content(
    prompt: str,
    consensus: ConsensusResult,
    responses: list[ModelResponse] | None = None,
) -> tuple[str, dict[str, int | bool]]:
    """Deadlock payload: model, position, key reasoning, confidence only."""
    entries: list[str] = []
    claims_map = _claims_by_model(consensus)

    source_items: list[tuple[str, str, ExtractedClaims | None, ModelResponse | None]] = []
    if consensus.extracted_claims:
        for claim in consensus.extracted_claims:
            source_items.append((claim.model_id, claim.model_name or claim.model_id, claim, None))
    elif responses:
        for resp in responses:
            if resp.success and resp.effective_content:
                source_items.append(
                    (
                        resp.model_id,
                        resp.model_name or resp.model_id,
                        claims_map.get(resp.model_id),
                        resp,
                    )
                )

    count = max(len(source_items), 1)
    per_model_budget = max(MIN_PER_MODEL_CHARS, USER_CONTENT_BUDGET // count)

    for model_id, model_name, claim, resp in source_items:
        confidence = _model_confidence(model_id, consensus)
        model_resp = resp or ModelResponse(
            modelId=model_id,
            modelName=model_name,
            content="",
            success=True,
        )
        entries.append(
            compress_model_entry(
                model_resp,
                claim,
                per_model_budget=per_model_budget,
                confidence=confidence,
            )
        )

    council_block = "\n\n".join(entries)
    raw_chars = sum(len(r.effective_content) for r in (responses or []) if r.success)

    disagreement_note = ""
    if consensus.disagreement:
        d = consensus.disagreement
        disagreement_note = (
            f"\nPrimary disagreement: {truncate_text(d.disputed_concept, 200)}\n"
            f"Majority cluster ({consensus.majority_support * 100:.0f}%): "
            f"{truncate_text(d.majority_position, MAX_POSITION_CHARS)}\n"
            f"Minority cluster ({consensus.minority_support * 100:.0f}%): "
            f"{truncate_text(d.minority_position, MAX_POSITION_CHARS)}\n"
        )
    elif consensus.primary_disagreement:
        disagreement_note = (
            f"\nPrimary disagreement: {truncate_text(consensus.primary_disagreement, 400)}\n"
        )

    user_content = (
        f"User Question:\n{truncate_text(prompt, 1500)}\n\n"
        f"Agreement Score: {consensus.agreement_score:.2f} (DEADLOCK — no majority position)\n\n"
        f"Council Positions:\n\n{council_block}"
        f"{disagreement_note}\n"
        "Present the deadlock transparently to the user."
    )

    truncated = False
    if len(user_content) > USER_CONTENT_BUDGET:
        user_content = truncate_text(user_content, USER_CONTENT_BUDGET)
        truncated = True

    meta = {
        "prompt_chars": len(user_content),
        "compressed_chars": len(council_block),
        "raw_chars": raw_chars,
        "compressed": True,
        "truncated": truncated,
    }
    return user_content, meta


def build_structured_deadlock_fallback(consensus: ConsensusResult) -> str:
    """Deterministic deadlock summary when LLM synthesis fails."""
    lines = [
        "## Council Deadlocked",
        "",
        "The council could not reach a majority position on this question.",
        "",
        f"- **Agreement score:** {consensus.agreement_score * 100:.0f}%",
        f"- **Majority vote support:** {consensus.majority_support * 100:.0f}%",
    ]

    if consensus.primary_disagreement:
        lines.extend(["", f"**Primary disagreement:** {consensus.primary_disagreement}"])

    if consensus.clusters:
        lines.extend(["", "### Positions"])
        for cluster in consensus.clusters:
            lines.append(
                f"- **{cluster.position_label}** ({cluster.support * 100:.0f}% — "
                f"{', '.join(cluster.model_names)}): "
                f"{truncate_text(cluster.position_summary, 400)}"
            )
    elif consensus.extracted_claims:
        lines.extend(["", "### Positions"])
        for claim in consensus.extracted_claims:
            bullets = _format_claim_bullets(claim.claims, max_bullets=2)
            lines.append(
                f"- **{claim.model_name}:** {claim.position_summary}\n  {bullets}"
            )

    if consensus.disagreement:
        d = consensus.disagreement
        lines.extend(
            [
                "",
                "### Why they disagree",
                truncate_text(d.explanation or d.disputed_concept, 600),
            ]
        )

    return "\n".join(lines)


def build_consensus_fallback(
    consensus: ConsensusResult,
    responses: list[ModelResponse],
) -> str:
    """Fallback answer for failed consensus synthesis."""
    if consensus.majority_position:
        header = f"## {consensus.outcome_label}\n\n"
        body = truncate_text(consensus.majority_position, MAX_MESSAGE_CHARS - len(header) - 100)
        if consensus.minority_support > 0 and consensus.disagreement:
            minority = truncate_text(consensus.disagreement.minority_position, 400)
            body += f"\n\n*Note: A minority view ({consensus.minority_support * 100:.0f}% support) differed: {minority}*"
        return header + body

    best = max(
        (r for r in responses if r.success and r.effective_content),
        key=lambda r: len(r.effective_content),
        default=None,
    )
    if best:
        return truncate_text(best.effective_content, MAX_MESSAGE_CHARS)

    return "The council responded but synthesis could not be completed. Please review individual responses below."
